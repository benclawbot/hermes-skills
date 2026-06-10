---
name: pm-290-status-reporting
description: Produce and distribute regular project status reports to stakeholders. Tier 1 PM skill.
triggers:
  - "status report"
  - "weekly status"
  - "project update"
  - "progress report"
  - "pm-290"
steps:
  - Determine the reporting cadence (daily, weekly, bi-weekly, or monthly) agreed with stakeholders.
  - Collect data from all workstream leads: tasks completed, tasks in progress, tasks blocked, upcoming milestones.
  - Calculate key metrics: percent complete against plan, earned value if applicable, budget spent vs. forecast, schedule variance.
  - Identify and quantify issues (problems currently impacting delivery) and risks (potential future impacts).
  - Summarize decisions needed from steering committee or stakeholders.
  - Draft the status report using the standard template: Executive Summary, RAG Status, Milestone Tracker, Budget Status, Risks & Issues, Decisions Needed, Next Period's Priorities.
  - Review report for accuracy with team leads before distribution.
  - Distribute report to all stakeholders per the communication plan (email, project portal, shared workspace).
  - Archive all previous reports with version number and date.
  - Capture stakeholder feedback and incorporate into next report.
  - Output: Completed Status Report distributed to all stakeholders.
verification:
  - Report is produced on the agreed schedule and distributed within the agreed window.
  - Report uses the standard template with all sections complete.
  - Report accurately reflects current project state — verified with team leads.
  - Report is filed in the project repository under version-controlled naming (e.g., status-report-YYYY-MM-DD.md).
pitfalls:
  - Do not omit blockers or bad news — stakeholders need accurate information to make decisions.
  - Do not bury key decisions in the middle of the report — put them in a clearly labeled section near the top.
  - Avoid over-formatting — a clean, readable report beats a colorful but confusing one.
  - Do not let the report become the project — spend time doing the work, not just writing about it.
examples:
  - "Weekly status report: Project GREEN overall; Milestone M3 (design approval) at risk — 3-day slip due to late vendor deliverable; budget at 42% spent vs. 45% planned."
  - "Monthly status: Project AMBER; Q3 delivery milestone at risk due to resource availability; requesting decision on contractor extension by Friday."
---
# Status Reporting — pm-290

## When to Use
Run this skill at the agreed reporting cadence throughout the project. Trigger ad-hoc reports when a major issue, scope change, or escalation occurs.

## RAG Status Definitions
| RAG | Meaning | Criteria |
|---|---|---|
| 🟢 Green | On track | Budget, schedule, and scope within 10% of plan; no major risks materializing |
| 🟡 Amber | At risk | Budget or schedule variance 10–20%; significant risks active; recovery plan in place |
| 🔴 Red | Off track | Budget or schedule variance >20%; critical issues unblocked; executive intervention needed |

## Status Report Template (Markdown)
\`\`\`markdown
# Project Status Report — [Project Name]
**Report Date:** YYYY-MM-DD | **Reporting Period:** Start – End | **Prepared by:** PM Name

## RAG Status
| Domain | Status | Notes |
|---|---|---|
| Overall | 🟢 Green | |
| Schedule | 🟢 Green | |
| Budget | 🟡 Amber | |
| Scope | 🟢 Green | |

## Executive Summary
[2–3 sentence overview of project health and key events this period.]

## Milestone Tracker
| Milestone | Baseline | Forecast | Status | Notes |
|---|---|---|---|---|
| M1: Kickoff | Date | Date | 🟢 | |
| M2: Design Complete | Date | Date +3 days | 🟡 | Vendor delay |

## Budget Status
| Item | Budget | Actual | Forecast | Variance |
|---|---|---|---|---|
| Labor | $X | $Y | $Z | +/-$ |

## Risks & Issues
**Open Issues:**
1. [Issue description] — Owner: [Name] — Escalation: [Date/Action]
2. ...

**Active Risks:**
1. [Risk description] — Likelihood: [H/M/L] — Impact: [H/M/L] — Mitigation: [Action]

## Decisions Needed
1. [Decision description] — Needed by: [Date] — Owner: [Name]

## Next Period's Priorities
1. ...
2. ...
\`\`\`