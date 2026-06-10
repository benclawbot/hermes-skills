---
name: pm-100-raci-matrix
description: Define and communicate accountability for all project activities using a RACI matrix (Responsible, Accountable, Consulted, Informed) (Tier 2 — governance artifact)
trigger: "When you need to clarify who does what before execution starts, or when roles are unclear causing confusion or duplication of effort"
when_to_use: |
  - Early in planning phase after WBS and activity list are defined
  - When project involves many teams, vendors, or external stakeholders
  - When organizational change or restructuring means existing roles are unclear
  - Before any project with multiple workstreams and shared deliverables
  - During new team formation to prevent accountability gaps
inputs:
  - Activity list (from pm-080)
  - WBS with responsible owners per work package
  - Organizational chart or list of project roles
  - Stakeholder register
  - Contract or procurement documents (for vendor accountability)
workflow:
  1. List all activities from the activity list in rows — use activity IDs that match the schedule for traceability.
  2. List all stakeholders/roles in columns — group by function (Business, IT, Finance, Vendors, Executives). Use role titles, not individual names where possible (easier to maintain as people change).
  3. Assign RACI per cell:
     - R (Responsible): Who does the work? There should be one primary R per activity (can have multiple for joint work, but flag it).
     - A (Accountable): Who owns the outcome? Exactly ONE A per activity — the buck stops here. Never the same as R (distinguish between doing and owning).
     - C (Consulted): Who provides input before the decision? Two-way communication. Required for activities with technical or business dependency.
     - I (Informed): Who needs to know the output? One-way communication after the activity. Do not over-populate — only genuine stakeholders.
  4. Review with each identified Accountable — confirm they accept ownership and understand the scope of their accountability.
  5. Validate for common issues:
     - No A assigned — accountability gap, escalate to sponsor
     - More than one A — conflict, determine who has final authority
     - All Is with no R — a black hole, identify who actually does the work
     - Every cell filled — over-engineered, simplify
  6. Publish the matrix — embed in project handbook, share in kickoff, reference in status reports.
  7. Update the RACI when scope changes or at phase boundaries — treat it as a living document during planning, lock after baseline.
output: |
  - RACI Matrix: rows = activities, columns = stakeholders/roles, cells = R/A/C/I
  - Role definitions document: brief description of each role's authority and responsibilities
  - Accountability summary: list of who is Accountable for what (one-page overview for executives)
  - RACI sign-off: acknowledged by all As
tips: |
  - One A per activity is a non-negotiable rule — if you find two potential As, escalate to the project sponsor for a decision. Divided accountability is no accountability.
  - The "R and A cannot be the same person" rule exists to create a check-and-balance — the accountable person does not do the work, they own the outcome and verify it.
  - Do not create a RACI for 200 activities — group into work packages or phases. Detailed RACI for major deliverables only.
  - Avoid using individual names in the RACI during planning — use role titles. Plug in names at execution when team is confirmed.
  - If a vendor is involved, map them to the RACI explicitly — their contract should reflect what the RACI says they are A for.
---

# pm-100-raci-matrix

Define and communicate accountability for all project activities using a RACI matrix (Responsible, Accountable, Consulted, Informed).

## When to Use

- Early in planning phase after WBS and activity list are defined
- When project involves many teams, vendors, or external stakeholders
- When organizational change or restructuring means existing roles are unclear
- Before any project with multiple workstreams and shared deliverables
- During new team formation to prevent accountability gaps

## Inputs

- Activity list (from pm-080)
- WBS with responsible owners per work package
- Organizational chart or list of project roles
- Stakeholder register
- Contract or procurement documents (for vendor accountability)

## Workflow

1. List all activities from the activity list in rows — use activity IDs that match the schedule for traceability.
2. List all stakeholders/roles in columns — group by function (Business, IT, Finance, Vendors, Executives). Use role titles, not individual names where possible (easier to maintain as people change).
3. Assign RACI per cell:
   - R (Responsible): Who does the work? There should be one primary R per activity (can have multiple for joint work, but flag it).
   - A (Accountable): Who owns the outcome? Exactly ONE A per activity — the buck stops here. Never the same as R (distinguish between doing and owning).
   - C (Consulted): Who provides input before the decision? Two-way communication. Required for activities with technical or business dependency.
   - I (Informed): Who needs to know the output? One-way communication after the activity. Do not over-populate — only genuine stakeholders.
4. Review with each identified Accountable — confirm they accept ownership and understand the scope of their accountability.
5. Validate for common issues:
   - No A assigned — accountability gap, escalate to sponsor
   - More than one A — conflict, determine who has final authority
   - All Is with no R — a black hole, identify who actually does the work
   - Every cell filled — over-engineered, simplify
6. Publish the matrix — embed in project handbook, share in kickoff, reference in status reports.
7. Update the RACI when scope changes or at phase boundaries — treat it as a living document during planning, lock after baseline.

## Output

- RACI Matrix: rows = activities, columns = stakeholders/roles, cells = R/A/C/I
- Role definitions document: brief description of each role's authority and responsibilities
- Accountability summary: list of who is Accountable for what (one-page overview for executives)
- RACI sign-off: acknowledged by all As

## Tips

- One A per activity is a non-negotiable rule — if you find two potential As, escalate to the project sponsor for a decision. Divided accountability is no accountability.
- The "R and A cannot be the same person" rule exists to create a check-and-balance — the accountable person does not do the work, they own the outcome and verify it.
- Do not create a RACI for 200 activities — group into work packages or phases. Detailed RACI for major deliverables only.
- Avoid using individual names in the RACI during planning — use role titles. Plug in names at execution when team is confirmed.
- If a vendor is involved, map them to the RACI explicitly — their contract should reflect what the RACI says they are A for.