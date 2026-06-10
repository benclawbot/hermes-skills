---
name: pm-070-wbs-development
description: Decompose project scope into the Work Breakdown Structure — deliverables, sub-deliverables, and work packages (Tier 2 — core planning artifact)
trigger: "When you need to turn scope into a hierarchical decomposition before activity sequencing or scheduling"
when_to_use: |
  - After requirements are baselined and scope is defined
  - Before activity definition and estimation
  - When organizing work for phase-gate or stage-gate project frameworks
  - As input to scope verification and change control
inputs:
  - approved_scope_statement
  - requirements_register
  - project_charter
  - organizational_breakdown_structure (OBS) if applicable
  - known_constraints (budget, resources, deadlines)
workflow:
  1. Start with the project objective — the top-level deliverable that defines project completion. Write it as a noun phrase (e.g., "Operational CRM system", "Certified training program").
  2. Decompose using the 100% rule — every deliverable in the WBS must represent 100% of the work at that level. Include work AND dependencies (testing, documentation, training).
  3. Choose decomposition approach:
     - Deliverable-based (most common) — break by end product or result
     - Phase-based — break by project lifecycle (Initiate, Plan, Execute, Close)
     - Organizational — break by department responsible
  4. Build levels iteratively — aim for 3-5 children per parent node. Go deeper only where complexity or control requires it. Work packages should be 8-80 hours of effort (adjust for project scale).
  5. Assign WBS codes (e.g., 1.0, 1.1, 1.1.1) — these become the cost account identifiers in your budget.
  6. Create work package descriptions — each work package needs: description, responsible owner, dependencies, quality criteria, acceptance sign-off.
  7. Cross-check against requirements register — each requirement should map to at least one WBS element. Use the traceability matrix.
  8. Validate with key stakeholders — particularly those who will be responsible for delivering each branch.
output: |
  - WBS Dictionary: hierarchical tree with WBS codes, work package names, descriptions, owners, effort estimates, dependencies
  - Scope baseline: the approved WBS with effort/duration/cost estimates rolled up
  - Requirements traceability matrix: maps each requirement to its WBS element(s)
  - Control account plan: assigns cost account codes to responsible teams
tips: |
  - Resist decomposing too early — wait until requirements are stable enough. Premature breakdown creates rework.
  - The 100% rule is the most violated principle — always ask "what else is missing at this level?"
  - Keep the WBS as a deliverable-oriented hierarchy, not a task list. Tasks live at the activity level (pm-080), WBS lives at the deliverable level.
  - If a work package is bigger than 40 hours of work for one person, it probably needs sub-deliverables.
  - Use WBS as your change control anchor — anything added to scope must map to a WBS element.
---

# pm-070-wbs-development

Decompose project scope into the Work Breakdown Structure — deliverables, sub-deliverables, and work packages.

## When to Use

- After requirements are baselined and scope is defined
- Before activity definition and estimation
- When organizing work for phase-gate or stage-gate project frameworks
- As input to scope verification and change control

## Inputs

- approved_scope_statement
- requirements_register
- project_charter
- organizational_breakdown_structure (OBS) if applicable
- known_constraints (budget, resources, deadlines)

## Workflow

1. Start with the project objective — the top-level deliverable that defines project completion. Write it as a noun phrase (e.g., "Operational CRM system", "Certified training program").
2. Decompose using the 100% rule — every deliverable in the WBS must represent 100% of the work at that level. Include work AND dependencies (testing, documentation, training).
3. Choose decomposition approach:
   - Deliverable-based (most common) — break by end product or result
   - Phase-based — break by project lifecycle (Initiate, Plan, Execute, Close)
   - Organizational — break by department responsible
4. Build levels iteratively — aim for 3-5 children per parent node. Go deeper only where complexity or control requires it. Work packages should be 8-80 hours of effort (adjust for project scale).
5. Assign WBS codes (e.g., 1.0, 1.1, 1.1.1) — these become the cost account identifiers in your budget.
6. Create work package descriptions — each work package needs: description, responsible owner, dependencies, quality criteria, acceptance sign-off.
7. Cross-check against requirements register — each requirement should map to at least one WBS element. Use the traceability matrix.
8. Validate with key stakeholders — particularly those who will be responsible for delivering each branch.

## Output

- WBS Dictionary: hierarchical tree with WBS codes, work package names, descriptions, owners, effort estimates, dependencies
- Scope baseline: the approved WBS with effort/duration/cost estimates rolled up
- Requirements traceability matrix: maps each requirement to its WBS element(s)
- Control account plan: assigns cost account codes to responsible teams

## Tips

- Resist decomposing too early — wait until requirements are stable enough. Premature breakdown creates rework.
- The 100% rule is the most violated principle — always ask "what else is missing at this level?"
- Keep the WBS as a deliverable-oriented hierarchy, not a task list. Tasks live at the activity level (pm-080), WBS lives at the deliverable level.
- If a work package is bigger than 40 hours of work for one person, it probably needs sub-deliverables.
- Use WBS as your change control anchor — anything added to scope must map to a WBS element.