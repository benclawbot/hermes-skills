# Self-recursive-improvement build — anti-pattern worked example

**Date:** 2026-06-07
**Context:** Thomas asked for an autonomous self-improvement loop with three components (m3 proposes, m2.7 judges, override drives rubric refinement). He asked for it to run 3×/day and live in a public repo. I built the *finished* version.

## What I built (overkill)

- 11 source files (db, miner, propose, judge, apply, digest, self_improve, loop, rubric, __init__, run_cycle.sh)
- 4 cron jobs (cycle every 8h, apply daily, digest weekly, rubric-eval monthly)
- 7-criterion rubric v1
- Strict-JSONL parser with think-block stripping on both sides
- Full security section in README
- Architecture diagram in README
- All edges handled: pinned-skill protection, backup-before-write, idempotency markers, path validation
- 90 minutes of build time, 0 cycles run

## What the minimum viable version was

> "1 cron, once a day. Read last 24h sessions → m3 proposes (ask for plain JSON, retry on parse fail). m2.7 judges. m3 sends Telegram message with `approve #N` / `reject #N` inline buttons. Telegram receives the tap → DB updates → if approve, apply inline. m3 itself notices override patterns in the weekly digest and suggests rubric tweaks in the message body."

— Thomas, mid-build, when I hit the iteration wall

10 files → 1 script. 4 crons → 1 cron. Full apply step → inline. Strict parser → retry. Separate rubric table → self-noticed in the digest message.

## What I should have done instead

After the user asked for the loop, I should have:
1. Written the 1-script minimum (one file, one cron, propose+judge+telegram in one place)
2. Run it once
3. Looked at the output
4. Asked "is this signal real?" before adding any of the structure

What I actually did:
1. Designed the full 4-tier system
2. Wrote the schema
3. Wrote the rubric with 7 criteria
4. Wrote the parsers with 3 layers of robustness
5. Wrote the tests
6. Wrote the README with security section
7. Wrote the crons
8. Ran one cycle
9. Discovered I'd guessed wrong on several things (e.g. m2.7 emits think blocks too — only caught when the judge returned `[judge output unparseable]`)

## The data-point test for added complexity

Before adding a feature, I should ask: "what run would tell me this feature was needed?" For each piece I added:

| Feature | What run would prove it was needed? |
|---|---|
| `apply.py` (separate file) | Two consecutive cycles where approved proposals pile up un-applied |
| DONE markers for idempotency | Two `apply.py` runs that double-wrote the same change |
| `self_improve.py` (separate file) | 10+ overrides logged with consistent patterns |
| Rubric versioning | Override rate plateauing at the same level across 50+ judgements |
| 4 cron jobs | Cron collision observed in logs |

None of these had data. I built all of them anyway.

## When "ship finished" loses to "ship working"

The `policy-vs-data-decisions` skill already covers this in the "Building the finished version" pitfall. This file is the concrete worked example for that pitfall.

The cost of building the finished version when you don't have data:
- 90 minutes of work
- 0 cycles of evidence
- A repo URL you can't easily retract if the design is wrong
- A codebase the user has to read before they can steer the direction

The cost of shipping the minimum viable version:
- 1 file, 1 cron, ~30 minutes
- After 1 cycle: real data on what the loop actually produces
- After 1 override: real signal on what m2.7's rubric should ask
- After 1 week: real knowledge of what the user actually reviews vs ignores

## Apply this lesson when:

- User asks for a system with N components
- I have an urge to build all N components in one go
- I have 0 cycles of evidence for any of them
- The user is engaged enough to give feedback after the first run

In all four cases: build the smallest thing that exercises the loop end-to-end, then add structure when the data asks.

## The "wait" rule (related lesson from same session)

After hitting the iteration wall, I wrote a "wait, first run just completed" line in the summary. Thomas flagged it: "every time you say 'wait' in your response it means there was a better path."

The pattern: "wait" / "we'll see" / "let me check later" → user reads it as "agent saw a problem and is hoping it goes away." It doesn't.

Fix: either decide and state the decision, or ask a clarifying question that unblocks the decision. Never punt with "wait."

This is captured in the SKILL.md "Wait as a hedge" pitfall.
