---
name: pm-300-milestone-stage-gate
description: Track project milestones and stage gate reviews — trigger reviews at each phase transition, collect go/no-go decisions, and escalate blocked gates.
phase: monitoring
tier: 2
---

# Milestone & Stage Gate Review (pm-300)

## What It Does

Tracks project milestones and stage gate reviews — triggers reviews at each phase transition, collects go/no-go decisions, and escalates blocked gates.

## When to Use

- A project phase completes and a stage gate review is due
- A milestone date is approaching (3 days, 1 day, same day)
- A gate decision is pending beyond the scheduled review window
- Escalated gate issues require sponsor resolution

## Inputs

- Active milestone list with due dates and decision owners
- Phase deliverable status report
- Risk and issue log
- Previous stage gate outcomes

## Workflow

1. **Identify active milestones and pending gates** — Query the project tracker (Linear, Jira, or spreadsheet) for milestones with status `open` or `at-risk`. List each gate's scheduled date, decision owner, and current status.
2. **Check milestone health indicators** — For each milestone within 3 days, calculate: % completion of precursor deliverables, open critical issues, and any flagged blockers. Summarize as green/amber/red.
3. **Generate gate review agenda** — Produce a structured agenda: (1) Deliverables review, (2) Criteria assessment, (3) Risk acceptance, (4) Go/No-Go vote, (5) Conditions and caveats. Tag owner and sponsor.
4. **Conduct gate review meeting** — Walk through the agenda, capture decision, rationale, and any conditional requirements. Obtain verbal or written sign-off from decision owner.
5. **Record gate decision** — Log the decision (Go / Conditional Go / No-Go / Escalate) with rationale, conditions, and timestamp. Update milestone status in the tracker.
6. **Escalate blocked gates** — If a gate has been pending more than 24 hours past its scheduled date, notify the project sponsor and log an escalation ticket. If No-Go, trigger the issue register (pm-170).

## Outputs

- Completed stage gate review agenda with decisions
- Updated milestone status (open / completed / blocked / escalated)
- Escalation notifications sent to sponsor
- Issue entries for No-Go or blocked gates

## Verification

- Run `list_milestones(status=open)` — all active milestones should appear with due dates and decision owners
- Confirm pending gates older than today trigger escalation notification
- Spot-check: update a milestone with a Go decision; verify status changes to `completed`

## Tips

- Do not confuse milestone dates with gate review dates — a gate is the review meeting, the milestone is the deliverable/phase completion date
- If decision owner is unavailable, do not default to Go — escalate instead
- Conditional Go decisions must have written conditions logged before the next phase begins
- Stage gates are governance events, not just status updates — allocate time for deliberation
