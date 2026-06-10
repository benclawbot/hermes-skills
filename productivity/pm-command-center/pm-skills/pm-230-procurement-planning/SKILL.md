---
name: pm-230-procurement-planning
description: Plan and manage the procurement of goods, services, and resources needed for project delivery. Tier 3 PM skill.
triggers:
  - "procurement"
  - "vendor selection"
  - "procurement planning"
  - "contract management"
  - "pm-230"
steps:
  - Identify all items that need to be procured (goods, services, materials, software, contractors).
  - Classify each item: Make vs. Buy decision — build in-house, purchase off-the-shelf, or outsource to vendor.
  - For each procurement item, document: item description, quantity, estimated cost, lead time, delivery date needed, and responsible buyer.
  - Issue Request for Quote (RFQ), Invitation to Bid (ITB), or Request for Proposal (RFP) to vendors.
  - Evaluate vendor responses using pre-defined criteria (cost, quality, timeline, risk, past performance).
  - Conduct vendor risk assessment (financial stability, compliance, capacity, references).
  - Negotiate terms and conditions including payment schedule, SLAs, warranties, and intellectual property rights.
  - Issue Purchase Orders (PO) or Contracts and track acknowledgments.
  - Monitor delivery against milestones and flag delays proactively.
  - Maintain a procurement log/ tracker with vendor name, item, PO number, expected delivery, actual delivery, cost, and status.
  - Conduct a procurement post-mortem for major contracts.
  - Output: Completed Procurement Plan and updated Procurement Log.
verification:
  - Procurement plan covers all items identified in WBS that are marked "external."
  - All vendors are evaluated against written criteria and documented.
  - All contracts/POs are countersigned and filed.
  - Procurement log is current and reconciled with actuals.
pitfalls:
  - Do not start work before procurement is approved — always get a signed PO or contract first.
  - Avoid single-source procurement without documented justification and approval.
  - Do not accept terms without legal/compliance review for high-value or long-duration contracts.
  - Avoid scope creep in vendor contracts — lock deliverables, timelines, and acceptance criteria.
examples:
  - "Issue RFP for cloud migration services; evaluate 3 vendors; award contract to Vendor B for $120K, Q2 delivery."
  - "Procure 200 licenses of project management software; compare SaaS vs. perpetual license; choose SaaS at $15K/year."
  - "Vendor delivery delayed by 2 weeks — escalate per contract SLA and identify alternative vendor as backup."
---
# Procurement Planning — pm-230

## When to Use
Run this skill when a project requires external goods, services, or resources that cannot be supplied in-house. Initiate during planning phase and maintain throughout execution.

## Output
A **Procurement Plan** (procurement-plan.md) and a running **Procurement Log** (procurement-log.md).

## Make vs. Buy Criteria
| Factor | Favor Make | Favor Buy |
|---|---|---|
| Core competency | In-house expertise exists | No internal expertise |
| Volume | High, long-term | Low or one-time |
| Time | Sufficient lead time | Urgent need |
| Cost | Lower total cost of ownership | Higher cost but avoids investment |
| Risk | Low delivery risk | Vendor risk acceptable |

## Vendor Evaluation Scorecard (sample)
| Criteria | Weight | Vendor A | Vendor B | Vendor C |
|---|---|---|---|---|
| Cost | 30% | | | |
| Quality / Compliance | 25% | | | |
| Timeline | 20% | | | |
| Risk | 15% | | | |
| Past Performance | 10% | | | |
| **Weighted Score** | 100% | | | |
