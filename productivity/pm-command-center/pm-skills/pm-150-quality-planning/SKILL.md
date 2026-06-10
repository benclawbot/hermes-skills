---
name: pm-150-quality-planning
description: Define quality objectives, standards, and acceptance criteria for the project deliverable. Tier 2 PM skill.
triggers:
  - "quality plan"
  - "quality standards"
  - "acceptance criteria"
  - "quality assurance"
  - "pm-150"
steps:
  - Identify the quality standards relevant to the project domain (ISO 9001, GDPR, HIPAA, SOC2, industry-specific standards).
  - Define quality objectives: What does "done" mean? What level of defect rate is acceptable? What performance thresholds must be met?
  - Define acceptance criteria for each major deliverable (use SMART criteria: Specific, Measurable, Achievable, Relevant, Time-bound).
  - Plan quality assurance (QA) activities: code reviews, testing phases, peer inspections, compliance audits.
  - Assign quality roles and responsibilities (QA lead, testers, auditors).
  - Document in a quality-plan.md file with: Objectives | Standards | Acceptance Criteria | QA Activities | Schedule | Owner.
  - Integrate QA milestones into the project schedule.
  - Validate quality plan with the project sponsor and product owner.
verification:
  - Quality objectives are documented and measurable.
  - Acceptance criteria exist for all major deliverables.
  - QA activities are scheduled and assigned in the project plan.
pitfalls:
  - Do not define quality as "no bugs" — set realistic, domain-appropriate thresholds.
  - Acceptance criteria must be agreed upon before work begins, not after.
  - Quality gates must be enforced — a deliverable that fails quality review does not proceed.
  - Separate quality assurance (process) from quality control (product).
examples:
  - "API endpoints must respond within 200ms at P95 under 1000 concurrent users."
  - "Data pipeline must process 1M records with <0.01% error rate per run."
  - "All user-facing strings must be localized for EN, ES, FR, DE before release."
---
# Quality Planning — pm-150

## Quality Framework
1. **Quality Planning** — Define what quality means and how it will be measured.
2. **Quality Assurance (QA)** — Process adherence; are we building it the right way?
3. **Quality Control (QC)** — Product validation; did we build the right thing?

## Quality Metrics Examples
| Domain | Metric | Target |
|---|---|---|
| Software | Test coverage | ≥ 80% |
| Software | Critical bugs at release | 0 |
| Data | Record accuracy | ≥ 99.5% |
| Operations | System uptime | ≥ 99.9% |
| Security | Vulnerability critical findings | 0 at release |
| UX | Task completion rate | ≥ 90% |

## Acceptance Criteria Template
- **Given** [precondition]
- **When** [action performed]
- **Then** [expected outcome — measurable]

## Defect Severity Levels
- **Critical**: System unusable, data loss, security breach
- **High**: Major feature broken, workaround required
- **Medium**: Feature partially works, minor workaround
- **Low**: Cosmetic, minor inconvenience
