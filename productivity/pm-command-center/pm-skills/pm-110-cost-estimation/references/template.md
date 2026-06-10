# Cost Estimation Template

**Project Name:** {{PROJECT_NAME}}
**Date:** {{DATE}}
**Prepared By:** {{PREPARED_BY}}
**Version:** {{VERSION}}

---

## 1. Cost Estimate Summary

| Field | Value |
|-------|-------|
| Estimate Type | {{ROM / DETAILED / FINAL}} |
| Estimate Accuracy | {{+/-XX%}} |
| Budget at Completion (BAC) | {{$AMOUNT}} |
| Contingency Reserve | {{$AMOUNT}} |
| Total Project Budget | {{$AMOUNT}} |
| Currency | {{CURRENCY}} |

---

## 2. Labor Cost Estimates

| Activity ID | Activity Name | WBS Ref | Resource/Role | Hours | Hourly Rate (Fully-Loaded) | Total Labor Cost |
|-------------|---------------|---------|---------------|-------|---------------------------|------------------|
| ACT-001 | {{NAME}} | {{WBS}} | {{ROLE}} | {{HRS}} | {{$RATE}} | {{$COST}} |
| ACT-002 | {{NAME}} | {{WBS}} | {{ROLE}} | {{HRS}} | {{$RATE}} | {{$COST}} |
| | | | | **{{TOTAL_HRS}}** | | **{{$TOTAL_LABOR}}** |

**Hourly Rate Includes:** Base salary + Benefits + Taxes + Overhead

---

## 3. Material and Equipment Costs

| Item Description | WBS Ref | Quantity | Unit Cost | Total Cost | Vendor/Supplier | Quote Date |
|------------------|---------|----------|-----------|------------|-----------------|------------|
| {{MATERIAL_ITEM}} | {{WBS}} | {{QTY}} | {{$UNIT}} | {{$TOTAL}} | {{VENDOR}} | {{DATE}} |
| {{EQUIPMENT_ITEM}} | {{WBS}} | {{QTY}} | {{$UNIT}} | {{$TOTAL}} | {{VENDOR}} | {{DATE}} |
| | | | | **Subtotal** | **{{$MATERIAL_TOTAL}}** | | |

**Assumptions:**
- Freight/Shipping: {{$AMOUNT}}
- Bulk Discount: {{$AMOUNT or N/A}}
- Lead Time: {{DAYS}} days

---

## 4. Vendor/Contractor Costs

| Contract/Quote ID | Vendor Name | Service/Deliverable | WBS Ref | Contract Value | Status | Notes |
|-------------------|-------------|---------------------|---------|----------------|--------|-------|
| {{CONTRACT_ID}} | {{VENDOR}} | {{SERVICE}} | {{WBS}} | {{$AMOUNT}} | {{Signed/ROM/Pending}} | {{NOTES}} |
| | | | | **Subtotal** | **{{$VENDOR_TOTAL}}** | | |

---

## 5. Other Direct Costs

| Cost Category | Description | WBS Ref | Amount | Notes |
|---------------|-------------|---------|--------|-------|
| Travel | {{TRAVEL_DESCRIPTION}} | {{WBS}} | {{$AMOUNT}} | {{NOTES}} |
| Training | {{TRAINING_DESCRIPTION}} | {{WBS}} | {{$AMOUNT}} | {{NOTES}} |
| Software Licenses | {{SOFTWARE_DESCRIPTION}} | {{WBS}} | {{$AMOUNT}} | {{NOTES}} |
| Facilities/space | {{FACILITIES_DESCRIPTION}} | {{WBS}} | {{$AMOUNT}} | {{NOTES}} |
| | | | **Subtotal** | **{{$OTHER_TOTAL}}** | |

---

## 6. Indirect Costs / Overhead

