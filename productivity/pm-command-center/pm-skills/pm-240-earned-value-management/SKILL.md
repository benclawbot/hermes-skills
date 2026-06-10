---
name: pm-240-earned-value-management
description: Track project performance using Earned Value Management (EVM) — CPI, SPI, EV, PV, AC metrics and forecasting.
triggers:
  - "When do we need an EVM report?"
  - "What is our cost performance index?"
  - "Are we on schedule?"
  - "Project health dashboard"
  - "EVM forecast"
tags:
  - tier-1
  - monitoring
  - earned-value
  - evm
  - cpi
  - spi
  - forecasting
category: pm
---

# PM-240: Earned Value Management (EVM)

Earned Value Management is a Tier 1 monitoring technique that integrates scope, schedule, and cost measurements to assess project health objectively.

---

## Core EVM Metrics

### The Three Baselines

| Acronym | Name | Definition |
|---------|------|------------|
| **PV** | Planned Value | Budgeted cost of work scheduled (BCWS) |
| **EV** | Earned Value | Budgeted cost of work performed (BCWP) |
| **AC** | Actual Cost | Actual cost of work performed (ACWP) |

### Variance & Index Formulas

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Schedule Variance (SV)** | EV − PV | Positive = ahead, Negative = behind |
| **Cost Variance (CV)** | EV − AC | Positive = under budget, Negative = over |
| **Schedule Performance Index (SPI)** | EV / PV | >1 = ahead, <1 = behind |
| **Cost Performance Index (CPI)** | EV / AC | >1 = under budget, <1 = over |
| **Estimate at Completion (EAC)** | BAC / CPI (among variants) | Forecast final cost |
| **Variance at Completion (VAC)** | BAC − EAC | Forecast cost overrun/savings |
| **To-Complete Performance Index (TCPI)** | (BAC − EV) / (BAC − AC) | Cost efficiency needed to stay on budget |

---

## EVM Interpretation Guide

### Status Thresholds

| Index Value | Status | Action |
|-------------|--------|--------|
| CPI ≥ 1.0 and SPI ≥ 1.0 | **On Track** | Maintain monitoring |
| 0.9 ≤ CPI < 1.0 or 0.9 ≤ SPI < 1.0 | **Caution** | Investigate root cause |
| CPI < 0.9 or SPI < 0.9 | **Critical** | Escalate and corrective action |
| TCPI > 1.2 | **At Risk** | Recovery unlikely without intervention |

### Forecasting Models (EAC)

| Approach | Formula | When to Use |
|----------|---------|-------------|
| **Variance-based** | BAC − CV | Current variances are atypical |
| **CPI-based** | BAC / CPI | Current performance will continue |
| **Composite** | AC + (BAC − EV) / (CPI × SPI) | Schedule and cost both factor |
| **Bottom-up** | AC + remaining work | Detailed re-estimate available |

---

## Step-by-Step: Produce an EVM Report

### Step 1: Gather Baseline Data

```
1. Confirm the project WBS and control account baselines
2. Obtain the detailed project schedule with baseline costs
3. Identify the budget at completion (BAC) for each work package
```

### Step 2: Collect Performance Data

```
1. Obtain status date (data date)
2. Gather actual costs expended to date (AC)
3. Determine earned value: % complete × BAC for each work package
   - 0/100 method (pass/fail on tasks)
   - 50/50 method (50% credit when started, 50% when complete)
   - % complete method (subjective estimation)
4. Calculate planned value from the baseline schedule
```

### Step 3: Calculate Metrics

```
For each control account:
  SV  = EV - PV
  CV  = EV - AC
  SPI = EV / PV
  CPI = EV / AC

For the project:
  Overall SPI = Sum(EV) / Sum(PV)
  Overall CPI = Sum(EV) / Sum(AC)
  VAC = BAC - EAC
```

### Step 4: Forecast

```
EAC  = BAC / CPI               # if CPI-based
TCPI = (BAC - EV) / (BAC - AC) # cost efficiency required
```

### Step 5: Narrative & Recommendations

Write a brief health summary:
```
- Overall status: GREEN / YELLOW / RED
- SV and CV trend over last 3 reporting periods
- Primary drivers of any variance
- Forecast trajectory and risk to BAC
- Recommended corrective actions
```

---

## Example EVM Dashboard (Text)

```
Project: [Name]         Status Date: [YYYY-MM-DD]
Sponsor: [Name]         Next Review: [Date]
─────────────────────────────────────────────────
  PV (Planned Value):   $500,000
  EV (Earned Value):    $450,000
  AC (Actual Cost):     $480,000
─────────────────────────────────────────────────
  Schedule Variance:    -$50,000  (SPI: 0.90)
  Cost Variance:        -$30,000  (CPI: 0.94)
─────────────────────────────────────────────────
  BAC:  $1,000,000
  EAC:  $1,064,000       ← Forecast
  VAC:  -$64,000         ← Projected Overrun
  TCPI:  1.07            ← Required to finish on budget
─────────────────────────────────────────────────
  Status: AMBER — Cost and schedule slippage detected
  Primary Issue: [Description]
  Corrective Action: [Owner] [Due Date]
```

---

## Common Pitfalls

- **Using subjective % complete instead of objective methods** — inflate EV, mask true status
- **Inconsistent data date** — all three metrics must use the same status date
- **Ignoring schedule variance when cost is on track** — SV affects downstream cost
- **TCPI > 1.2 not escalated** — recovery probability drops sharply above this threshold
- **Reporting EAC without noting the assumption** — always state which EAC formula was used
- **BAC not locked** — EVM is meaningless if the baseline keeps moving

---

## Verification Steps

```
1. Confirm PV + EV + AC are all expressed in same currency and time period
2. Verify EV ≤ BAC for each work package (cannot earn more than budgeted)
3. Verify SPI and CPI are calculated independently before combining
4. Cross-check EAC against finance's actual spend + remaining commitment
5. Confirm TCPI is directionally correct: TCPI < CPI means recovery is feasible
```

---

## Related Skills

- pm-120-risk-identification: Risk assessment feeds EVM forecasting
- pm-190-sprint-planning: Sprint velocity relates to EV tracking in agile
- pm-290-status-reporting: EVM output feeds the formal status report
- pm-110-cost-estimation: BAC originates from cost estimation
