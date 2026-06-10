---
name: pm-350-risk-review-meetings
description: Facilitate recurring risk review meetings — surface high-impact risks, assess probability and impact, update response strategies, and escalate critical items to sponsors.
phase: monitoring
tier: 2
---

# Risk Review Meetings (pm-350)

## What It Does

Facilitates recurring risk review meetings — surfaces high-impact risks, assesses probability and impact, updates response strategies, and escalates critical items to sponsors before they materialize.

## When to Use

- Scheduled risk review cadence (weekly or bi-weekly)
- When a new high-impact risk is identified outside the normal cadence
- Prior to major project milestones or phase transitions
- After a risk event occurs or a mitigation plan is executed

## Inputs

- Risk register (pm-120)
- Risk response plans with owners and due dates
- Recent issue log and project status updates
- Open action items with risk implications

## Workflow

1. **Pre-meeting preparation** — Pull the risk register and filter for risks with status `open`, `escalated`, or `triggered`. Sort by risk score (probability × impact). Identify the top 10 risks by score. Distribute the list to participants 24 hours before the meeting.
2. **Call the meeting to order** — Confirm attendees (risk owner, project manager, impacted team leads, sponsor if escalation is on the agenda). Review the meeting purpose: surface risks, validate scoring, update response plans, escalate where needed.
3. **Walk the risk register** — For each risk on the pre-meeting list: confirm current risk score (have probability or impact changed?), review mitigation status, check owner accountability, and note any new risk events that have occurred since the last review.
4. **Assess new risks** — Open the floor to participants to surface any new risks not yet in the register. For each new risk: assign an owner, estimate probability and impact, calculate risk score, and define an initial response strategy.
5. **Update risk scores and statuses** — For existing risks that have changed: update probability, impact, or score. Close risks that have been fully mitigated or have passed without occurring (deprecate them with rationale). Ensure all changes are logged with a timestamp.
6. **Review response plan health** — Check that all high-priority risks have a response plan with an assigned owner and a due date. Flag any response plans that are overdue. Adjust plans if the risk landscape has shifted significantly.
7. **Escalate critical risks** — Identify risks with a score above the escalation threshold (e.g., 15 or above on a 1–25 scale). Prepare a one-page risk brief for the sponsor. Obtain sponsor acknowledgment and any decisions required.
8. **Close the meeting** — Summarize action items, owners, and due dates. Confirm the date for the next risk review. Distribute meeting notes and updated risk register to all participants within 4 hours.

## Outputs

- Updated risk register with current scores, statuses, and owners
- Meeting minutes with decisions, action items, and owners
- Escalation briefs for sponsors
- New or modified response plans with owners and due dates

## Verification

- Pull the risk register before and after a risk review meeting — confirm that all open risks have been reviewed (no stale entries older than the last review date).
- Verify that new risks added during the meeting appear in the register with owners, scores, and response plans.
- Confirm that escalation briefs have been sent to sponsors for all risks scoring above the escalation threshold.
- Check that action items from the previous meeting have been completed or carried forward with updated due dates.

## Tips

- Keep the review focused on high-scoring risks — do not re-litigate every risk in the register. Limit the pre-meeting list to the top 10 by score.
- Risk scores are estimates, not absolutes. If two risk owners disagree on probability, use a simple vote or average — do not let scoring debates consume the meeting.
- When a risk materializes, close it in the register and open an issue in pm-170 immediately. Do not let triggered risks linger in the risk register.
- Escalation thresholds should be agreed upon at project kickoff. If the sponsor is unreachable for an urgent escalation, document the attempt and proceed with the most conservative mitigation path.