| Overhead Type | Calculation Method | Rate | Applied To | Amount |
|---------------|-------------------|------|------------|--------|
| Program Management Fee | {{METHOD}} | {{RATE}} | Total Direct Costs | {{$AMOUNT}} |
| Admin Overhead | {{METHOD}} | {{RATE}} | Labor | {{$AMOUNT}} |
| Other Overhead | {{METHOD}} | {{RATE}} | {{BASE}} | {{$AMOUNT}} |
| | | | **Subtotal** | **{{$INDIRECT_TOTAL}}** |

---

## 7. Cost Baseline Roll-up (By WBS Element)

| WBS Code | WBS Element Name | Labor | Materials | Vendor | Other Direct | Indirect | Total |
|----------|------------------|-------|-----------|--------|-------------|---------|-------|
| 1.1 | {{DELIVERABLE}} | {{$}} | {{$}} | {{$}} | {{$}} | {{$}} | {{$}} |
| 1.2 | {{DELIVERABLE}} | {{$}} | {{$}} | {{$}} | {{$}} | {{$}} | {{$}} |
| 2.0 | {{DELIVERABLE}} | {{$}} | {{$}} | {{$}} | {{$}} | {{$}} | {{$}} |
| | **TOTAL** | **{{$}}** | **{{$}}** | **{{$}}** | **{{$}}** | **{{$}}** | **{{$BAC}}** |

**Budget at Completion (BAC):** {{$AMOUNT}}

---

## 8. Cost Baseline Roll-up (By Project Phase)

| Phase | Start Date | End Date | Total Cost | % of Budget |
|-------|------------|----------|------------|-------------|
| Initiation | {{DATE}} | {{DATE}} | {{$AMOUNT}} | {{%}} |
| Planning | {{DATE}} | {{DATE}} | {{$AMOUNT}} | {{%}} |
| Execution | {{DATE}} | {{DATE}} | {{$AMOUNT}} | {{%}} |
| Closing | {{DATE}} | {{DATE}} | {{$AMOUNT}} | {{%}} |
| **TOTAL** | | | **{{$BAC}}** | **100%** |

---

## 9. Contingency Reserve

| Contingency Type | Amount | % of BAC | Justification | Trigger Criteria |
|------------------|--------|----------|---------------|-------------------|
| Management Reserve | {{$AMOUNT}} | {{%}} | {{RISK_JUSTIFICATION}} | {{TRIGGER}} |
| Risk Contingency | {{$AMOUNT}} | {{%}} | {{RISK_JUSTIFICATION}} | {{TRIGGER}} |
| **Total Contingency** | **{{$TOTAL}}** | **{{%}}** | | |

**Contingency Governance:** {{HOW_CONTINGENCY_WILL_BE_RELEASED}}

---

## 10. Time-Phased Budget (Cash Flow)

| Month/Quarter | Planned Spend | Cumulative Spend | Budget Remaining |
|---------------|---------------|------------------|-----------------|
| {{MONTH/QUARTER}} | {{$AMOUNT}} | {{$AMOUNT}} | {{$AMOUNT}} |
| {{MONTH/QUARTER}} | {{$AMOUNT}} | {{$AMOUNT}} | {{$AMOUNT}} |
| **TOTAL** | **{{$BAC}}** | | |

---

## 11. Benchmark Validation

| Metric | This Project | Similar Past Project | Variance | Explanation |
|--------|--------------|----------------------|----------|-------------|
| Cost per WBS Element | {{$}} | {{$}} | {{%}} | {{NOTES}} |
| Labor Cost as % of Total | {{%}} | {{%}} | {{%}} | {{NOTES}} |
| Cost per Phase | {{$}} | {{$}} | {{%}} | {{NOTES}} |

**Variance > 20% Investigation Required:** ☐ Required ☐ Not Required

---

## 12. Budget Approval Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Project Manager | {{NAME}} | {{DATE}} | ☐ |
| Project Sponsor | {{NAME}} | {{DATE}} | ☐ |
| Finance Representative | {{NAME}} | {{DATE}} | ☐ |

**Approved Budget at Completion (BAC):** {{$AMOUNT}}
**Approval Date:** {{DATE}}

---

## Notes

{{ADDITIONAL_NOTES}}