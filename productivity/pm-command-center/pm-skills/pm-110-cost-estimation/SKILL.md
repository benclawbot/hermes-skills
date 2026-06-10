---
name: pm-110-cost-estimation
description: Develop project cost estimates — labor, materials, equipment, contingency, and budget baseline (Tier 2 — core planning artifact)
trigger: "When you need to convert activity durations and resource assignments into a credible budget and cost baseline"
when_to_use: |
  - After schedule development (pm-090) gives you durations and resource assignments
  - When you need to present a budget to sponsors or finance for approval
  - Before procurement decisions or contract negotiations
  - When cost overrun risks require contingency reserves
inputs:
  - Activity list with durations
  - Resource assignments and hourly rates
  - WBS (work packages map to cost accounts)
  - Vendor quotes or procurement contracts
  - Historical cost data from similar projects
  - Cost_management_plan (threshold for budget changes)
  - Organizational cost accounting policies
workflow:
  1. Estimate labor costs — multiply estimated hours per activity by hourly labor rate (including overhead, benefits, or blended rates). Sum by resource type or individual.
  2. Estimate material and equipment costs — itemize physical materials needed. Get quotes for anything over a minor threshold. Document assumptions (freight, shipping, lead time, bulk discounts).
  3. Estimate vendor/contractor costs — use signed quotes where available, or rough order of magnitude (ROM) at plus/minus 25% accuracy if quotes are not in yet. Flag as TBD.
  4. Estimate other direct costs — travel, training, software licenses, facility costs. Be specific, not lump-sum.
  5. Calculate indirect costs — overhead allocation, program management fees, admin overhead. Apply organizational policy (% markup or fixed rate).
  6. Build the cost baseline — roll up all estimates by WBS element and project phase. This is your Budget at Completion (BAC).
  7. Apply contingency — add management reserve to the baseline based on risk assessment. Typical range: 5-15% for well-understood work, 20-40% for innovative/high-uncertainty work. Contingency is for unknown risks, not known scope.
  8. Validate against benchmarks — compare total cost (or cost per deliverable) to similar past projects. Investigate variances greater than 20%.
  9. Present the budget in required format — often three levels: summary by phase, detailed by WBS, and cash flow by month/quarter.
  10. Obtain approval — get signed budget baseline from sponsor and finance. This becomes the cost performance baseline (EVT).
output: |
  - Cost estimate document: labor, materials, vendor, other costs, contingency per WBS element
  - Budget at Completion (BAC): approved total project cost
  - Cost baseline: time-phased budget (monthly/quarterly spend curve)
  - Cash flow forecast: planned expenditure over time (for finance planning)
  - Contingency reserve: amount and trigger criteria for using it
  - Cost breakdown by phase or deliverable
  - Budget approval sign-off from sponsor and finance
tips: |
  - Never estimate in a vacuum — always use historical data as a sanity check. If you do not have comparable projects, use three independent estimate methods and reconcile.
  - Contingency is not a padding line — it has a specific purpose (unknown risks) and a governance process. Use it, do not hide it.
  - Labor rates should reflect the whole cost to the organization — benefits, taxes, overhead. If you use fully-loaded rates, you avoid surprises later.
  - Budget estimates in early phases (plus/minus 25-50%) should be clearly labeled as ROM — do not let stakeholders treat them as firm commitments.
  - Build a time-phased budget even if you do not need monthly reporting — it forces you to think about when money is actually spent, not just what is spent.
---

# pm-110-cost-estimation

Develop project cost estimates — labor, materials, equipment, contingency, and budget baseline.

## When to Use

- After schedule development (pm-090) gives you durations and resource assignments
- When you need to present a budget to sponsors or finance for approval
- Before procurement decisions or contract negotiations
- When cost overrun risks require contingency reserves

## Inputs

- Activity list with durations
- Resource assignments and hourly rates
- WBS (work packages map to cost accounts)
- Vendor quotes or procurement contracts
- Historical cost data from similar projects
- Cost_management_plan (threshold for budget changes)
- Organizational cost accounting policies

## Workflow

1. Estimate labor costs — multiply estimated hours per activity by hourly labor rate (including overhead, benefits, or blended rates). Sum by resource type or individual.
2. Estimate material and equipment costs — itemize physical materials needed. Get quotes for anything over a minor threshold. Document assumptions (freight, shipping, lead time, bulk discounts).
3. Estimate vendor/contractor costs — use signed quotes where available, or rough order of magnitude (ROM) at plus/minus 25% accuracy if quotes are not in yet. Flag as TBD.
4. Estimate other direct costs — travel, training, software licenses, facility costs. Be specific, not lump-sum.
5. Calculate indirect costs — overhead allocation, program management fees, admin overhead. Apply organizational policy (% markup or fixed rate).
6. Build the cost baseline — roll up all estimates by WBS element and project phase. This is your Budget at Completion (BAC).
7. Apply contingency — add management reserve to the baseline based on risk assessment. Typical range: 5-15% for well-understood work, 20-40% for innovative/high-uncertainty work. Contingency is for unknown risks, not known scope.
8. Validate against benchmarks — compare total cost (or cost per deliverable) to similar past projects. Investigate variances greater than 20%.
9. Present the budget in required format — often three levels: summary by phase, detailed by WBS, and cash flow by month/quarter.
10. Obtain approval — get signed budget baseline from sponsor and finance. This becomes the cost performance baseline (EVT).

## Output

- Cost estimate document: labor, materials, vendor, other costs, contingency per WBS element
- Budget at Completion (BAC): approved total project cost
- Cost baseline: time-phased budget (monthly/quarterly spend curve)
- Cash flow forecast: planned expenditure over time (for finance planning)
- Contingency reserve: amount and trigger criteria for using it
- Cost breakdown by phase or deliverable
- Budget approval sign-off from sponsor and finance

## Tips

- Never estimate in a vacuum — always use historical data as a sanity check. If you do not have comparable projects, use three independent estimate methods and reconcile.
- Contingency is not a padding line — it has a specific purpose (unknown risks) and a governance process. Use it, do not hide it.
- Labor rates should reflect the whole cost to the organization — benefits, taxes, overhead. If you use fully-loaded rates, you avoid surprises later.
- Budget estimates in early phases (plus/minus 25-50%) should be clearly labeled as ROM — do not let stakeholders treat them as firm commitments.
- Build a time-phased budget even if you do not need monthly reporting — it forces you to think about when money is actually spent, not just what is spent.