---
name: pm-130-risk-response-planning
description: Develop response strategies for identified project risks. Tier 2 PM skill.
triggers:
  - "risk response"
  - "risk response planning"
  - "mitigation plan"
  - "contingency plan"
  - "pm-130"
steps:
  - Retrieve the risk register from the project (risk-log.md).
  - For each risk with score ≥ 4, define a response strategy.
  - Response strategies: Avoid, Transfer, Mitigate, Accept, Escalate.
  - Avoid: Eliminate the cause entirely.
  - Transfer: Shift impact to a third party (insurance, contracts, outsourcing).
  - Mitigate: Reduce probability and/or impact (preferred for most risks).
  - Accept: Acknowledge and document — use when risk is within tolerance and cost of mitigation > impact.
  - Escalate: Notify sponsor/stakeholders when risk exceeds organizational appetite.
  - For each response: assign owner, set trigger condition (when to activate), define action steps, and set deadline.
  - Create a risk response register as a section in risk-log.md or a separate risk-response-plan.md.
  - Validate responses with risk owners and the project sponsor.
verification:
  - All risks scored ≥ 4 have a defined response.
  - Each response has: owner, trigger, action steps, deadline.
  - Response plan is reviewed by the project sponsor.
pitfalls:
  - Do not default to "accept" — always explore avoid/transfer/mitigate first.
  - Avoid vague triggers like "if things go wrong" — use specific, measurable conditions.
  - Do not assign risk response owners who lack authority to act.
  - Contingency budget/time should be documented separately in the project plan.
examples:
  - "Avoid: Migrate to a second cloud vendor to eliminate vendor lock-in risk before contract renewal."
  - "Mitigate: Add a second data engineer to the team, reducing single-point-of-failure probability from High to Low."
  - "Transfer: Purchase project delay insurance covering contractor non-performance."
---
# Risk Response Planning — pm-130

## Response Strategy Selection Guide
| Strategy | When to Use | Example |
|---|---|---|
| **Avoid** | Risk is critical and alternative approaches exist | Cancel a high-risk subcontractor engagement |
| **Transfer** | Impact is high but outside your control | Use fixed-price contracts, insurance |
| **Mitigate** | Probability or impact can be reduced with effort | Add redundancy, increase testing, cross-train |
| **Accept** | Risk is within appetite and mitigation cost > impact | Accept minor schedule variance in low-criticality path |
| **Escalate** | Risk exceeds organizational risk appetite | Notify executive sponsor immediately |

## Trigger Examples
- "When velocity drops below 20 story points per sprint for 2 consecutive sprints"
- "When AWS EC2 uptime falls below 99.5% for any 24-hour period"
- "When actual cost variance exceeds 10% of phase budget"
