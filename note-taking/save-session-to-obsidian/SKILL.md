---
name: save-session-to-obsidian
description: Save Hermes session transcripts to Obsidian as daily conversation summaries with auto-detected "Decisions today" section. Session files are detected automatically by a watchdog cron job and written to $OBSIDIAN_VAULT_PATH/Conversations/YYYY/YYYY-MM/YYYY-MM-DD.md. Multiple sessions on the same day are appended to the same file (not overwritten) with time-stamped session markers. Designed to be fully automatic — no manual steps required.
version: 1.6.0
---

# Save Session to Obsidian

Session transcripts are detected and written automatically. Manual steps are only needed if the watchdog is not running.

## Architecture

```
Hermes session ends (any way: /quit, Ctrl+C, exit)
  → ~/.hermes/sessions/
       ├── saved/hermes_conversation_YYYYMMDD_HHMMSS.json  (Telegram, JSON array)
       ├── session_YYYYMMDD_HHMMSS_id.json                  (CLI interactive, JSON array)
       ├── session_bg_HHMMSS_id.json                         (CLI background, JSON array)
       ├── session_cron_JOBID_YYYYMMDD_HHMMSS.json           (cron subagent, JSON array)
       └── YYYYMMDD_HHMMSS_<hex>.jsonl                      (CLI default writer, JSONL)
  → watch_sessions.py (cron, every 15 min)  — handles BOTH container formats
  → $OBSIDIAN_VAULT_PATH/Conversations/YYYY/YYYY-MM/YYYY-MM-DD.md
  → Conversations/README.md index updated

# Gap: live, unclosed sessions OR sessions whose file write was suppressed
# (gateway crash, short TTL) never produce a file. The file watcher is
# structurally blind to these. The DB-poll companion catches them:
  → watch_sessions_db.py (cron, every 30 min)
       queries state.db for ended sessions with message_count > 0
       that have no file on disk and aren't already in state.db marker
       → backfills from state.db directly → Obsidian
```

**5 source patterns across 2 container formats** (`.json` array and `.jsonl` lines). The watchdog dispatches on extension: `.json` → `json.load()` of the whole file, `.jsonl` → line-by-line `json.loads()`. Source label in output is `📱 TELEGRAM` for `hermes_conversation_*`, `💻 CLI` for everything else (including `.jsonl`).

## Key design decisions

**`/save` does NOT write to Obsidian.** It saves a local JSON transcript to `~/.hermes/sessions/saved/`. The watchdog then picks it up within 15 min and writes to Obsidian. Do not rely on `/save` as a manual Obsidian save — it's a local transcript only.

**Cron watchdog, NOT manual invocation.** First version required `/skill save-session-to-obsidian` then `/quit`. User rejected this — "I'm not going to call manually the skill then exit." Automation via `watch_sessions.py` running as a no_agent cron job is the correct pattern.

**Append, don't overwrite.** Multiple sessions per day accumulate in the same file, each with a `### Session HH:MM [source]` marker. Overwriting (old → new) loses data.

**Decisions today — the only section that must not be empty.** Per the vault's empty-container finding (theme 07), the previous version captured timestamps and topics but never captured decisions. v1.4 adds heuristic decision detection from each user message (first-person commitments, switch/decide verbs, imperative bullets) and seeds a `## Decisions today` section on first file creation. Auto-detected items are advisory — the writer edits to keep only what was actually decided. A day with zero detected decisions is still signal (no real decisions made that day), and the section placeholder persists at the bottom of every daily file.

**State tracking.** `~/.hermes/sessions/.session_watchdog_state` tracks processed files — prevents re-processing on re-runs. Uses `fcntl.flock` for concurrency safety.

**Watchdog frequency:** Every 15 minutes. Sufficient — sessions appear in the filesystem within seconds of ending, 15 min is an acceptable lag.

## Defensive warnings (added 2026-06-07)

The watchdog emits two stderr warnings designed to make the next silent
break loud instead of silent:

- `UNMATCHED_SESSION_FORMAT: <filename>` — fires when a file in
  `~/.hermes/sessions/` ends in `.json` but doesn't match any known
  prefix. Catches the moment a new file format is introduced.
- `STALE_STATE_WARNING: newest session is Nh newer than newest
  processed state entry` — fires when the on-disk newest session file
  is >24h newer than the newest state-tracked file. Catches the
  pipeline-silently-broke-because-glob-doesn't-match failure mode that
  state-based dedup is structurally blind to.

Both surface via Sandy's stderr pass-through. If you change the cron
delivery mode, make sure stderr still reaches you. If you ever see
either warning, the pipeline has been broken — the next cron tick
hasn't silently recovered, the user has lost data.

**These warnings would have caught the 33-day silent break in
May–June 2026 within 24 hours instead.** The original SKILL.md (v1.4)
claimed "all 4 formats are monitored" but the actual glob patterns
only matched `.json` files with known prefixes — `.jsonl` was missing.
The doc and the code were wrong in the same direction. Don't repeat
this: every patch that touches the format table or the glob list
should update the other in the same change.

## Session file formats

