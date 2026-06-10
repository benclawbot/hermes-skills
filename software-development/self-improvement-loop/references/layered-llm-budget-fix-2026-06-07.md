# Layered LLM-Budget Fix — Session Notes (2026-06-07)

This is a session-specific record of the failed-then-fixed propose-step
overtime that validated the "LLM timeout fix is belt-and-suspenders"
pitfall in the parent SKILL.md. The pitfall is the rule; this file is
the worked session that proved the rule is necessary.

## Symptom

`python3 src/loop.py --skip-apply --dry-run` logged:

```
[propose] Mining 1 sessions with MiniMax-M3...
  - 20260520_235126_1935c6 (353 msgs)
    ! m3 call failed: The read operation timed out
```

The 353-message session blew the LLM call budget. The cycle completed
(judge step still ran on prior proposals) but the propose step
contributed nothing.

## What was tried, in order

Each fix alone was insufficient. They are layered for a reason.

### 1. `urllib.request.urlopen(req, timeout=30)` -> `timeout=60`

In `src/propose.py`. The cron cap is 120s for `no_agent` jobs.
Per-call budget should sit under that with margin. 30s was the
original default; 60s is the in-spec band.

**Result:** still timed out on the 353-msg session. The 60s budget
isn't being violated by the model -- it's being violated by the
*transcript size* being too large for the model to finish reading +
reasoning + emitting JSONL inside 60s.

### 2. `load_session(max_msgs=60)` -> `max_msgs=30` (head 15 + tail 15)

In `src/miner.py`. The default was `head 20 + tail 40 = 60`. The
worked value is `head 15 + tail 15 = 30`. The proposer needs framing
(the first 15 messages) and outcome (the last 15 messages); the middle
is implementation detail that costs input tokens without adding
signal.

**Result:** still timed out at 60s on a 30-message transcript. The
remaining 30 messages x the system prompt (avoid-list, stale memory,
pipeline gaps, self-incident injection) is already ~8K input tokens.
m3 on this provider occasionally exceeds 60s for inputs in that range.

### 3. `max_tokens=4000` -> `max_tokens=1500`

In `src/propose.py`. Proposals are short JSONL -- typically 5-15
lines per proposal. 4000 tokens of output headroom let m3 ramble
(`<think>...</think>` blocks, restatements of the rubric) past the
budget. 1500 is the right ceiling: forces terseness, cuts output
time roughly in half.

**Result:** propose call completed in ~36s for the next 3 sessions
(verified by reading `usage.completion_tokens` in the API response:
1219 tokens emitted, well under 1500). All 3 sessions returned
parseable JSONL. All three emitted `{"no_proposals": true, "reason":
"..."}` (correct rubric application -- the sessions had no
recurring patterns), and the parser correctly accepted the form.

### 4. `unmined_sessions(limit=3)` returning 0 with eligible candidates

In `src/miner.py`. After fixes 1-3, the loop logged
`[propose] No unmined sessions.` even though
`unmined_sessions(limit=10)` returned 10 candidates. Root cause: the
function scanned `list_sessions(limit=limit * 4 = 12)` and the top 12
most recent session files were all already-mined OR oversized OR too
small. The function gave up at 12 candidates scanned without ever
reaching an eligible one.

**Fix:** `list_sessions(limit=scan_window)` with a generous absolute
default (`scan_window=200`). The scan is a filename glob + a
`was_session_mined` check; 200 is cheap.

**Lesson:** any "find N candidates matching filter X" function
should either (a) scan all candidates and slice, or (b) use a
`scan_window` that's decoupled from `limit`. Multiplying the result
count by 4 is a code smell: it assumes density of matches is
roughly uniform across the recent window, which is not true when
many recent sessions are already-mined or filtered out for other
reasons.

## Other findings from this session

### Judge parser failures look like judge rejections

Proposal #1 in the DB had **9 judge verdicts** recorded. The first 2
were `verdict=reject, score=0.0`, the next 7 were `verdict=approve,
score=0.75-0.85`. The first 2 were not actual judge decisions --
they were parser failures:

```
reasoning: "[judge output unparseable: <think>Let me analyze this proposal against the rubric criteria..."
reasoning: "[judge output unparseable: {\n  \"verdict\": \"approve\",..."
```

The `reasoning` column carried the diagnostic, but `verdict` and
`score` were populated with **the parser's failure default**, not the
model's actual output. In both cases, the model's real verdict was
visible in the `reasoning` text -- once `approve`, once the rubric
analysis was incomplete but the intent was unclear.

**Implication for override-rate math:** if you compute
`override_rate = count(verdict=reject) / count(*)` over
`judge_verdicts` without filtering for
`reasoning LIKE '[judge output unparseable%'`, you under-count
approvals and over-count rejections. The result is an artificially
high override rate, which then triggers the rubric self-eval to
propose rubric rewrites that aren't actually needed.

**Recommended fix (not applied in this session):**
- Add a column `parse_failed BOOLEAN` to `judge_verdicts`, default 0.
- Set it to 1 when the parser returns no JSON object.
- Filter `parse_failed=1` rows out of every override-rate /
  approval-rate query, both in `digest.py` and in `self_improve.py`.

This is a Phase-3 "pipeline gap" -- a real defect in the loop's
machinery that the next proposer cycle should propose a fix for.
Specifically, the proposer prompt's "Pipeline gaps from last 7 days"
section already feeds back loop-internal errors as `category='gap'`
lessons. The fix-proposal mechanism is in place; it just needs the
parser to write the lesson when it fails.

### Incident-watcher caught the very cycle we ran

After the fixes landed, the cycle completed in 174.4s. The
incident-watcher's threshold for `sri-cycle/wall_time_high` is 110s.
A `self_incidents` row was written:

```
job_name: sri-cycle
incident_type: wall_time_high
detail: last cycle 174.4s (threshold 110s)
```

On the next propose cycle, this incident is fed back as a synthetic
"session" under "Self-referential incident (Phase 4)" in the system
prompt. The proposer can then propose a fix (e.g. drop
`max_sessions` from 3 to 2, or split sri-cycle into even narrower
stages). This is the loop catching its own slowness -- exactly the
design intent.

### Proposal #1 (premortem skill patch) is real and ready to apply

The judge has been calling it approve at 0.75-0.85 for the last 7
verdicts. The diff adds a pitfalls section clarifying that
premortems are analysis-only and the agent must not edit the user's
tree without explicit confirmation. Evidence is a specific session
(`20260527_115313_815bc435`) where the agent rewrote `ipc_client.py`
when the user asked for a "blind spots" report. No `thomas_feedback`
row exists yet -- the proposal is awaiting human verdict. The skill
file is at `~/.hermes/skills/premortem/SKILL.md`; the apply step
should verify it's not hub-installed before writing.

## Files changed in this session

- `src/propose.py`: `timeout=30` -> `timeout=60`, `max_tokens=4000`
  -> `max_tokens=1500`
- `src/miner.py`: `load_session(max_msgs=60)` -> `max_msgs=30` with
  `head 15 + tail 15`; `unmined_sessions()` gains `max_messages=200`
  and `scan_window=200` parameters.

No DB schema changes. No prompt changes. No rubric changes.
