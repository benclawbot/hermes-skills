---
name: pm-090-schedule-development
description: Build the project schedule — estimate durations, assign resources, identify critical path, and produce Gantt charts (Tier 2 — core planning artifact)
trigger: "When activities are sequenced and you need to convert the network diagram into a time-bound schedule with resource assignments"
when_to_use: |
  - After activity sequencing (pm-080) is complete
  - When you need to validate the project end date against stakeholder expectations
  - Before presenting a baseline schedule for stakeholder sign-off
  - When resource conflicts or over-allocation need to be resolved
inputs:
  - Activity list with dependencies
  - Project network diagram with ES/EF/LS/LF values
  - Resource requirements per activity
  - Resource availability calendars
  - Historical data (similar past project durations)
  - Defined milestones and constraints
workflow:
  1. Estimate durations per activity — use three-point estimation (Optimistic/Most Likely/Pessimistic) or bottom-up from work packages. Adjust for resource skill level and availability.
  2. Calculate total float for each activity: LS - ES (or LF - EF). Critical path activities have zero float.
  3. Assign resources — match activities to responsible individuals or roles. Check resource calendar availability against activity demands. If demand exceeds availability, flag as over-allocated.
  4. Resolve over-allocations using:
     - Resource leveling (extend duration to fit available capacity)
     - Lead/lag adjustments (shift non-critical activities to smooth peaks)
     - Fast-tracking (overlap activities that were sequential — increases risk)
     - Crashing (add resources to critical path activities — increases cost)
  5. Build the Gantt chart — show activities as bars over time. Include: start/end dates, duration, % complete, dependencies (FT/SS/FF), milestones as diamonds.
  6. Identify schedule contingency — add buffer to critical path based on risk assessment. Common approaches: 10-20% buffer, or PERT-based contingency from three-point estimation variance.
  7. Validate against constraints — confirm final date meets any hard deadlines, contractual dates, or market windows.
  8. Baseline the schedule — lock the approved schedule as the performance measurement baseline (PMB). All future variance is measured against this.
  9. Publish schedule with roles clearly assigned — responsible owner per activity, escalation path for delays.
output: |
  - Detailed project schedule (Gantt view): activities, start/end, duration, % complete, resource, dependencies, milestones
  - Schedule baseline document: approved schedule with dates, signed off by sponsor
  - Critical path report: list of critical activities with float = 0
  - Resource loading chart: allocated hours per resource per time period
  - Over-allocation report and resolution actions taken
  - Schedule contingency: buffer time or cost reserves
tips: |
  - Duration estimation is the highest uncertainty input — always use ranges, not point estimates, especially early in planning.
  - Resource leveling can extend the project end date — agree with stakeholders on acceptable trade-offs before you start.
  - Fast-tracking is the most common cause of rework and quality issues — document the agreed risk/benefit decision.
  - Build schedule margin into milestones, not just the final date. A milestone every 2-4 weeks keeps the schedule visible and controllable.
  - Re-baseline only through change control — ad-hoc schedule updates break the performance measurement baseline.
---

# pm-090-schedule-development

Build the project schedule — estimate durations, assign resources, identify critical path, and produce Gantt charts.

## When to Use

- After activity sequencing (pm-080) is complete
- When you need to validate the project end date against stakeholder expectations
- Before presenting a baseline schedule for stakeholder sign-off
- When resource conflicts or over-allocation need to be resolved

## Inputs

- Activity list with dependencies
- Project network diagram with ES/EF/LS/LF values
- Resource requirements per activity
- Resource availability calendars
- Historical data (similar past project durations)
- Defined milestones and constraints

## Workflow

1. Estimate durations per activity — use three-point estimation (Optimistic/Most Likely/Pessimistic) or bottom-up from work packages. Adjust for resource skill level and availability.
2. Calculate total float for each activity: LS - ES (or LF - EF). Critical path activities have zero float.
3. Assign resources — match activities to responsible individuals or roles. Check resource calendar availability against activity demands. If demand exceeds availability, flag as over-allocated.
4. Resolve over-allocations using:
   - Resource leveling (extend duration to fit available capacity)
   - Lead/lag adjustments (shift non-critical activities to smooth peaks)
   - Fast-tracking (overlap activities that were sequential — increases risk)
   - Crashing (add resources to critical path activities — increases cost)
5. Build the Gantt chart — show activities as bars over time. Include: start/end dates, duration, % complete, dependencies (FT/SS/FF), milestones as diamonds.
6. Identify schedule contingency — add buffer to critical path based on risk assessment. Common approaches: 10-20% buffer, or PERT-based contingency from three-point estimation variance.
7. Validate against constraints — confirm final date meets any hard deadlines, contractual dates, or market windows.
8. Baseline the schedule — lock the approved schedule as the performance measurement baseline (PMB). All future variance is measured against this.
9. Publish schedule with roles clearly assigned — responsible owner per activity, escalation path for delays.

## Output

- Detailed project schedule (Gantt view): activities, start/end, duration, % complete, resource, dependencies, milestones
- Schedule baseline document: approved schedule with dates, signed off by sponsor
- Critical path report: list of critical activities with float = 0
- Resource loading chart: allocated hours per resource per time period
- Over-allocation report and resolution actions taken
- Schedule contingency: buffer time or cost reserves

## Tips

- Duration estimation is the highest uncertainty input — always use ranges, not point estimates, especially early in planning.
- Resource leveling can extend the project end date — agree with stakeholders on acceptable trade-offs before you start.
- Fast-tracking is the most common cause of rework and quality issues — document the agreed risk/benefit decision.
- Build schedule margin into milestones, not just the final date. A milestone every 2-4 weeks keeps the schedule visible and controllable.
- Re-baseline only through change control — ad-hoc schedule updates break the performance measurement baseline.