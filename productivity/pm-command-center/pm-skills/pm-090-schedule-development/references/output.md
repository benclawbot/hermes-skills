# Schedule Development Template

**Project Name:** Enterprise ERP Implementation
**Date:** 2026-05-29
**Prepared By:** Project Management Office
**Version:** 1.0

---

## 1. Schedule Parameters

| Field | Value |
|-------|-------|
| Project Start Date | 2026-05-29 |
| Project End Date | 2026-08-27 |
| Total Duration | 90 calendar days |
| Schedule Baseline Version | 1.0 |
| Working Days per Week | 90 |

---

## 2. Activity Duration Estimates

| Activity ID | Activity Name | Optimistic (days) | Most Likely (days) | Pessimistic (days) | Estimated Duration | Notes |
|-------------|---------------|-------------------|-------------------|--------------------|--------------------|-------|
| ACT-001 | John Smith | 3 | 5 | 8 | 5 | {{NOTES}} |
| ACT-002 | John Smith | 3 | 5 | 8 | 5 | {{NOTES}} |

**Calculation Method:** PERT
**PERT Formula:** (O + 4×ML + P) / 6

---

## 3. Resource Assignment

| Activity ID | Activity Name | Assigned Resource | Role | Available Hours | Required Hours | Over-allocated? |
|-------------|---------------|-------------------|------|-----------------|---------------|-----------------|
| ACT-001 | John Smith | John Smith | Senior Developer | 40 | 40 | {{Yes/No}} |
| ACT-002 | John Smith | John Smith | Senior Developer | 40 | 40 | {{Yes/No}} |

---

## 4. Over-Allocation Resolution Log

| Over-allocated Resource | Activity Causing Conflict | Resolution Action | Resolution Type | New Status |
|-------------------------|---------------------------|-------------------|-----------------|------------|
| Senior Developer | ACT-002 | Reassigned to alternate resource with similar skills | Leveling | Yes |

---

## 5. Gantt Chart Data

| Activity ID | Activity Name | Start Date | End Date | Duration (days) | % Complete | Dependencies | Milestone |
|-------------|---------------|------------|----------|-----------------|------------|--------------|-----------|
| ACT-001 | John Smith | 2026-05-29 | 2026-06-03 | 5 | 0 | ACT-001 | MS-001 |
| ACT-002 | John Smith | 2026-05-29 | 2026-06-03 | 5 | 0 | ACT-001 | — |
| ACT-003 | John Smith | 2026-05-29 | 2026-06-03 | 5 | 0 | ACT-001 | MS-002 |

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
| CP-001 | John Smith | {{ES}} | {{EF}} | {{LS}} | {{LF}} | 0 | YES |
| CP-002 | John Smith | {{ES}} | {{EF}} | {{LS}} | {{LF}} | 0 | YES |

**Critical Path Duration:** 90 days
**Project End Date:** 2026-05-29

---

## 7. Resource Loading Chart

| Resource Name | Role | Week 1 | Week 2 | Week 3 | Week 4 | Total Hours |
|---------------|------|--------|--------|--------|--------|-------------|
| John Smith | Senior Developer | 40 | 40 | 40 | 40 | {{TOTAL}} |
| John Smith | Senior Developer | 40 | 40 | 40 | 40 | {{TOTAL}} |

---

## 8. Schedule Contingency

| Buffer Type | Location | Duration | Justification |
|-------------|----------|----------|---------------|
| Schedule Buffer | After CP-001 | 90 days | Based on historical variance for similar projects |
| Milestone Buffer | MS-002 | 90 days | Based on historical variance for similar projects |

**Total Contingency:** 90 days
**Adjusted Project End Date:** 2026-05-29

---

## 9. Schedule Baseline Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Project Manager | John Smith | 2026-05-29 | ☐ |
| Project Sponsor | John Smith | 2026-05-29 | ☐ |
| Finance (if required) | John Smith | 2026-05-29 | ☐ |

---

## 10. Validation Against Constraints

| Constraint | Requirement | Schedule Date | Compliant? | Notes |
|------------|-------------|---------------|------------|-------|
| Hard Deadline | Must complete by Q4 | 2026-05-29 | {{Yes/No}} | {{NOTES}} |
| Contractual Date | Must complete by Q4 | 2026-05-29 | {{Yes/No}} | {{NOTES}} |

---

## Notes

{{ADDITIONAL_NOTES}}