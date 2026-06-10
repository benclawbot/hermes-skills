# Watchdog Debug Recipe

How to diagnose "sessions exist on disk but Conversations/ in Obsidian isn't getting them" — the gap between source and vault.

## Symptom

User reports: "I see entries for some dates in `~/Desktop/Memory/Conversations/` but not others. The pipeline used to work."

## The 5-step recipe (in order)

### Step 1 — Identify what Hermes is actually writing

```bash
ls -lt ~/.hermes/sessions/ | head -20
```

Look at the **extensions** (`.json` vs `.jsonl`) and **patterns** (`session_*` vs `YYYYMMDD_HHMMSS_*`). Don't trust the SKILL.md's documented "4 formats" — the writer has changed containers at least twice (June 2026: `.jsonl` → `.json` → `.jsonl`). The skill doc lags the runtime.

### Step 2 — Confirm cron exists and is running

```bash
hermes cron list
```

Look for `session-to-obsidian watchdog`. Must be `[active]`. Check `Last run:` timestamp and `Mode: no-agent (script stdout delivered directly)`. `Last run: ok` is necessary but not sufficient — Sandy scenarios can return exit 0 without doing anything.

### Step 3 — Verify the wrapper actually runs the watchdog

The cron `Script:` field points to a wrapper, not the script directly. Open that wrapper:

```bash
cat ~/.hermes/scripts/watch_sessions_sandy.sh
# OR
cat ~/.hermes/scripts/watch_sessions.sh
```

If the wrapper invokes a Sandy scenario JSON, open that scenario and confirm `params.command` calls the real watchdog:

```bash
cat ~/.hermes/sandy/scenarios/session-to-obsidian-watchdog.json
# Look for: "command": "python3 /home/thomas/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions.py"
```

If the scenario wraps the command in a wrong path or the script doesn't exist at that path, the cron silently no-ops.

### Step 4 — Inspect the state file

```bash
head -c 500 ~/.hermes/sessions/.session_watchdog_state | python3 -c "import json,sys; print(json.load(sys.stdin)[-5:])"
```

The newest filenames in the state tell you the last time the watchdog successfully processed anything. **If the newest state entry is older than the newest session file, the watchdog has stopped processing.**

### Step 5 — Run the watchdog manually and cross-check

```bash
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions.py
```

Expected outputs:
- `NO_NEW_SESSIONS` — nothing new to process, normal idle tick
- `PROCESSED:N` followed by vault paths — fixed it
- Python traceback — paste the error and debug

Then cross-check:

```bash
ls -lt ~/.hermes/sessions/*.json ~/.hermes/sessions/*.jsonl 2>/dev/null | head -10
echo "---"
ls ~/Desktop/Memory/Conversations/2026/2026-MM/  # for each recent month
```

The set of vault dates must be a subset of session-file dates. If vault is missing recent dates → pipeline broken. If vault has dates with no matching session files → something else wrote them (manual save, or the watchdog overwrote with stub data).

## Common root causes (seen 2026-06-07)

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| `Last run: ok` but vault stops updating | Sandy scenario's inner command uses wrong path or silent failure | Re-run manually; check `~/.hermes/sandy/scenarios/session-to-obsidian-watchdog.json` |
| State file is stale (oldest date is 5+ days old) | Glob patterns in `find_new_sessions()` don't match the current writer's format | Add the missing pattern to the glob, e.g. `SESSIONS_DIR.glob("[0-9]*_[0-9]*_*.jsonl")` |
| Session file is `.jsonl` not `.json` | Hermes switched container format; `json.load()` fails on a single line | Add a JSONL branch to `parse_session()` |
| Some days have no vault entry AND no session file | Session crashed before write, OR gateway connection lost | Check `request_dump_*.json` in sessions/ for max_retries_exhausted traces; check `~/.hermes/logs/gateway.log` for errors |
| Vault has Jun 1 + Jun 3 entries, nothing in between | Two distinct bugs: glob miss + parser miss | Fix both, then backfill manually with `watch_sessions.py` |

## Backfill procedure

When a gap is discovered and the watchdog is fixed, backfill missed sessions:

```bash
# Backup state first
cp ~/.hermes/sessions/.session_watchdog_state ~/.hermes/sessions/.session_watchdog_state.bak.$(date +%s)

# Clear state so watchdog re-scans everything
rm ~/.hermes/sessions/.session_watchdog_state

# Run watchdog — will process everything currently on disk
python3 ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions.py
```

Output: `PROCESSED:N` for each new file written. Idempotent — re-running after the state file is repopulated returns `NO_NEW_SESSIONS`.

**Caveat:** the watchdog appends to the daily vault file, not overwrites. If a partial entry already exists for a day, the backfill will create a second session marker on the same day. This is the intended behavior (one file per day, multiple session markers), but if a corrupt partial entry was written previously, the file may need manual cleanup first.

## Detection that triggered this recipe (2026-06-07)

User: "list what we've done in the last week in order"

Agent: pulled 10 recent sessions from `session_search` (the SQLite message DB), but the user could only see 2 in `~/Desktop/Memory/Conversations/2026/2026-06/` (Jun 1, Jun 3). The source had `*.jsonl` files for May 28+ and `session_*.json` for Jun 1, but nothing for Jun 2–7. The watchdog had been silently failing since the `.jsonl` writer took over from the `session_*` writer (or vice versa — both transitions broke it).

## Verification after the fix

1. `python3 watch_sessions.py` returns `PROCESSED:N` with N > 0 on first run
2. `hermes cron list` shows the watchdog's `Last run:` advancing every 15 min
3. New session files appear in `Conversations/` within one cron tick of session end
4. `head -c 500 ~/.hermes/sessions/.session_watchdog_state | python3 -c "..."` shows filenames matching the newest session files
