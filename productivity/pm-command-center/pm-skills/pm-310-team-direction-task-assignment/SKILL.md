---
name: pm-310-team-direction-task-assignment
description: Assign project tasks to team members with clear direction, accountability, and deadline. Tier 3 PM skill.
triggers:
  - "assign task"
  - "task assignment"
  - "team direction"
  - "work allocation"
  - "pm-310"
steps:
  - Review the WBS and the current project schedule to identify all tasks that need to be assigned.
  - For each task, confirm: task description, dependencies (predecessors and successors), duration, start and end dates, and required skills/expertise.
  - Identify the responsible resource(s) for each task using the RACI matrix as a guide.
  - Conduct a workload check — confirm the resource has capacity during the task window without exceeding 100% allocation.
  - Hold a task assignment meeting (or individual 1:1) with each team member.
  - For each task, communicate clearly: what (deliverable), why (business context), how (process/method), when (deadline), and what success looks like (acceptance criteria).
  - Assign the task formally in the project tracking tool (Linear, Jira, Asana, etc.) or issue a written task directive.
  - Confirm the team member accepts the assignment and acknowledges the deadline.
  - Set up checkpoint dates for progress reviews on tasks longer than 3 days.
  - Track task status weekly; follow up immediately on any task that is not started by its planned start date.
  - Document any resource conflicts or overloaded resources and escalate to the project sponsor.
  - Output: Task assignments documented in project tracker with confirmed acceptance from all assignees.
verification:
  - Every WBS task has an assigned owner (individual or team).
  - All assignees have acknowledged their tasks and agreed to deadlines.
  - No resource is allocated above 100% during any time period.
  - All task assignments include clear acceptance criteria.
  - Task status is reviewed at each weekly status cycle.
pitfalls:
  - Do not assign tasks without confirming the resource has capacity — a task assigned is not a task done.
  - Do not change task scope mid-assignment without re-confirming the deadline with the resource.
  - Avoid vague assignments like "help with testing" — be specific: "Execute regression test suite by EOD Friday and report results."
  - Do not pile multiple high-priority tasks on one person simultaneously — sequence or redistribute.
examples:
  - "Assign M4.2 (database migration script) to DevOps engineer — deadline Friday 5 PM, 8 hours estimated, no dependencies — acceptance criteria: script tested in staging, documented in runbook."
  - "Redistribute M5.3 (API integration) from Engineer A (overloaded at 120%) to Engineer B (capacity available at 80%) — confirm both agree in writing."
  - "Task M6.1 blocked — third-party data feed not available — escalate to sponsor for vendor intervention."
---
# Team Direction & Task Assignment — pm-310

## When to Use
Run this skill whenever new tasks are created, when team composition changes, when tasks are blocked, or during resource conflicts. Conduct at project kickoff, at sprint/phase start, and weekly throughout execution.

## Task Assignment Briefing (minimum content per task)
| Field | Description |
|---|---|
| Task ID | WBS / Tracker ID |
| Task Name | Short, descriptive title |
| Owner | Individual team member |
| Assignee Acknowledge | Yes/No and date |
| Start Date | Planned start |
| End Date | Deadline |
| Estimated Hours | Effort estimate |
| Priority | High / Medium / Low |
| Dependencies | Predecessor tasks |
| Acceptance Criteria | What "done" looks like |
| Checkpoint | Progress review date |

## Workload Balancing Rules
1. No resource should exceed **100% allocation** in any given week.
2. High-priority tasks go to resources with the required skill AND available capacity.
3. When conflicts arise, escalate to the project sponsor — do not decide unilaterally to over-allocate.
4. Re-balance weekly as tasks complete and new tasks emerge.

## Escalation Protocol
| Situation | Action |
|---|---|
| Resource refuses assignment | Discuss with resource, document reason, escalate to line manager if unresolved |
| Resource overloaded | Redistribute or extend deadline; escalate if neither is possible |
| Task blocked > 3 days | Escalate to project sponsor with options |
| Critical path task at risk | Immediate escalation to sponsor and steering committee |
