# Watchdog "Active but Silent" — Debugging Recipe

When a cron job shows `[active]` and `last_status: ok` but the thing it watches is not happening, the cron layer is *fine* — the bug is downstream. The classic patterns:

## Pattern A — Sandy wrapper silently no-ops

**Symptom:** Cron job is `active`, `last_status: ok`, no error in the journal. The underlying script never runs (or runs and produces empty output).

**Diagnosis:**
```bash
# 1. Look at the wrapper the cron actually invokes
hermes cron list  # find the Script: field
cat ~/.hermes/scripts/watch_xxx_sandy.sh
# 2. Look at the scenario it calls
cat ~/.hermes/sandy/scenarios/<scenario>.json
# 3. Run the inner command directly to see real error
python3 <inner-command-from-scenario>
```

**Common root causes:**
- The scenario `params.command` points to a path that no longer exists (renamed/removed script)
- The Sandy player swallows stderr and only shows it on failure — if the inner command is wrong but exits 0, you see nothing
- The wrapper script has auto-fix logic (e.g. installs missing modules) that masks the original error

**Test:** Create a `touch /tmp/canary` from the inner command, then run the wrapper. If canary never appears, the wrapper isn't reaching the script.

## Pattern B — Format mismatch between writer and watcher

**Symptom:** Cron is active, last_status=ok, but the output is stale (no new entries). Recently, the writer changed file format (e.g. `.json` → `.jsonl`) but the watcher's glob patterns only match the old format.

**Diagnosis (4 steps, in order):**

1. **See what the writer is actually producing:**
   ```bash
   ls -lt <source-dir>/ | head -20
   ```
   Note the extensions on the newest files. If they don't match the patterns in the watcher, that's the bug.

2. **See what the watcher claims to match:**
   - Read the watcher's source (`grep -n "glob\|<pattern>" <watcher.py>`)
   - Read the skill's SKILL.md "formats" table
   - **The two often disagree.** The SKILL.md is documentation lag; the source is the truth.

3. **Run the watcher manually and compare:**
   ```bash
   python3 <watcher.py> 2>&1
   ```
   - `NO_NEW_SESSIONS` — watcher ran fine, found nothing. Bug is upstream of the watcher.
   - `PROCESSED:N` followed by paths — watcher ran, processed N files. The pipeline is fine *now*; the question is what was missed.
   - Python traceback — the watcher itself is broken. Fix the script.

4. **Cross-check the state file vs the source dir:**
   ```bash
   # Newest entries in the state file (the watcher's memory)
   tail -c 500 <state-file> | python3 -c "import json,sys; print(json.load(sys.stdin)[-5:])"
   # Newest files in the source dir
   ls -t <source-dir>/*.json* | head -5
   ```
   **If the newest state-file entry is older than the newest source file, the watcher has been silently broken for that gap.** That's the data loss.

