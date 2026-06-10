# sri-cycle → sri-propose + sri-judge: Splitting an LLM-Backed Cron

**Source:** `~/Recursive-Self-Improvement/`, commit `ef78713` (June 2026).
**Symptom:** `sri-cycle` cron failed with `Script timed out after 120s` and
no log file written. Previous cycle had finished in ~5 min successfully,
making the failure look transient.

## The setup that broke

`src/loop.py` ran all three steps in one script:
- STEP 1: PROPOSE — m3 LLM call per session (3 sessions → up to 3 API hits)
- STEP 2: JUDGE — m2.7 LLM call per proposal (1-3 proposals)
- STEP 3.5: GRADE OUTCOMES — local heuristics, no LLM

Per-call urllib timeout was 120s (in `propose.py`) and 60s (in `judge.py`).
The 120s cron cap is the Hermes scheduler hard limit on `no_agent` script
jobs — not configurable from inside the script.

## Why the previous run "worked" (and this one didn't)

A 5-min run had been completing the day before, but that was a lucky
window. On the failing day, a 353-message session pushed propose past
the cron cap. A single hung call == the entire cycle dies. And critically,
**cron kills the parent shell before stdout flushes**, so the log file
is never written. `last_status: error` with no `logs/cycle_*.log` to
inspect is the signature.

## The fix — two changes, applied together

### 1. Lower per-call urllib timeouts (defense in depth)

```python
# propose.py
urllib.request.urlopen(req, timeout=30)   # was 120

# judge.py
urllib.request.urlopen(req, timeout=30)   # was 60
```

If the API hangs, the call throws `socket.timeout` after 30s, the
caller catches it, the script exits cleanly with a real log file.

### 2. Add `--propose-only` flag and split into two cron jobs

```python
# src/loop.py
def cycle(skip_apply=False, judge_only=False,
          propose_only=False, dry_run=False, max_sessions=3):
    ...
    if not judge_only:
        ...  # PROPOSE step
        if propose_only:
            return result   # <-- exit before judge
    ...  # JUDGE step
```

```bash
# ~/.hermes/scripts/sri-propose.sh
#!/usr/bin/env bash
set -e
cd ~/Recursive-Self-Improvement || exit 1
LOG=logs/propose_$(date -u +%Y%m%d_%H%M%S).log
python3 src/loop.py --propose-only --max 3 > "$LOG" 2>&1
EXIT=$?
tail -30 "$LOG"
exit $EXIT

# ~/.hermes/scripts/sri-judge.sh
#!/usr/bin/env bash
set -e
cd ~/Recursive-Self-Improvement || exit 1
LOG=logs/judge_$(date -u +%Y%m%d_%H%M%S).log
python3 src/loop.py --judge-only --skip-apply > "$LOG" 2>&1
python3 src/grade_outcomes.py >> "$LOG" 2>&1
tail -30 "$LOG"
exit $?
```

```bash
# Update the existing job (was sri-cycle, becomes sri-propose)
hermes cron update <job_id> --name sri-propose --script sri-propose.sh

# Add the new judge job, 5 minutes later
hermes cron create sri-judge --schedule "5 */8 * * *" \
  --script sri-judge.sh --no-agent
```

## Why 5 minutes offset

Propose on N sessions finishes well within 5 min on a healthy API. If
propose is *still* running at minute 5, the next run will just find an
empty `pending` queue and exit silently — no harm done, the late
proposals get picked up on the *next* 8h cycle or by the daily
`apply.py` cron.

If you want tighter coupling, use a polling sleep in the judge script
that checks for pending proposals. We didn't bother — 5 min drift is
invisible at this granularity.

## What to check after deploying

1. `hermes cron list` — both jobs should show `last_status: ok` after
   the next tick.
2. `tail -30 logs/propose_*.log` — should show propose + exit
   cleanly. A 30s urllib timeout will surface here as a `socket.timeout`
   traceback; that's normal API behavior, not a loop bug.
3. `tail -30 logs/judge_*.log` — should show judge + grade + exit.
4. The first cycle after the split may show 0 proposals if propose
   timed out (logged) and judge found nothing. That's the failure
   mode being detected, not a new bug.

## What NOT to do

- **Don't try to raise the 120s cron cap.** It's a scheduler-level
  constraint, not a per-job setting. Bumping it for one job is not
  exposed via the `cronjob` tool.
- **Don't wrap python in `timeout 600`.** Same problem — the shell
  gets killed at 120s by the scheduler, and any sub-process timing
  doesn't help.
- **Don't lower `--max 3` to 1 as a "fix".** The 120s per-call is
  the real cap, not the number of sessions. One hung call on one
  session still dies at 120s. Splitting is the real fix.
- **Don't combine propose + judge into one script and rely on
  "the API is usually fast."** It usually is, until it isn't, and
  the failure is invisible (no log file).
