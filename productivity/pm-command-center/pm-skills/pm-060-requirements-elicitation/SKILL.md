---
name: pm-060-requirements-elicitation
description: Elicit and document project requirements through interviews, workshops, JAD sessions, and observation (Tier 3 — specialized technique)
trigger: "When you need to gather, clarify, or validate requirements from stakeholders before scope is finalized"
when_to_use: |
  - Kickoff meeting or project initiation
  - Scope ambiguity or conflicting stakeholder expectations
  - Complex project with diverse user groups
  - Regulatory/compliance requirements that need formal documentation
  - Agile sprint planning where stories need acceptance criteria
inputs:
  - stakeholder_list (names, roles, contact info)
  - project_charter_or_statement_of_work
  - existing documentation (current processes, systems, constraints)
  - known_gaps_or_areas_of_uncertainty
workflow:
  1. Identify all stakeholder groups — map power/interest grid. Classify as primary (deciders), secondary (influencers), tertiary (consulted for specifics).
  2. Choose elicitation technique per stakeholder type:
     - One-on-one interviews for executives and singular decision-makers
     - Joint Application Development (JAD) workshops for cross-functional teams
     - Document analysis for regulatory/compliance constraints
     - Observation/job shadowing for operational user requirements
  3. Prepare session guides — open-ended questions first, then specifics. For interviews: why, what, how, constraints. For workshops: agenda, ground rules, parking lot for out-of-scope items.
  4. Conduct sessions — record in shared doc (Miro, Notion, Google Docs). Capture actual quotes vs. paraphrasing. Note unresolved items explicitly as TBD.
  5. Consolidate outputs into requirements register:
     - Unique ID per requirement
     - Source stakeholder
     - Requirement text (specific, measurable, testable)
     - Acceptance criteria
     - Priority (MoSCoW: Must/Should/Could/Won't)
     - Status (draft/confirmed/approved)
  6. Review and sign-off — circulate to all stakeholders, collect explicit approval or tracked changes.
  7. Baseline the requirements — once approved, lock version. All future changes go through change control.
output: |
  Requirements Register (spreadsheet or structured doc) with:
  - Requirement IDs, descriptions, criteria, sources, priorities, status
  - Traceability matrix linking requirements to project objectives
  - Approved requirements baseline document
  - List of open questions / TBD items with owners and due dates
tips: |
  - Never accept "we need a better system" as a requirement — drill down to specific functional needs with measurable outcomes.
  - In workshops, use round-robin to ensure quieter voices are heard; enforce time-boxing per topic.
  - If stakeholders conflict, document both positions and escalate to sponsor for decision — do NOT arbitrate alone.
  - Save all raw session notes separately from the cleaned requirements register.
  - Re-confirm requirements at sprint planning, not just at project start — business context shifts.
---

# pm-060-requirements-elicitation

Elicit and document project requirements through interviews, workshops, JAD sessions, and observation.

## When to Use

- Kickoff meeting or project initiation
- Scope ambiguity or conflicting stakeholder expectations
- Complex project with diverse user groups
- Regulatory/compliance requirements that need formal documentation
- Agile sprint planning where stories need acceptance criteria

## Inputs

- stakeholder_list (names, roles, contact info)
- project_charter_or_statement_of_work
- existing documentation (current processes, systems, constraints)
- known_gaps_or_areas_of_uncertainty

## Workflow

1. Identify all stakeholder groups — map power/interest grid. Classify as primary (deciders), secondary (influencers), tertiary (consulted for specifics).
2. Choose elicitation technique per stakeholder type:
   - One-on-one interviews for executives and singular decision-makers
   - Joint Application Development (JAD) workshops for cross-functional teams
   - Document analysis for regulatory/compliance constraints
   - Observation/job shadowing for operational user requirements
3. Prepare session guides — open-ended questions first, then specifics. For interviews: why, what, how, constraints. For workshops: agenda, ground rules, parking lot for out-of-scope items.
4. Conduct sessions — record in shared doc (Miro, Notion, Google Docs). Capture actual quotes vs. paraphrasing. Note unresolved items explicitly as TBD.
5. Consolidate outputs into requirements register:
   - Unique ID per requirement
   - Source stakeholder
   - Requirement text (specific, measurable, testable)
   - Acceptance criteria
   - Priority (MoSCoW: Must/Should/Could/Won't)
   - Status (draft/confirmed/approved)
6. Review and sign-off — circulate to all stakeholders, collect explicit approval or tracked changes.
7. Baseline the requirements — once approved, lock version. All future changes go through change control.

## Output

Requirements Register (spreadsheet or structured doc) with:
- Requirement IDs, descriptions, criteria, sources, priorities, status
- Traceability matrix linking requirements to project objectives
- Approved requirements baseline document
- List of open questions / TBD items with owners and due dates

## Tips

- Never accept "we need a better system" as a requirement — drill down to specific functional needs with measurable outcomes.
- In workshops, use round-robin to ensure quieter voices are heard; enforce time-boxing per topic.
- If stakeholders conflict, document both positions and escalate to sponsor for decision — do NOT arbitrate alone.
- Save all raw session notes separately from the cleaned requirements register.
- Re-confirm requirements at sprint planning, not just at project start — business context shifts.