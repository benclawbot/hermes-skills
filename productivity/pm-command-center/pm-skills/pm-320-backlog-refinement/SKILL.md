---
name: pm-320-backlog-refinement
description: Review, prioritize, and detail the project backlog to ensure the right items are ready for execution. Tier 1 PM skill.
triggers:
  - "backlog refinement"
  - "backlog grooming"
  - "prioritize backlog"
  - "product backlog"
  - "pm-320"
steps:
  - Schedule a recurring Backlog Refinement session (weekly or bi-weekly, 60–90 minutes).
  - Review the entire backlog — existing items and newly submitted requests.
  - For each backlog item, confirm: clear title, detailed description, acceptance criteria, estimated effort (story points or hours), business value, and dependencies.
  - Remove duplicate, obsolete, or out-of-scope items — document rationale for removal.
  - Break down large items (epics) into smaller, actionable items (user stories or tasks) that can be completed within one sprint/iteration.
  - Re-prioritize items based on: business value, strategic alignment, dependencies, risk, and effort — apply MoSCoW or similar framework.
  - Confirm that the top N items (where N = sprint capacity) are fully ready: no ambiguity, all dependencies resolved, acceptance criteria agreed.
  - Update item ordering in the backlog tracker (Linear, Jira, ProductBoard, etc.).
  - Communicate the refined backlog to all stakeholders, especially team leads and the steering committee.
  - Output: Refined and prioritized backlog with all top items fully ready for sprint/phase planning.
verification:
  - Backlog refinement session occurred on the agreed schedule.
  - Top priority items have: clear description, acceptance criteria, estimate, and owner assigned.
  - No item in the top of the backlog is blocked by an unresolved dependency.
  - Backlog is re-ordered in the tracking tool and communicated to the team.
  - Items removed from scope are documented and approved.
pitfalls:
  - Do not let the backlog grow without culling — an unmaintained backlog becomes noise.
  - Do not refine items that are not yet ready to be refined — wait for stakeholder input on ambiguous items.
  - Do not prioritize purely by effort (lowest effort first) — value and strategic alignment matter more.
  - Avoid committing to the entire backlog — only commit to items that are fully ready.
examples:
  - "Refined backlog: Top 10 items for Sprint 7 — all have acceptance criteria, estimates, and confirmed team capacity."
  - "Broke Epic E5 (reporting module) into 5 user stories; removed 2 duplicate items; re-prioritized E5.3 from P2 to P1 based on client feedback."
  - "Backlog grooming: 3 items blocked by legal sign-off — escalated to project sponsor to unblock before next sprint."
---
# Backlog Refinement — pm-320

## When to Use
Run this skill on a recurring cadence (weekly or bi-weekly) throughout the project. Trigger an ad-hoc session when a major scope change occurs or when the team consistently cannot execute planned items due to lack of readiness.

## MoSCoW Prioritization Framework
| Priority | Meaning | Target % of Items |
|---|---|---|
| **Must Have** | Critical path; project fails without this | 60% |
| **Should Have** | Important but not critical; project succeeds without | 20% |
| **Could Have** | Desirable; increases satisfaction | 15% |
| **Won't Have (This Time)** | Explicitly deprioritized; document rationale | 5% |

## Definition of Ready (for backlog items)
A backlog item is **Ready** for sprint/phase planning when:
- [ ] Clear title and description
- [ ] Acceptance criteria defined (minimum 3 criteria)
- [ ] Estimated (story points or hours)
- [ ] Owner assigned
- [ ] Dependencies identified and resolved
- [ ] Tested/verifiable outcome defined

## Backlog Item Template
\`\`\`markdown
## [Item ID] — [Short Title]

**Type:** Feature / Bug Fix / Technical Debt / Research  
**Priority:** Must / Should / Could / Won't  
**Estimated Effort:** X story points / X hours  
**Owner:** [Name]  
**Sprint/Phase:** [Target]  

### Description
[What this item delivers and why it matters.]

### Acceptance Criteria
1. [Criterion 1 — observable, testable]
2. [Criterion 2]
3. [Criterion 3]

### Dependencies
- [Dependency 1 and its status]
- [Dependency 2 and its status]

### Notes
[Any additional context, constraints, or decisions.]
\`\`\`