**Hermes writes sessions in two distinct container formats:**

1. **JSON array** (`.json`) — one full session object per file. Used by Telegram (`hermes_conversation_*`) and CLI (`session_*`, `session_bg_*`, `session_cron_*`).
2. **JSON Lines** (`.jsonl`) — one JSON object per line. Used by older CLI sessions and the current default CLI writer. Pattern: `YYYYMMDD_HHMMSS_<hex>.jsonl` (date_stamp_hash, no `session_` prefix).

| Pattern | Source | Format | Date extraction | Time extraction |
|---------|--------|--------|-----------------|-----------------|
| `hermes_conversation_YYYYMMDD_HHMMSS.json` | Telegram | JSON array | `re.search(r'(\d{8})')` | `re.search(r'_(\d{2})(\d{2})(\d{2})(?:_\w+)?$')` |
| `session_YYYYMMDD_HHMMSS_id.json` | CLI | JSON array | same | same |
| `session_bg_HHMMSS_id.json` | background | JSON array | fallback → mtime | same |
| `session_cron_JOBID_YYYYMMDD_HHMMSS.json` | cron subagent | JSON array | `re.search(r'(\d{8})')` | same |
| `YYYYMMDD_HHMMSS_<hex>.jsonl` | CLI (default) | JSONL | `re.search(r'^(\d{8})')` | `re.search(r'^\d{8}_(\d{2})(\d{2})(\d{2})')` |

**Both formats are monitored.** The script's `find_new_sessions()` globs all five patterns; `parse_session()` dispatches to `json.load` for arrays and a line-by-line read for JSONL. **Pitfall:** the SKILL.md v1.4.0 doc said "all 4 formats" and only listed JSON-array patterns — the JSONL container was missing entirely, and sessions written as `.jsonl` (the majority of recent ones) silently fell through. Discovered 2026-06-07 when the user noticed "I don't see this stored into the conversations in obsidian, only 2 entries in june." Always check the actual on-disk file extension before trusting the format table — the Hermes writer changed containers mid-stream (`.jsonl` → `.json` → back to `.jsonl`) and the skill doc lagged.

**Date:** Parsed from `YYYYMMDD` anywhere in filename — do not assume fixed position. Falls back to file `mtime` if no date found.

**Time:** HHMMSS extracted from the end of the stem using `re.search(r'_(\d{2})(\d{2})(\d{2})(?:_\w+)?$')` which handles all four formats. The session marker format is `### Session HH:MM`.

## Ctrl+C / incomplete file handling

When a session ends abruptly (Ctrl+C, signal kill), the JSON file may be half-written or truncated. `watch_sessions.py` guards against this with `is_json_valid(filepath)` — a full `json.load()` parse test. Files that fail are:
- Skipped silently
- Recorded in the state file so they are not re-checked every tick

The watchdog will not re-process corrupt/incomplete files on subsequent runs.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/watch_sessions.py` | File-based watchdog — run via cron, detects new session JSON/JSONL dumps, writes to Obsidian. Emits the two defensive warnings (UNMATCHED_SESSION_FORMAT, STALE_STATE_WARNING) to stderr on each tick. |
| `scripts/watch_sessions_db.py` | **DB-poll companion** to the file watcher. Catches the "ended session with no file dump" gap that the file watcher is structurally blind to. Runs as a second no_agent cron job, every 30 min, silent on no-op. |
| `scripts/save_session.py` | Manual one-shot — parses a session file and writes summary (no state tracking) |
| `scripts/backfill_from_db.py` | Recover lost sessions from `~/.hermes/state.db` (SQLite). Use when session files are missing or the pipeline was broken for days. Accepts a session_id or `--since YYYY-MM-DD`. **Skips sessions already marked `db:<id>` in state** (idempotent — safe to re-run). |
| `scripts/backfill_request_dump.py` | Recover a session from a `request_dump_*.json` (gateway-crash artifact). Trusts the `session_id` date over the dump's own timestamp. |

**Reference for the "ended but no file" gap** — when the file watcher is structurally blind to a session (live/unclosed sessions, gateway crash, suppressed file write). Full diagnosis recipe, recovery procedure, and what to verify going forward: `references/live-session-blind-spot.md`.

## Cron job setup

**⚠️ The scheduler prepends `~/.hermes/scripts/` to the script path** and splits on spaces. You CANNOT pass `python3 /full/path` — it becomes `/home/user/.hermes/scripts/python3 /full/path`. Instead, create a wrapper shell script in `~/.hermes/scripts/` and pass its name only:

```bash
# Create wrapper (one-time)
cat > ~/.hermes/scripts/watch_sessions.sh << 'EOF'
#!/bin/bash
exec python3 /home/thomas/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions.py
EOF
chmod +x ~/.hermes/scripts/watch_sessions.sh

# Create cron job — use WRAPPER NAME only, no spaces
hermes cron create "*/15 * * * *" \
  --script "watch_sessions.sh" \
  --name "session-to-obsidian watchdog" \
  --no-agent
