# Schedule Development Template

**Project Name:** {{PROJECT_NAME}}
**Date:** {{DATE}}
**Prepared By:** {{PREPARED_BY}}
**Version:** {{VERSION}}

---

## 1. Schedule Parameters

| Field | Value |
|-------|-------|
| Project Start Date | {{START_DATE}} |
| Project End Date | {{END_DATE}} |
| Total Duration | {{DAYS}} calendar days |
| Schedule Baseline Version | {{VERSION}} |
| Working Days per Week | {{DAYS}} |

---

## 2. Activity Duration Estimates

| Activity ID | Activity Name | Optimistic (days) | Most Likely (days) | Pessimistic (days) | Estimated Duration | Notes |
|-------------|---------------|-------------------|-------------------|--------------------|--------------------|-------|
| ACT-001 | {{NAME}} | {{O}} | {{ML}} | {{P}} | {{EST}} | {{NOTES}} |
| ACT-002 | {{NAME}} | {{O}} | {{ML}} | {{P}} | {{EST}} | {{NOTES}} |

**Calculation Method:** {{PERT / BOTTOM_UP / HISTORICAL}}
**PERT Formula:** (O + 4×ML + P) / 6

---

## 3. Resource Assignment

| Activity ID | Activity Name | Assigned Resource | Role | Available Hours | Required Hours | Over-allocated? |
|-------------|---------------|-------------------|------|-----------------|---------------|-----------------|
| ACT-001 | {{NAME}} | {{NAME}} | {{ROLE}} | {{HRS}} | {{HRS}} | {{Yes/No}} |
| ACT-002 | {{NAME}} | {{NAME}} | {{ROLE}} | {{HRS}} | {{HRS}} | {{Yes/No}} |

---

## 4. Over-Allocation Resolution Log

| Over-allocated Resource | Activity Causing Conflict | Resolution Action | Resolution Type | New Status |
|-------------------------|---------------------------|-------------------|-----------------|------------|
| {{RESOURCE}} | {{ACTIVITY}} | {{ACTION}} | {{Leveling/FastTrack/Crashing}} | {{Resolved}} |

---

## 5. Gantt Chart Data

| Activity ID | Activity Name | Start Date | End Date | Duration (days) | % Complete | Dependencies | Milestone |
|-------------|---------------|------------|----------|-----------------|------------|--------------|-----------|
| ACT-001 | {{NAME}} | {{START}} | {{END}} | {{DUR}} | {{%}} | {{DEPS}} | {{MS-001}} |
| ACT-002 | {{NAME}} | {{START}} | {{END}} | {{DUR}} | {{%}} | {{DEPS}} | — |
| ACT-003 | {{NAME}} | {{START}} | {{END}} | {{DUR}} | {{%}} | {{DEPS}} | {{MS-002}} |

### Gantt Chart (Visual)

```
Activity       │ W1 │ W2 │ W3 │ W4 │ W5 │ W6 │ W7 │ W8 │
───────────────┼────┴────┴────┴────┴────┴────┴────┴────┤
ACT-001        │████████████│                            │ ← Duration
ACT-002        │            │██████████████│            │ ← Duration
ACT-003        │            │    ◆          │████████████│ ← Duration, Milestone ◆
               │            │               │            │
◆ = Milestone
```

---

## 6. Critical Path Report

| Activity ID | Activity Name | ES | EF | LS | LF | Float | Critical |
|-------------|---------------|----|----|----|----|----|----------|
| CP-001 | {{NAME}} | {{ES}} | {{EF}} | {{LS}} | {{LF}} | 0 | YES |
| CP-002 | {{NAME}} | {{ES}} | {{EF}} | {{LS}} | {{LF}} | 0 | YES |

**Critical Path Duration:** {{DAYS}} days
**Project End Date:** {{DATE}}

---

## 7. Resource Loading Chart

| Resource Name | Role | Week 1 | Week 2 | Week 3 | Week 4 | Total Hours |
|---------------|------|--------|--------|--------|--------|-------------|
| {{NAME}} | {{ROLE}} | {{HRS}} | {{HRS}} | {{HRS}} | {{HRS}} | {{TOTAL}} |
| {{NAME}} | {{ROLE}} | {{HRS}} | {{HRS}} | {{HRS}} | {{HRS}} | {{TOTAL}} |

---

## 8. Schedule Contingency

| Buffer Type | Location | Duration | Justification |
|-------------|----------|----------|---------------|
| Schedule Buffer | After CP-001 | {{DAYS}} days | {{RISK_REASON}} |
| Milestone Buffer | MS-002 | {{DAYS}} days | {{RISK_REASON}} |

**Total Contingency:** {{DAYS}} days
**Adjusted Project End Date:** {{DATE}}

---

## 9. Schedule Baseline Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Project Manager | {{NAME}} | {{DATE}} | ☐ |
| Project Sponsor | {{NAME}} | {{DATE}} | ☐ |
| Finance (if required) | {{NAME}} | {{DATE}} | ☐ |

---

## 10. Validation Against Constraints

| Constraint | Requirement | Schedule Date | Compliant? | Notes |
|------------|-------------|---------------|------------|-------|
| Hard Deadline | {{CONSTRAINT}} | {{DATE}} | {{Yes/No}} | {{NOTES}} |
| Contractual Date | {{CONSTRAINT}} | {{DATE}} | {{Yes/No}} | {{NOTES}} |

---

## Notes

{{ADDITIONAL_NOTES}}