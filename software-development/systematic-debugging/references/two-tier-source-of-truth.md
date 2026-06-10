# Two-Tier Source of Truth — Recovery Patterns

When a file-based pipeline is missing data, the most common instinct is to assume the files are incomplete. Often they're not — the application has a *live* store that's the actual source of truth, and the files are just snapshots. Knowing where to look turns "lost data" into "easily recoverable."

## The pattern

Most file-based pipelines work like this:
```
Application → writes snapshot files → watcher/process → output
```

When the output is wrong/missing, the instinct is to debug the watcher. But the actual source of truth is one layer up — the application's live in-memory or DB-backed store. The files are a *projection*, not the truth.

## Where to look, by application

| Application | Snapshot files (what watcher reads) | Live store (the actual truth) | Recovery |
|-------------|-------------------------------------|-------------------------------|----------|
| **Hermes** | `~/.hermes/sessions/*.json*` | `~/.hermes/state.db` (SQLite) — `messages` table has every message ever processed | Query SQLite directly: `SELECT * FROM messages WHERE session_id = ?` |
| **Hermes** | (no snapshot for crashed sessions) | `request_dump_*.json` files in `~/.hermes/sessions/` — written when API call exhausts retries, contains the full request body | Parse the `request.body.messages` array |
| **Any agent framework** | conversation log files | agent's own session/memory DB | Look for `.db`, `.sqlite`, `.sqlite3`, leveldb/rocksdb dirs |
| **Any web app** | localStorage dumps, JSON exports | server-side DB the user can query directly | Ask for API access or DB credentials |
| **Any log pipeline** | rotated log files | the application's primary log buffer (often in-memory) | Check journald, k8s logs, primary DB |

## Diagnostic sequence (3 steps)

1. **Confirm the file layer is broken.** Don't assume — verify the file mtime is older than the last known event, OR the file doesn't exist when it should, OR the file is empty/truncated.

2. **Find the live store.** Three ways:
   - **Configuration:** most apps have a config file pointing at the live store (DB path, log path). `grep -rn "DATABASE\|DB_PATH\|database" <config>`.
   - **Process inspection:** `lsof -p <pid>` shows what files the app has open — the active log/DB file is usually there.
   - **Filesystem sweep:** `find <data-dir> -name "*.db" -o -name "*.sqlite*"` finds the obvious cases. For embedded stores, look for `leveldb/`, `rocksdb/`, or single-file binary stores.

3. **Recover.** Two paths:
   - **Query the live store directly.** Faster, more accurate. Often gives you exactly what you need without rebuilding.
   - **Read snapshots that aren't normally watched.** Crash dumps, temp files, debug logs, request bodies — these are often more complete than the production path because they're written before the sanitization/compression/rotation.

## "Trust the session_id, not the timestamp" rule

When recovering sessions from crash dumps or alternate stores, the date metadata in the *record* (timestamp field) is not always the date the *event* happened. Common off-by-one:

- **Crash dump:** `timestamp` = when the failure happened, often seconds-to-minutes after the actual event, sometimes crossing midnight
- **Queued message:** `received_at` = when the queue was drained, not when the user sent it
- **Replay log:** `recorded_at` = replay time, original is in the message body

**Always prefer the ID-embedded date** (e.g. `YYYYMMDD_HHMMSS_<hash>`) over the timestamp metadata. The ID is assigned at creation; the timestamp is assigned at storage.

## Recovery scripts as a pattern

When you build a recovery path for a pipeline, ship it as a CLI script in the skill's `scripts/` directory. It should:
- Take a date range or session_id as input
- Query the live store
- Write to the same output structure as the live pipeline
- Mark the recovered items with a distinct state prefix (`db:`, `dump:`, `recovered:`) so the live pipeline doesn't double-process

This makes recovery a one-liner, not a 4-step manual process every time.

**Example (Hermes save-session-to-obsidian):**
```bash
# Recover from state.db
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/backfill_from_db.py --since 2026-06-05
# Recover from a crash dump
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/backfill_request_dump.py ~/.hermes/sessions/request_dump_*.json
```

## Pitfalls

- **Don't fix the bug before backfilling if you might re-run the live pipeline** — recovered items need to be marked so the watcher skips them. Use a state prefix like `db:<id>`.
- **Don't assume the snapshot files are authoritative** — the live store is. Files are projections; they lag, get truncated, get lost in rotation. The DB is where the source of truth lives.
- **Don't trust the `timestamp` field for date routing** — it's the storage time, not the event time. Use the ID-embedded date.
- **Don't ignore crash dumps** — they often contain *more* information than the normal path (full request body, error context, attempt history). They're a free recovery source.
