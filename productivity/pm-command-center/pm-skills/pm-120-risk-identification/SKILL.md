---
name: pm-120-risk-identification
description: Identify and document project risks in a risk register. Tier 1 PM skill.
triggers:
  - "risk register"
  - "identify risks"
  - "risk identification"
  - "risk log"
  - "pm-120"
steps:
  - Create or open the risk register (risk-log.md, risk-register.md, or project-risk-log.md in the project root).
  - For each risk, document: ID, description, category, probability, impact, risk score (P × I), owner, mitigation strategy, status, and date identified.
  - Risk categories: Technical, External, Organizational, Scope, Schedule, Cost, Quality, Resource, Stakeholder.
  - Use a table format for the register.
  - Review and validate each risk entry with the project team.
  - Set review frequency (weekly/monthly) and escalation thresholds.
  - Output: Updated risk register with all identified risks.
verification:
  - Risk register exists and contains at least one risk entry.
  - Each entry has: ID, description, probability, impact, score, owner, mitigation, status.
  - Register is reviewed and approved by the project manager.
pitfalls:
  - Do not identify risks that are already issues — focus on future/uncertain events.
  - Do not leave probability or impact blank — if unknown, mark as "TBD" and resolve within 48 hours.
  - Avoid generic risks like "key person risk" — make them specific (e.g., "Data engineer resignation before data pipeline completion").
  - Risk score alone does not determine priority — also consider urgency and proximity.
examples:
  - "New regulatory requirement could delay Q3 launch (P=Medium, I=High, Score=High)"
  - "Cloud infrastructure costs may exceed budget by 20% if data volume grows as projected"
---
# Risk Identification — pm-120

## When to Use
Run this skill when starting a new project, at project kickoff, or whenever the project manager requests a risk identification session.

## Output
A completed or updated **Risk Register** saved as `risk-log.md` in the project directory.

## Risk Score Matrix
| Probability | Low (1) | Medium (2) | High (3) |
|---|---|---|---|
| **Low Impact** | 1 | 2 | 3 |
| **Medium Impact** | 2 | 4 | 6 |
| **High Impact** | 3 | 6 | 9 |

Score 1–3: Monitor | Score 4–6: Escalate | Score 7–9: Immediate action required
