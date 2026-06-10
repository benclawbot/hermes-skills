---
name: policy-vs-data-decisions
description: "Distinguish 'policy' (rules that get injected into every future prompt forever) from 'data' (facts scoped to a session, run, or artifact) before auto-promoting, auto-applying, or persisting anything. When in doubt, treat as policy and require explicit human approval with quality gate + TTL + audit trail."
triggers:
  - "auto-promote the lesson"
  - "apply this lesson going forward"
  - "remember this and use it next time"
  - "make this a default rule"
  - "learn from this and stop asking"
  - "remove the human in the loop"
  - "configure lessons to auto-apply"
---

# Policy vs Data Decisions

Anything that gets injected into future prompts, system messages, or default behavior for a class of task is **policy** — not data. Auto-promotion of "learned lessons" is a one-way door: a bad lesson becomes a recurring bug across every future run of that mode.

## The test

Before auto-promoting, auto-applying, or persisting any "lesson" / "pattern" / "rule" the agent claims to have learned, ask:

> Does this thing get injected into every future prompt for some mode / task / user? If yes, it's policy.

| Type | Scope | Auto-promote? |
|---|---|---|
| A fact about a specific artifact ("this file is at path X") | Data | Yes (it's already true) |
| A scoring rule ("correctness weighted 35%") | Policy | No — humans decide weight |
| A heuristic for a *new* task the agent has never seen | Policy | No — bad heuristic = recurring bias |
| A reflection on a single run ("this run took 12 turns, was that wasteful?") | Data | Yes (or don't, it ages out) |
| "When the user says X, do Y" | Policy | No — Y becomes a default forever |
| A correction of a one-off mistake | Data | Yes if logged, no if it generalizes |

## Default rule for lessons

Per spec, the lessons module is human-gated by default (`auto_promote: false`). Do not propose flipping the toggle without also proposing:

1. **Quality gate** — only auto-promote lessons with confidence / verification score above a threshold (e.g. ≥ 0.8)
2. **TTL** — every lesson expires (e.g. 7 days) and must be re-validated by runs
3. **Soft cap** — limit active lessons per mode (e.g. 5) so a runaway learner can't fill the prompt with garbage
4. **Audit trail** — log every promote/reject with reason, run ID, and confidence so a bad lesson can be traced and revoked

If the user pushes back ("just auto-promote, no gates"), push back in turn. A 30-second unfiltered auto-promote is a one-line config change but a multi-month recurring-bug surface.

## When "remove the human in the loop" is the right call

It rarely is. The human is the *quality gate* in the loop. If you want it removed, replace the human with a *better* gate, not no gate.

Cheaper alternatives to "no human":
- **Confidence-threshold auto-promote** — promote only above 0.8, leave borderline to human
- **Time-bounded auto-pilot** — auto-promote for 24h, then require re-validation
- **Shadow mode** — apply auto-promoted lessons but also log what would have happened with the old default; surface the diff for human review
- **Staged rollout** — auto-promote only on tasks that match a trusted-pattern fingerprint

## Memory-vs-skill placement

Some "lessons" are user-memory facts (Thomas is brief, Thomas wants `both` on parallel options, Thomas catches false claims). Those are already in `~/.hermes/memory.md` and persist correctly. Don't try to re-encode them in skills.

Some "lessons" are skill-update triggers (a workflow failed, a tool was missing, a deviation was needed). Those go in the relevant skill's `SKILL.md` or `references/`. See `no-replay` for the missing-trace reflex and `session-reflex` for the search-vs-assert asymmetry.

**Worked example:** see `references/sri-build-anti-pattern.md` for the self-recursive-improvement loop (2026-06-07) — a case study in shipping the *finished* version when the *minimum viable* version would have produced real data to justify the structure.

Don't conflate these with auto-promoted policy. Memory and skill updates are *curated by the agent*; lessons are *extracted from runs*. The curation is the quality gate.

## Refusal pattern

When the user asks for unfiltered auto-promotion of lessons, the response is not "yes, done" — it's:

> Auto-promote with no gate means a bad lesson becomes a recurring bug across every future run of that mode. The spec put the human there on purpose. I can flip the toggle (30 sec) or build a gated version (quality ≥ 0.8 + TTL 7d + soft cap 5/mode + audit) — pick which.

Both options are real. The point is to surface the tradeoff, not default the user into the dangerous one.

## Pitfalls

### Building the finished version before the minimum viable one

When the user asks for a system, the reflex is to ship the *complete* version: full schema, multiple cron tiers, versioned rubrics, security sections, architecture diagrams. Resist this.

**The pattern that fails:**
- 11 files, 4 crons, 7-criterion rubric, parser robustness layers
- 90 minutes of build before any data exists to justify the complexity
- User says "real talk, the minimum viable version is..."

**The right reflex:**
- Build the smallest thing that could plausibly work — 1 cron, 1 script, 1 DB table
- Run it for a week
- Add complexity only when the data asks for it (override rate plateaus → add rubric versioning; cron jobs collide → add DONE markers; etc.)

The "finished version" instinct is real because it feels like quality. It's not. It's premature optimization of a system that has zero runs of evidence. Ship working → gather signal → add structure.

**Test:** before adding a feature, can you name the data point that will tell you it was needed? If you can't, don't build it.

### "Wait" as a hedge

Every "wait", "we'll see", "let me check on that" in a response is a punt on a decision. Either:
- Decide and say what you're doing
- Flag the blocker as a clarifying question

"Wait" feels like humility. It's actually a refusal to commit. The user reads it as: "the agent saw a problem and is hoping it goes away." It doesn't go away.

**Trigger:** writing "wait", "we'll see", "let me check later", "TBD" in any response. Replace with: (1) the decision and its reasoning, or (2) a question that unblocks the decision.

**Source:** 20260607 self-recursive-improvement build, user feedback "every time you say 'wait' in your response it means there was a better path."

### Creating public artifacts without asking

The user-memory rule "Always confirm before opening PRs" extends to anything public-facing: GitHub repos, public packages, forum posts, social media content. Creating *and* pushing in one step skips the confirmation step.

**The pattern that fails:**
- `gh repo create <org>/<name> --public --push` — creates + pushes in one call
- User had to retroactively ask "is this safe?" — and could only approve/reject/delete, not shape the choice

**The right reflex:** When the action is *irreversible* or *publicly visible*, ask first. Even if the user said "make it public" earlier, that didn't authorize the *specific* repo name, description, or push target. Confirm the specifics: "OK to create `github.com/<org>/<name>` as public with description X?" — then act.

**Applies to:** public repos, package publishes, social media posts, public documentation, public APIs. Does *not* apply to: local writes, local commits, files in user's home dir.
