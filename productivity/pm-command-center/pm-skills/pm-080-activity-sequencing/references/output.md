# Activity Sequencing Template

**Project Name:** Enterprise ERP Implementation
**Date:** 2026-05-29
**Prepared By:** Project Management Office
**Version:** 1.0

---

## 1. Activity List

| Activity ID | Activity Name | WBS Ref | Description | Owner | Duration (days) |
|-------------|---------------|---------|-------------|-------|-----------------|
| ACT-001 | Requirements Documentation | 1.1.2 | Document all business requirements for ERP system | Business Analyst | 5 |
| ACT-002 | Requirements Documentation | 1.1.2 | Document all business requirements for ERP system | Business Analyst | 5 |
| ACT-003 | Requirements Documentation | 1.1.2 | Document all business requirements for ERP system | Business Analyst | 5 |

---

## 2. Dependency Register

| Activity ID | Activity Name | Predecessor ID | Dependency Type | Lead/Lag Time | Notes |
|-------------|---------------|----------------|-----------------|---------------|-------|
| ACT-002 | Requirements Documentation | ACT-001 | FS | +2 days lead | Predecessor must be completed before start |
| ACT-003 | Requirements Documentation | ACT-002 | FS | +2 days lead | Predecessor must be completed before start |

**Dependency Types:**
- **FS** = Finish-to-Start (A must finish before B starts)
- **SS** = Start-to-Start (A must start before B starts)
- **FF** = Finish-to-Finish (A must finish before B finishes)
- **SF** = Start-to-Finish (A must start before B finishes)

---

## 3. Project Network Diagram (PDM)

```
Activity    ES    EF    LS    LF    Float    Critical
─────────────────────────────────────────────────────
ACT-001     0  5  0  5   0  Y
ACT-002     0  5  0  5   0  Y
ACT-003     0  5  0  5   0  Y
```

### Network Diagram (Visual)

```
[ACT-001]──FS──>[ACT-002]──SS──>[ACT-003]
  (3 days)     (+2 days lead)    (5 days)
                ↓
              [ACT-004]──FF──>[ACT-005]
```

---

## 4. Critical Path Analysis

### Critical Path Activities (Float = 0)

| Activity ID | Activity Name | Duration | Total Float |
|-------------|---------------|----------|-------------|
| CP-001 | Requirements Documentation | 5 | 0 |
| CP-002 | Requirements Documentation | 5 | 0 |
| CP-003 | Requirements Documentation | 5 | 0 |

**Total Critical Path Duration:** 5 days

### Near-Critical Paths

| Activity ID | Activity Name | Float (days) | Risk Level |
|-------------|---------------|--------------|------------|
| NC-001 | Requirements Documentation | 0 | {{High/Medium/Low}} |

---

## 5. Milestone List

| Milestone ID | Milestone Name | Activity ID | Target Date | Status |
|--------------|---------------|-------------|-------------|--------|
| MS-001 | Requirements Sign-off | ACT-XXX | 2026-05-29 | {{Draft/Confirmed/Achieved}} |
| MS-002 | Requirements Sign-off | ACT-XXX | 2026-05-29 | {{Draft/Confirmed/Achieved}} |

---

## 6. Lead and Lag Summary

| Activity ID | Lead/Lag Value | Reason | Risk Assessment |
|-------------|----------------|--------|-----------------|
| ACT-XXX | {{+2 days lead}} | {{REASON}} | {{RISK_NOTES}} |

---

## 7. Network Diagram Assumptions and Constraints

### Assumptions
- All required stakeholders available for review
- No scope changes during sequencing

### Constraints
- **Hard Deadline:** 2026-05-29 — May require fast-tracking or additional resources
- **External Dependency:** External vendor delivers third-party integration

---

## 8. Validation and Review

| Review Item | Owner | Date | Status |
|-------------|-------|------|--------|
| Dependency logic validated | Requirements Documentation | 2026-05-29 | {{Complete/Pending}} |
| Resource feasibility confirmed | Requirements Documentation | 2026-05-29 | {{Complete/Pending}} |
| Critical path reviewed | Requirements Documentation | 2026-05-29 | {{Complete/Pending}} |

---

## Notes

Critical path reviewed and approved by PMO