#!/usr/bin/env python3
"""
DB-poll watchdog for Hermes sessions → Obsidian.

Complements the file-based watchdog (watch_sessions.py). The file watcher
only sees sessions that produced a JSON/JSONL dump on disk. Live, unclosed
sessions and any session whose file write was suppressed (gateway crash,
short TTL, etc.) are invisible to it. This script queries state.db — the
source of truth — and backfills any session that has ended but hasn't been
written to Obsidian yet.

Runs as a no_agent cron job. Stdout is delivered only when sessions are
written (silent on no-op ticks, watchdog pattern).

Design notes
------------
- Backs the existing watch_sessions.py. Same Obsidian format, same state
  file (so the two can't double-process). Markers use the `db:<sid>` prefix
  the file watcher already understands.
- Skips sessions that are still open (ended_at IS NULL). The file watcher
  will pick those up on session end; this script only rescues the
  "ended but never produced a file" gap.
- Skips sessions with 0 messages — these are typically the gateway's
  0-message startup pings and would just clutter the vault.
- Idempotent: re-running on an already-written session is a no-op because
  the `db:<sid>` marker in .session_watchdog_state gates the write.
"""
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Reuse the backfill script's write logic so format stays consistent.
sys.path.insert(
    0,
    str(Path.home() / ".hermes/skills/note-taking/save-session-to-obsidian/scripts"),
)
from backfill_from_db import backfill_sessions  # noqa: E402

DB_PATH = Path.home() / ".hermes/state.db"


def find_ended_unprocessed():
    """Return session_ids in state.db that have ended but weren't backfilled yet.

    "Ended" = ended_at is not null. The file watcher handles open sessions
    when they close.

    "Unprocessed" = not present in the watchdog state file as `db:<sid>`.
    The file watcher only writes JSON filenames; we ignore those here and
    let the file watcher own them. We only rescue sessions the file
    watcher will never see (i.e. those that have no corresponding file on
    disk — checked by glob below).
    """
    con = sqlite3.connect(f"file://{DB_PATH}?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute(
        """
        SELECT s.id
        FROM sessions s
        WHERE s.ended_at IS NOT NULL
          AND s.message_count > 0
          AND s.archived = 0
        ORDER BY s.ended_at DESC
        LIMIT 50
        """
    )
    candidate_ids = [r[0] for r in cur.fetchall()]
    con.close()

    if not candidate_ids:
        return []

    # State check
    state_file = Path.home() / ".hermes/sessions/.session_watchdog_state"
    import json
    if state_file.exists():
        state = set(json.loads(state_file.read_text()))
    else:
        state = set()

    # Glob for files corresponding to each session id. We only backfill
    # sessions that DON'T have a file — if a file exists, the file watcher
    # owns it. A session_id is a 13-char stem like `20260607_124414_c38e6c`.
    sessions_dir = Path.home() / ".hermes/sessions"
    files = list(sessions_dir.glob("*.json")) + list(sessions_dir.glob("*.jsonl"))
    file_stems = {f.stem for f in files}
    saved_dir = sessions_dir / "saved"
    if saved_dir.exists():
        file_stems |= {f.stem for f in saved_dir.glob("*.json")}

    missing = []
    for sid in candidate_ids:
        if f"db:{sid}" in state:
            continue
        # session ids look like YYYYMMDD_HHMMSS_<hex>
        # Match against file stems directly (most files start with the sid)
        # plus a Telegram-style prefix match.
        sid_stem = sid
        # Extract the YYYYMMDD_HHMMSS prefix for a broader match
        prefix = "_".join(sid.split("_")[:2])
        has_file = (
            sid_stem in file_stems
            or any(f.startswith(sid_stem) for f in file_stems)
            or any(f.startswith(prefix) for f in file_stems)
        )
        if not has_file:
            missing.append(sid)

    return missing


def main():
    sids = find_ended_unprocessed()
    if not sids:
        # Watchdog pattern: silent when nothing to report.
        return
    print(f"DB-POLL: found {len(sids)} ended session(s) without a file dump")
    written = backfill_sessions(sids)
    if written:
        for sid, n, target in written:
            print(f"WROTE: {target}  ({n} msgs, sid={sid})")


if __name__ == "__main__":
    main()
