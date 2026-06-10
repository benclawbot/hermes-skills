#!/usr/bin/env python3
"""
Backfill from Hermes state.db (SQLite) — the live session DB that
session_search queries.

The watchdog normally watches the JSON file dumps in ~/.hermes/sessions/,
but those are a snapshot. The state.db is the source of truth: every
session that Hermes actually ran, with all messages and tool calls.

Use this to recover sessions that exist in the DB but never produced
a JSON file (gateway crashes, mid-session kills, request_dump incidents).

Usage:
    python3 backfill_from_db.py <session_id> [<session_id> ...]
    python3 backfill_from_db.py --since YYYY-MM-DD [--until YYYY-MM-DD]

Writes one Obsidian Conversation file per day, appending multiple
sessions to the same file.
"""
import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".hermes/state.db"
VAULT = Path("/home/thomas/Desktop/Memory")
CONV = VAULT / "Conversations"
STATE_FILE = Path.home() / ".hermes/sessions/.session_watchdog_state"


def truncate(s, n=700):
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0] + "…"


def extract_tool_calls(row):
    """Decode tool_calls JSON column into a short displayable summary.

    The full arguments are usually too noisy for a conversation digest —
    we just want the tool name and the first ~50 chars of the most
    distinctive argument. Tool names alone are usually enough signal.
    """
    tc_json = row["tool_calls"]
    if not tc_json:
        return ""
    try:
        calls = json.loads(tc_json)
    except (json.JSONDecodeError, TypeError):
        return ""
    parts = []
    for c in calls:
        if not isinstance(c, dict):
            continue
        name = c.get("function", {}).get("name") or c.get("name", "")
        if name:
            parts.append(f"[tc:{name}]")
    return " ".join(parts)


DECISION_PATTERNS = [
    r"\b(i'?ll|let'?s|going to|will|gonna)\b.{0,80}\b(use|switch|adopt|change|fix|build|start|stop|focus|try|move to|drop|enable|disable|set to|set the|make it)\b",
    r"\b(decided|decision|choosing|chose|switched to|moved to|adopted|killed|deprecated|pinned|archived|removed|deleted)\b.{0,80}\b(hermes|skill|repo|project|tool|file|note|tag|path|script|version|format|approach|strategy)\b",
    r"\b(from now on|going forward|new plan|new rule|new approach)\b",
    r"^(?:use|switch to|move to|adopt|enable|disable|delete|remove|archive|fix|build|create|start|stop|set)\b",
]


def detect_decisions(messages):
    found, seen = [], set()
    compiled = [re.compile(p, re.IGNORECASE) for p in DECISION_PATTERNS]
    for role, content in messages:
        if role != "user":
            continue
        for line in content.splitlines():
            cleaned = re.sub(r"^[\s>*\-•·]+", "", line).strip()
            if len(cleaned) < 10 or len(cleaned) > 240:
                continue
            for pat in compiled:
                if pat.search(cleaned):
                    if cleaned.lower() in seen:
                        break
                    seen.add(cleaned.lower())
                    found.append(truncate(cleaned, 180))
                    break
    return found


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f)


def write_obsidian(date, summary, session_label, source, session_time):
    year, month, day = date.strftime("%Y"), date.strftime("%Y-%m"), date.strftime("%Y-%m-%d")
    target = CONV / year / month / f"{day}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    hh, mm = session_time.split(":")[:2]
    icon = "📱" if source == "telegram" else ("⏰" if source == "cron" else "💻")
    marker = f"\n\n---\n### Session {hh}:{mm} [{icon} {source.upper()}] (recovered from state.db {session_label})\n"
    body = f"{marker}{summary}\n"
    if target.exists():
        with open(target, "a") as f:
            f.write(body)
    else:
        with open(target, "w") as f:
            f.write(f"# Conversation — {day}\n{body}\n\n---\n## Decisions today\n_(Auto-detected from this day's sessions. Edit to keep only what was actually decided.)_\n")
    return target


