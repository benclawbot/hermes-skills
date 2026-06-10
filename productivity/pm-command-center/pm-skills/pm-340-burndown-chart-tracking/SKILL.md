---
name: pm-340-burndown-chart-tracking
description: Track sprint and release burndown charts — calculate ideal vs. actual progress, identify velocity trends, and flag slips early.
phase: monitoring
tier: 1
---

# Burndown Chart Tracking (pm-340)

## What It Does

Tracks sprint and release burndown charts — calculates ideal vs. actual progress, identifies velocity trends, and flags slips early so corrective action can be taken before sprints derail.

## When to Use

- Daily or weekly sprint tracking meetings
- Release planning and forecasting
- Velocity and trend analysis for sprint retrospectives
- When a sprint is at risk of not completing its commitment

## Inputs

- Sprint backlog with story points or ideal days per ticket
- Daily or hourly task completion updates
- Sprint start and end dates
- Team capacity and availability ( PTO, meetings, holidays)

## Workflow

1. **Pull current sprint data** — Export or query the sprint board for all open, in-progress, and completed tickets with their point values and last-updated timestamps.
2. **Calculate ideal burndown line** — On day 1, total points = full scope. On last day, total = 0. Draw a straight diagonal. Adjust for non-working days (weekends, holidays) to create a realistic ideal curve.
3. **Plot actual progress** — Each day, record the remaining total points. Plot as a curve on the same chart as the ideal line. A rising curve above ideal signals a slip; a curve below ideal signals ahead-of-schedule.
4. **Analyze velocity trends** — Compare this sprint's velocity (points completed per day) to the last 3–5 sprints. Calculate a rolling average and variance. Flag if velocity is consistently below plan.
5. **Identify scope changes** — Note any tickets added or removed mid-sprint. Scope changes distort the burndown — track them separately and annotate the chart.
6. **Flag early warning signals** — If actual remaining points exceed ideal by more than 15% at any checkpoint, raise an alert to the Scrum Master and team. Common causes: blocked work, underestimated stories, capacity reduction.
7. **Forecast release burndown** — For release-level tracking, aggregate sprint velocities and project remaining scope onto a release burndown. Estimate completion date based on current velocity.

## Outputs

- Sprint burndown chart (actual vs. ideal) updated daily
- Velocity trend chart (rolling 5-sprint average)
- Scope change log with impact analysis
- Early warning alerts to Scrum Master and product owner
- Release forecast with estimated completion date

## Verification

- Pull a sprint with known completion data. Verify the remaining points at each day match the manually calculated totals.
- Add a mid-sprint scope change ticket; confirm it is flagged and annotated separately on the chart.
- Test the 15% early warning threshold — confirm an alert fires when the gap exceeds threshold.

## Tips

- Burndown only tracks remaining work — it does not directly show team utilization. Pair with a velocity chart to understand capacity.
- For teams with variable capacity (part-time, rotating members), normalize points to "available person-days" before comparing to ideal.
- A burndown curve that "jumps" (points added mid-sprint) should be distinguished visually from a curve that simply plateaus (work stalled). Use color coding.
- Commit to updating the chart at the same time each day — ideally right after the daily standup when the board is fresh.