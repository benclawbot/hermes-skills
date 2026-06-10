# PM-240: Earned Value Management Template

## Overview
This template tracks project performance using Earned Value Management (EVM) metrics including CPI, SPI, and forecasting.

## Project Information

**Project Name**: Project Alpha - Enterprise System Upgrade
**Project Manager**: John Davidson
**Report Period**: May 1 - May 15, 2026
**Report Date**: 2026-05-29
## Baseline Data

| Metric | Original Budget | Current Budget |
|--------|-----------------|----------------|
| Planned Value (PV) | $450,000 | |
| Budget at Completion (BAC) | $500,000 | |

## Earned Value Metrics

### Current Period Performance

| Metric | Value | Formula |
|--------|-------|---------|
| Planned Value (PV) | $450,000 | |
| Earned Value (EV) | $210,000 | |
| Actual Cost (AC) | $230,000 | |

### Performance Indicators

| Indicator | Value | Status |
|-----------|-------|--------|
| Cost Variance (CV) | EV - AC | ☐ Favorable ☐ Unfavorable |
| Schedule Variance (SV) | EV - PV | ☐ Favorable ☐ Unfavorable |
| Cost Performance Index (CPI) | EV / AC | ☐ On Budget ☐ Over Budget ☐ Under Budget |
| Schedule Performance Index (SPI) | EV / PV | ☐ On Schedule ☐ Ahead ☐ Behind |

### Variance Analysis

| Work Package | PV | EV | AC | CV | SV | Status |
|--------------|----|----|----|----|----|--------|
| | Requirements Definition | $50,000 | $48,000 | $52,000 | -$4,000 | -$2,000 | Behind Schedule |
| | System Design | $75,000 | $72,000 | $78,000 | -$6,000 | -$3,000 | Behind Schedule |
| | Development | $150,000 | $90,000 | $100,000 | -$10,000 | -$10,000 | Behind Schedule |
## Forecasting

### Estimate at Completion (EAC)

| Method | Formula | Estimate |
|--------|---------|----------|
| Typical (AC + (BAC - EV)) | AC + (BAC - EV) / CPI | $549,451 |
| Best Case (AC + remaining work at budget rate) | AC + (BAC - EV) | $530,000 |
| Worst Case (AC + remaining work at current rate) | AC + (BAC - EV) / CPI | $570,000 |

### To Complete Performance Index (TCPI)

| Metric | Value |
|--------|-------|
| TCPI to meet BAC | (BAC - EV) / (BAC - AC) |
| TCPI to meet EAC | (EAC - EV) / (EAC - AC) |

### Projected Final Cost

**Estimated at Completion (EAC)**: $549,451
**Variance at Completion (VAC)**: BAC - EAC   
**Project Status**: ☐ On Budget ☐ Over Budget ☐ Under Budget

## Trend Analysis

| Period | PV | EV | AC | CPI | SPI |
|--------|----|----|----|-----|-----|
| | Week 1 | $50,000 | $48,000 | $45,000 | 0.96 | 0.94 |
| | Week 2 | $100,000 | $95,000 | $98,000 | 0.95 | 0.93 |
| | Week 3 | $175,000 | $162,000 | $185,000 | 0.91 | 0.90 |
## Analysis & Recommendations

### Root Cause Analysis (for negative variances)
**Cost Variance**:
Integration testing revealed more defects than estimated, requiring additional resources

**Schedule Variance**:
Third-party vendor delays impacted dependent tasks

### Recommended Actions
1. Implement pair programming to reduce defect discovery cost
2. Escalate vendor delivery issues to sponsor for alternative vendor assessment
3. Add 10% contingency to remaining work packages
## Approvals

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Manager | | | |
| Sponsor | | | |

---
*Template Version: 1.0 | Last Updated: 2026-05-20*