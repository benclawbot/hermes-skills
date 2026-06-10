---
name: pm-330-quality-assurance-deliverables
description: Plan, execute, and validate quality assurance activities to ensure project deliverables meet defined standards. Tier 3 PM skill.
triggers:
  - "quality assurance"
  - "QA"
  - "deliverable review"
  - "quality control"
  - "pm-330"
steps:
  - Review the Quality Management Plan (from pm-150) to confirm quality objectives, standards, and acceptance criteria for all deliverables.
  - For each major deliverable, define the QA approach: inspection, testing, review, audit, or demonstration.
  - Identify QA resources and assign QA owners for each deliverable.
  - Establish QA entry criteria — what must be true before QA begins (e.g., code complete, documentation drafted).
  - Conduct peer reviews or walkthroughs for all documentation deliverables.
  - Execute functional testing, integration testing, performance testing, or user acceptance testing (UAC) as appropriate.
  - Document all test cases, test results, and defects in the QA tracking system.
  - Conduct a defect triage session — classify defects as Critical, Major, Minor, or Cosmetic.
  - Define and communicate the defect resolution SLA by severity level.
  - Re-test resolved defects and confirm closure.
  - Produce a QA Summary Report at the end of each phase or major milestone: test coverage, pass/fail rates, open defects, residual risk.
  - Obtain formal sign-off from the QA lead and project sponsor before declaring a deliverable "Accepted."
  - Output: QA Plan per deliverable, Test Results, Defect Log, QA Summary Report, and signed Acceptance Sign-off.
verification:
  - Every major deliverable has a defined QA approach documented before work begins.
  - All QA activities are executed as planned and results are documented.
  - Critical and Major defects are resolved before deliverable acceptance.
  - Formal sign-off is obtained and filed for each accepted deliverable.
  - QA Summary Report is produced and shared with stakeholders.
pitfalls:
  - Do not skip QA on low-priority deliverables — a deliverable without QA验收 is a risk.
  - Do not accept deliverables with open Critical or Major defects.
  - Do not conduct QA before entry criteria are met — you will get misleading results and wasted effort.
  - Do not treat all defects equally — establish and enforce severity-based SLAs.
examples:
  - "QA for Deliverable D4 (reporting module): 45 test cases executed, 2 Major defects found and resolved, 0 Critical defects — QA Lead sign-off obtained."
  - "UAT for Phase 2: 8 users tested 12 scenarios; 1 Critical defect (data export fails on Safari) — blocked acceptance until fixed and re-tested."
  - "QA Summary: Test coverage 94%; 18 defects found, 16 resolved, 2 Minor open (cosmetic); residual risk: Low."
---
# Quality Assurance of Deliverables — pm-330

## When to Use
Run this skill during the planning phase to establish QA approach per deliverable, and during execution to execute QA activities and validate deliverables before acceptance.

## QA Approach by Deliverable Type
| Deliverable Type | QA Method | QA Owner |
|---|---|---|
| Software / Code | Unit testing, integration testing, performance testing, security scan | QA Engineer |
| Documentation | Peer review, editorial check, stakeholder review | Tech Writer / PM |
| Infrastructure | Deployment validation, smoke test, disaster recovery test | DevOps / Engineer |
| User-facing Product | User acceptance testing (UAT), demo | Product Owner / Client |
| Data / Reports | Data validation, reconciliation, accuracy check | Data Analyst |

## Defect Severity Classification
| Severity | Definition | Resolution SLA | Example |
|---|---|---|---|
| **Critical** | System unusable; data loss; security breach | Fix within 24 hours | Application crashes on login |
| **Major** | Core feature broken; workaround exists | Fix within 3 business days | Export function fails for 10% of users |
| **Minor** | Feature degraded; no workaround needed | Fix within 2 weeks | UI alignment issue on mobile |
| **Cosmetic** | Visual only; no functional impact | Fix in next release | Typo in label text |

## QA Sign-off Template
\`\`\`markdown
# Deliverable Acceptance — QA Sign-off

**Project:** [Name]  
**Deliverable:** [ID and description]  
**Phase/Milestone:** [Phase X / M#]  
**QA Lead:** [Name]  
**Date of QA Completion:** YYYY-MM-DD  

## QA Summary
| Metric | Value |
|---|---|
| Test Cases Executed | N |
| Passed | N |
| Failed | N |
| Test Coverage | X% |
| Critical Defects Open | 0 |
| Major Defects Open | 0 |

## Defect Status
| Defect ID | Description | Severity | Status | Resolved Date |
|---|---|---|---|---|
| | | | | |

## Sign-off
**QA Lead:** _______________ Date: _______  
**Project Manager:** _______________ Date: _______  
**Sponsor (if required):** _______________ Date: _______  

**Status:** ☐ Accepted — All acceptance criteria met  
**Status:** ☐ Conditionally Accepted — See outstanding items below  
**Status:** ☐ Rejected — Critical/Major defects block acceptance  

**Outstanding Items:** [List any open Minor/Cosmetic defects accepted with known issue]
\`\`\`