def fetch_messages(cur, session_id):
    cur.execute(
        "SELECT role, content, tool_calls, timestamp FROM messages WHERE session_id = ? AND role IN ('user', 'assistant') ORDER BY timestamp",
        (session_id,),
    )
    out = []
    for role, content, tool_calls_json, ts in cur.fetchall():
        if not content and not tool_calls_json:
            continue
        if tool_calls_json:
            tc_display = extract_tool_calls({"tool_calls": tool_calls_json})
            if tc_display:
                content = (content or "") + f"\n[tc]\n{tc_display}"
        if content:
            out.append((role, content, ts))
    return out


def summarize(messages, source):
    if not messages:
        return None
    topic = truncate(messages[0][1], 100)
    lines = [f"## Topic [{source.upper()}]\n{topic}"]
    lines.append("\n## Key exchanges")
    if len(messages) >= 2:
        lines.append(f"- You: {truncate(messages[0][1], 200)}")
        lines.append(f"- Assistant: {truncate(messages[1][1], 200)}")
    if len(messages) > 4:
        mid = messages[len(messages) // 2]
        lines.append(f"- … {mid[0].title()}: {truncate(mid[1], 200)}")
    for role, content, _ in reversed(messages):
        if role == "user":
            lines.append(f"- You (end): {truncate(content, 200)}")
            break
    decisions = detect_decisions([(r, c) for r, c, _ in messages])
    if decisions:
        lines.append("\n## Decisions today")
        for d in decisions[:5]:
            lines.append(f"- {d}")
    return "\n".join(lines)


def get_session_meta(cur, session_id):
    cur.execute(
        "SELECT id, source, started_at, ended_at, message_count, end_reason FROM sessions WHERE id = ?",
        (session_id,),
    )
    return cur.fetchone()


def backfill_sessions(session_ids):
    con = sqlite3.connect(f"file://{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    written = []
    state = load_state()
    skipped = 0
    for sid in session_ids:
        if f"db:{sid}" in state:
            skipped += 1
            continue
        meta = get_session_meta(cur, sid)
        if not meta:
            print(f"NOT FOUND in DB: {sid}")
            continue
        messages = fetch_messages(cur, sid)
        if not messages:
            print(f"NO MESSAGES: {sid}")
            continue
        date = datetime.fromtimestamp(meta["started_at"])
        session_time = date.strftime("%H:%M:%S")
        source = meta["source"] or "unknown"
        summary = summarize(messages, source)
        target = write_obsidian(date, summary, sid, source, session_time)
        state.add(f"db:{sid}")
        written.append((sid, len(messages), target))
        print(f"WROTE: {target}  ({len(messages)} msgs, source={source})")
    if written:
        save_state(state)
    if skipped:
        print(f"SKIPPED: {skipped} session(s) already in state (db:<sid> marker)")
    con.close()
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session_ids", nargs="*", help="session_id values to backfill")
    ap.add_argument("--since", help="YYYY-MM-DD lower bound on started_at")
    ap.add_argument("--until", help="YYYY-MM-DD upper bound on started_at (exclusive)")
    args = ap.parse_args()

    if args.session_ids:
        backfill_sessions(args.session_ids)
        return

    if not args.since:
        print("Provide session_ids or --since", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(f"file://{DB_PATH}?mode=ro", uri=True)
    cur = con.cursor()
    since_ts = datetime.strptime(args.since, "%Y-%m-%d").timestamp()
    until_ts = datetime.strptime(args.until, "%Y-%m-%d").timestamp() if args.until else datetime.now().timestamp() + 86400
    cur.execute(
        "SELECT id FROM sessions WHERE started_at >= ? AND started_at < ? AND message_count > 0 ORDER BY started_at",
        (since_ts, until_ts),
    )
    sids = [r[0] for r in cur.fetchall()]
    con.close()
    if not sids:
        print(f"No sessions with messages in {args.since}..{args.until or 'now'}")
        return
    print(f"Found {len(sids)} session(s) with messages in window")
    backfill_sessions(sids)


if __name__ == "__main__":
    main()