```

The DB-poll companion has its own cron job (created 2026-06-08):

```bash
cat > ~/.hermes/scripts/watch_sessions_db.sh << 'EOF'
#!/bin/bash
exec python3 /home/thomas/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions_db.py
EOF
chmod +x ~/.hermes/scripts/watch_sessions_db.sh

hermes cron create "*/30 * * * *" \
  --script "watch_sessions_db.sh" \
  --name "session-to-obsidian db-poll" \
  --no-agent
```

## Troubleshooting

**Sessions not appearing in Obsidian:**
1. **Identify what Hermes is actually writing.** `ls -lt ~/.hermes/sessions/ | head -20` — note the extensions (`.json` vs `.jsonl`) and patterns. The skill's documented "all 4 formats" can lag behind reality; the writer has switched containers at least twice (June 2026: `.jsonl` → `.json` → `.jsonl`).
2. Check cron is running: `hermes cron list` — confirm `session-to-obsidian watchdog` exists, is `[active]`, and `Last run: ok`.
3. **Check the wrapper script actually invokes the watchdog.** The cron field `Script:` should point to a wrapper like `watch_sessions_sandy.sh` or `watch_sessions.sh`. If it points to a Sandy scenario JSON, open that scenario and confirm its `params.command` calls `python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions.py` — Sandy scenarios silently no-op when the inner command fails or is wrong.
4. Check state file exists and inspect its newest entries: `head -c 500 ~/.hermes/sessions/.session_watchdog_state | python3 -c "import json,sys; print(json.load(sys.stdin)[-5:])"`. The newest filenames in the state tell you the last time the watchdog successfully processed anything. **If the newest state entry is older than the newest session file, the watchdog has stopped processing.**
5. Run watchdog manually: `python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions.py`. Output is `NO_NEW_SESSIONS` (good — nothing to do), `PROCESSED:N` followed by paths (good — fixed it), or a Python traceback (bad — paste the error and fix).
6. **Cross-check:** `ls ~/Desktop/Memory/Conversations/2026/2026-MM/` and compare to the dates of the session files on disk. The set of vault dates must be a subset of session-file dates. If vault is missing recent dates, the pipeline is broken; if it has dates with no matching session files, the pipeline was overwriting or duplicating.
7. Check cron output for `Script not found` — if seen, the wrapper script is missing or the job uses a spaced command instead of the wrapper name.

8. **User reports MISSING RECENT conversations but steps 1–7 look healthy.** The pipeline is fine — the issue is **upstream**, not the watcher. Verify session files exist on disk for the expected time range: `ls -lt ~/.hermes/sessions/ | head -5` and check the newest file's mtime against the user's complaint. If the newest file is days older than expected, sessions are not being written. Two likely causes:
   - **Sessions never ended cleanly.** The file only appears on `/quit`, session boundary, or graceful shutdown. Active / background / killed sessions leave no file.
   - **Cleanup cron ran.** `session-cleanup` (`0 */6 * * *`, job `d7819f39a526`) deletes `request_dump_*` and old sessions. Check `~/.hermes/scripts/cleanup-sessions.py` for its retention window before concluding the pipeline lost data.

   **Recovery path: bypass the filesystem.** `state.db` (SQLite) is the source of truth — every message Hermes ever processed, regardless of whether the JSON file writer succeeded. Use `backfill_from_db.py --since YYYY-MM-DD` to recover days of conversation even when the session files are gone. This is why the live DB backfill exists, and it is the correct tool when "recent conversations missing" turns into "the user is right and the filesystem is empty."

**Duplicate entries in README:** Safe to re-run — README update is idempotent (checks if date already linked before adding).

**Full diagnostic recipe** (5 steps, root-cause table, backfill procedure, verification): see `references/watchdog-debug-recipe.md`.

## Manual override

If the cron fails or you want to save immediately without waiting 15 min:

```bash
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/save_session.py
```

Does NOT use state tracking — always writes/overwrites a single session to Obsidian.

## Backfill from state.db (recovery path)

When the pipeline has been broken for days and session files are missing
or corrupted, recover from the live SQLite session DB. The `state.db` is
the source of truth — it has every message Hermes ever processed,
regardless of whether the JSON file writer succeeded.

```bash
# Backfill a specific session_id
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/backfill_from_db.py <session_id>

# Backfill a date window (sessions with >0 messages in that range)
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/backfill_from_db.py --since 2026-06-05
```

Writes to the same Obsidian Conversation file structure as the watchdog,
appending to existing daily files. State is updated with `db:<session_id>`
markers so the watchdog won't reprocess. Tool calls are shown as
`[tc:tool_name]` to keep the digest scannable.

## Backfill from request_dump (gateway-crash recovery)

When the API call exhausts retries mid-session, Hermes writes a
`request_dump_*.json` containing the full request body that was about
to be sent. The session is recoverable from there:

```bash
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/backfill_request_dump.py ~/.hermes/sessions/request_dump_*.json
```

**Always trust the `session_id` date** (`YYYYMMDD_HHMMSS_*`) over the
dump's own `timestamp` — the latter is when the failure happened and
may be on a different day if the crash spanned midnight.