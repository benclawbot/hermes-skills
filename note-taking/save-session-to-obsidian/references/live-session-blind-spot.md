# Live-session blind spot: when the file watcher can't see what just happened

## Symptom (2026-06-08, thomas)

> "my most recent conversations (last 2 days) are not stored in the right subfolder in obsidian, can you check why?"

Vault files for the affected days were 600-1500 bytes — single-exchange stubs. State.db had sessions with 90-240 messages. JSONL/JSON dumps in `~/.hermes/sessions/` stopped at the day before.

## Root cause

The file-based watchdog (`watch_sessions.py`) globs `~/.hermes/sessions/` for `session_*.json` / `*.jsonl` / `hermes_conversation_*.json`. It only sees sessions that have **ended AND produced a file dump on disk**. Two failure modes make a session invisible:

1. **Live/unclosed sessions** — `ended_at IS NULL` in `state.db`, so no file is written. They accumulate in the DB but never trigger the file watcher.
2. **Gateway crash, short TTL, suppressed file write** — session ends, but the JSON/JSONL dump never lands. `state.db` has the full transcript; the filesystem does not.

The original SKILL.md (v1.6.0) said: *"marks backfilled items as `db:<id>` in the state file so the live watcher won't double-process."* The code did add the marker, but `backfill_sessions()` never checked it before writing. The `db:` marker was decorative, not a gate. Re-running on a populated state wrote dupes.

This was the second silent breakage pattern for this pipeline — the first was the `.jsonl` vs `.json` container mismatch (SKILL.md v1.4 claimed "4 formats" but the glob only matched 3). Both surfaced only when the user noticed missing data.

## Diagnosis recipe (4 checks, ~30 seconds)

```bash
# 1. What files actually exist on disk?
ls -lt ~/.hermes/sessions/ | head -20
# Note: .json vs .jsonl, the date in the filename, the mtime

# 2. What's actually in state.db?
python3 -c "
import sqlite3
from datetime import datetime
con = sqlite3.connect('file:///home/thomas/.hermes/state.db?mode=ro', uri=True)
con.row_factory = sqlite3.Row
for r in con.execute('SELECT id, source, started_at, ended_at, message_count FROM sessions ORDER BY started_at DESC LIMIT 15'):
    st = datetime.fromtimestamp(r['started_at']).strftime('%Y-%m-%d %H:%M')
    en = datetime.fromtimestamp(r['ended_at']).strftime('%H:%M') if r['ended_at'] else 'open'
    print(f'{st} → {en:5s} | {r[\"source\"]:8s} | msgs={r[\"message_count\"]:3d} | {r[\"id\"]}')
"

# 3. Cross-check: do vault dates ⊆ session-file dates?
ls ~/Desktop/Memory/Conversations/2026/2026-MM/

# 4. Are the new sessions in state.db but missing files? (the gap)
python3 -c "
import sqlite3, os
con = sqlite3.connect('file:///home/thomas/.hermes/state.db?mode=ro', uri=True)
files = {f.rsplit('.',1)[0] for f in os.listdir(os.path.expanduser('~/.hermes/sessions'))}
saved = os.path.expanduser('~/.hermes/sessions/saved')
if os.path.isdir(saved):
    files |= {f.rsplit('.',1)[0] for f in os.listdir(saved)}
for r in con.execute('SELECT id, message_count, ended_at FROM sessions WHERE ended_at IS NOT NULL AND message_count > 0 ORDER BY started_at DESC LIMIT 30'):
    sid = r[0]
    in_files = any(sid in f for f in files)
    if not in_files:
        print(f'GAP: {sid} ({r[1]} msgs) — ended, in DB, NO FILE')
"
```

If step 4 prints anything, the file watcher is structurally blind to those sessions. Use the DB-poll companion (`watch_sessions_db.py`).

## The fix (already shipped 2026-06-08)

Two changes, both in this skill:

1. **`scripts/watch_sessions_db.py`** — new no_agent cron script, every 30 min. Queries `state.db` for ended sessions with `message_count > 0` and no file on disk. Calls `backfill_sessions()` with the missing ids. Silent on no-op (watchdog pattern).

2. **`scripts/backfill_from_db.py`** — now checks `db:<sid>` in state before writing. Skips already-marked sessions. The marker is now an actual dedup gate, not just a record.

Cron job:
```
hermes cron create "*/30 * * * *" --script watch_sessions_db.sh \
  --name "session-to-obsidian db-poll" --no-agent
```

## Recovery after a long gap (the original symptom)

```bash
# 1. Backfill everything since the last good vault date
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/backfill_from_db.py --since YYYY-MM-DD

# 2. Identify and clean dupes (if backfill was run twice during the same gap)
python3 << 'EOF'
import re
from pathlib import Path
CONV = Path('/home/thomas/Desktop/Memory/Conversations')
for f in sorted(CONV.rglob('*.md')):
    text = f.read_text()
    parts = re.split(r'(^### Session .+$)', text, flags=re.MULTILINE)
    if len(parts) < 3: continue
    seen = set(); new = [parts[0]]; removed = 0
    i = 1
    while i < len(parts) - 1:
        marker, body = parts[i], parts[i+1]
        m = re.search(r'recovered from state\.?db\s+(\S+?)\)?$', marker)
        key = m.group(1).rstrip(')') if m else marker
        if key in seen: removed += 1
        else: seen.add(key); new.append(marker + body)
        i += 2
    if parts[-1] and not parts[-1].startswith('### Session'): new.append(parts[-1])
    if removed: f.write_text(''.join(new)); print(f'{f.name}: removed {removed} dupe(s)')
EOF

# 3. Re-run the DB-poll — should now be silent (idempotent)
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions_db.py
```

## What to verify going forward

The pipeline is now defense-in-depth:

- `watch_sessions.py` (15 min) — file watcher, catches anything that produces a dump
- `watch_sessions_db.py` (30 min) — DB poll, catches the "ended but no file" gap
- `backfill_from_db.py` — manual one-shot, idempotent

**Sanity check the two watchdogs are both running:**
```bash
hermes cron list | grep -E "watchdog|db-poll"
# Expect both "session-to-obsidian watchdog" and "session-to-obsidian db-poll"
```

**Sanity check the state is making forward progress:**
```bash
python3 -c "import json; d=json.load(open('/home/thomas/.hermes/sessions/.session_watchdog_state')); print('Last 3:', d[-3:])"
# Expect entries with recent dates
```

If the state stops advancing for >24h, the STALE_STATE_WARNING in `watch_sessions.py` will fire on the next tick — check `~/.hermes/logs/gateway.log` or wherever the cron delivers stderr.
