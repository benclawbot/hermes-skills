---
name: pm-160-scope-change-control
description: Control and document changes to project scope using a formal change request process. Tier 2 PM skill.
triggers:
  - "change control"
  - "scope change"
  - "change request"
  - "change management"
  - "CR"
  - "pm-160"
steps:
  - Define a Change Request (CR) threshold: What requires formal CR vs. informal note?
  - Any stakeholder can submit a CR, but the PM triages and validates it.
  - CR must include: Requestor, date, description of change, justification/rationale, impact assessment (schedule, cost, resources, quality, risk).
  - Impact assessment must quantify effects: +N days, +$N, +N resources, risk delta.
  - CR Review Board (CRB) or designated approver reviews CRs above the fast-track threshold.
  - Three outcomes: Approve, Reject (with rationale), Defer (backlog for future phase).
  - Upon approval: update project plan, WBS, schedule, budget, risk register, and communicate to all stakeholders.
  - Maintain a Change Log (change-log.md) tracking all CRs: ID, date, description, impact, decision, status.
  - Fast-track CRs (minor scope adjustments): PM approves directly if impact is below threshold and within approved contingency.
  - Full CRs: Require sponsor or CRB approval.
verification:
  - Change log exists and records all CRs (approved, rejected, deferred).
  - Every approved CR has a corresponding update to the project plan.
  - No work begins on a CR until it is formally approved.
pitfalls:
  - Do not approve CRs without an impact assessment — "scope creep" happens one undocumented change at a time.
  - Scope changes that affect quality must be reviewed by the QA lead.
  - Rejected CRs must be communicated to the requestor with clear rationale.
  - Emergency CRs (out-of-cycle) require post-hoc approval and documentation within 24 hours.
examples:
  - "CR-042: Add third-party SSO integration — impact: +5 days, +$12K license cost, no schedule slip if approved by Day 10."
  - "CR-043: Remove reporting module from Phase 1 — impact: -3 days, -$8K, reduces risk on data pipeline delivery."
---
# Scope Change Control — pm-160

## Change Request Template
```
## CR-{Number}: {Short Title}
- **Date**: YYYY-MM-DD
- **Requestor**: Name / Role
- **Priority**: Low / Medium / High / Critical
- **Description**: [What exactly is changing?]
- **Justification**: [Why is this change needed?]
- **Impact Assessment**:
  - Schedule: ±N days
  - Cost: ±$N
  - Resources: ±N FTE
  - Quality: [Effect on quality objectives]
  - Risk: [New risks introduced or existing risks reduced]
- **Alternatives Considered**: [What else was evaluated?]
- **Decision**: Approve / Reject / Defer
- **Approved By**: Name / Role / Date
```

## CR Prioritization
| Priority | Trigger | Approval Authority |
|---|---|---|
| **Critical** | Threatens project viability, safety, or compliance | Sponsor + PM immediately |
| **High** | Significant impact on primary deliverables | Sponsor |
| **Medium** | Moderate impact, within contingency | PM + CRB |
| **Low** | Minor scope adjustment, minimal impact | PM (fast-track) |

## Scope Creep vs. Legitimate Change
| Scope Creep (Reject) | Legitimate Change (Evaluate) |
|---|---|
| Undocumented, informal request | Formal CR with impact assessment |
| "We'll just add this quickly" | Quantified cost/schedule impact |
| No stakeholder sign-off | Sponsor-approved |
| Affects quality without acknowledgment | Quality impact explicitly assessed |