**Prevention — make the next silent break loud (add this to the watcher's find function):**

```python
import sys
from pathlib import Path

# Inside find_*_sessions(processed), after the glob:
def coverage_check(SESSIONS_DIR, STATE_FILE, gap_threshold_seconds=86400):
    """Emit STALE_STATE_WARNING if newest source file is much newer than newest state entry.
    Catches the "pipeline silently broke because glob didn't match" failure mode
    that state-based dedup is structurally blind to."""
    try:
        newest_session = max(
            (f.stat().st_mtime for f in SESSIONS_DIR.iterdir()
             if f.is_file() and f.suffix in (".json", ".jsonl") and not f.name.startswith("sessions.")),
            default=0.0,
        )
        state = json.loads(STATE_FILE.read_text() or "[]")
        newest_state = 0.0
        for name in state:
            if name.startswith("db:"):  # backfill marker, not a real file
                continue
            p = SESSIONS_DIR / name
            if p.exists():
                newest_state = max(newest_state, p.stat().st_mtime)
        if newest_session and newest_state:
            gap = newest_session - newest_state
            if gap > gap_threshold_seconds:  # default 24h
                print(
                    f"STALE_STATE_WARNING: newest session is {int(gap/3600)}h newer than newest "
                    f"processed state entry. Check glob patterns — pipeline may be silently "
                    f"dropping sessions.",
                    file=sys.stderr,
                )
    except (OSError, ValueError, json.JSONDecodeError):
        pass

# And add the unmatched-format warning alongside:
for f in SESSIONS_DIR.iterdir():
    if not f.is_file():
        continue
    n = f.name
    if n.endswith(".json") and not n.startswith(("known_prefix_1", "known_prefix_2")):
        print(f"UNMATCHED_SESSION_FORMAT: {n} (consider adding to watcher patterns)", file=sys.stderr)
```

These two checks make the next silent break loud instead of silent. Surface the stderr output via your cron delivery mode (Sandy can do this; bare `*/15 * * * * script.sh` won't unless you `set -x` or `tee` to a log).

## Pattern C — Source of truth isn't where you think

**Symptom:** Files the watcher reads are missing or truncated. You need to recover what was dropped.

**Where to look:**
1. **The watcher's own state file** — tells you what it *thinks* it processed (may be wrong)
2. **The application's "live" store** — for Hermes that's `~/.hermes/state.db` (SQLite). The `messages` table has every message Hermes ever processed, regardless of whether the file writer succeeded
3. **Crash dumps** — when the API call exhausts retries mid-session, Hermes writes `request_dump_*.json` containing the full request body. The session is recoverable from there
4. **Log files** — `~/.hermes/logs/agent.log` has request/response pairs; you can reconstruct sessions from request bodies

**Recovery scripts (for the save-session-to-obsidian pattern):**
- `backfill_from_db.py --since YYYY-MM-DD` — pull from state.db by date window
- `backfill_request_dump.py <path>` — recover from a single crash dump
- Both write to the same Obsidian file structure as the live watcher, with `db:<id>` or `request_dump_<filename>` state markers so the live watcher won't double-process

**The "trust the session_id, not the timestamp" rule:** Crash dumps have a `timestamp` field (= when the failure happened, often seconds-to-minutes after the actual session, sometimes crossing midnight). The `session_id` embeds the session's *start* time as `YYYYMMDD_HHMMSS_<hash>`. Always use the session_id for date routing.

## Pattern D — Cron was paused/disabled and you didn't notice

**Symptom:** Output is missing. The user assumes pipeline is broken. Reality: cron is paused or in a stuck state.

**Diagnosis:**
```bash
hermes cron list  # check [active] vs [paused] tags
hermes cron list -v  # verbose — shows last_status
```

`last_status: ok` only means the *most recent* scheduled run completed. If a job was paused for 3 days and resumed, the state file is current but the gap is unfilled — you still need a backfill.

## Pattern E — SKILL.md and code drift apart

**Symptom:** The skill doc claims the pipeline handles "4 formats" (or similar coverage claim), but the actual script only matches 1. The doc was last updated by a patch that fixed the doc, not the code. This is the most insidious variant of Pattern B because the doc actively hides the bug from the next person who reads it.

**Diagnosis:**
1. **Compare the SKILL.md's "supported formats" / "patterns" / "source files" section against the actual `glob()` / `os.listdir()` / extension checks in the script.** They should agree. If they disagree, trust the code.
2. **Check the git/file history of the SKILL.md vs the script.** Patches that touched only one of the two are the suspect.
3. **Cross-check with what the writer actually puts on disk** (`ls -lt` the source dir). If new extensions appeared after the last SKILL.md update, the doc is the liar.

**Prevention:**
- When patching a script that handles data files, also update the SKILL.md's format table in the same patch
- When patching the SKILL.md, don't claim coverage the code doesn't have — flag the gap as a known issue instead
- Add a "format table vs runtime" check to the SKILL.md as a section header that future patches must touch

The save-session-to-obsidian skill fell into this exact trap in 2026-06: SKILL.md v1.4 claimed "all 4 formats are monitored" but the underlying glob patterns only matched `.json` with known prefixes, never `.jsonl`. The drift was invisible for 33 days because the doc and the code were wrong in the same direction.

## Pitfalls

- **Don't trust "active" + "ok" as proof of working** — the cron layer can be perfectly fine while the script is silently misconfigured.
- **Don't trust the SKILL.md format table blindly** — the Hermes writer has changed file format mid-stream at least twice (June 2026: `.jsonl` → `.json` → `.jsonl`). The skill's table lagged. Always `ls -lt` the source dir first.
- **Don't trust the SKILL.md over the code** — the doc is documentation, the code is the truth. If they disagree, fix the code (and then the doc).
- **Don't assume the source dir is the only source of truth** — `state.db` (SQLite) is the live record of what Hermes actually did. If the JSON files are missing or partial, the DB has the rest.
- **Don't backfill before you understand why the pipeline broke** — fixing the bug first means the backfill doesn't get duplicated when the watcher comes back online. Mark backfilled items with `db:<id>` state so they're identifiable.
