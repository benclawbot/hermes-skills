# Activity Sequencing Template

**Project Name:** {{PROJECT_NAME}}
**Date:** {{DATE}}
**Prepared By:** {{PREPARED_BY}}
**Version:** {{VERSION}}

---

## 1. Activity List

| Activity ID | Activity Name | WBS Ref | Description | Owner | Duration (days) |
|-------------|---------------|---------|-------------|-------|-----------------|
| ACT-001 | {{ACTIVITY_NAME}} | {{WBS_CODE}} | {{DESCRIPTION}} | {{ROLE}} | {{DAYS}} |
| ACT-002 | {{ACTIVITY_NAME}} | {{WBS_CODE}} | {{DESCRIPTION}} | {{ROLE}} | {{DAYS}} |
| ACT-003 | {{ACTIVITY_NAME}} | {{WBS_CODE}} | {{DESCRIPTION}} | {{ROLE}} | {{DAYS}} |

---

## 2. Dependency Register

| Activity ID | Activity Name | Predecessor ID | Dependency Type | Lead/Lag Time | Notes |
|-------------|---------------|----------------|-----------------|---------------|-------|
| ACT-002 | {{NAME}} | ACT-001 | {{FS/SS/FF/SF}} | {{LEAD_LAG}} | {{NOTES}} |
| ACT-003 | {{NAME}} | ACT-002 | {{FS/SS/FF/SF}} | {{LEAD_LAG}} | {{NOTES}} |

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
ACT-001     {{ES}}  {{EF}}  {{LS}}  {{LF}}   {{FLOAT}}  {{Y/N}}
ACT-002     {{ES}}  {{EF}}  {{LS}}  {{LF}}   {{FLOAT}}  {{Y/N}}
ACT-003     {{ES}}  {{EF}}  {{LS}}  {{LF}}   {{FLOAT}}  {{Y/N}}
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
| CP-001 | {{ACTIVITY_NAME}} | {{DAYS}} | 0 |
| CP-002 | {{ACTIVITY_NAME}} | {{DAYS}} | 0 |
| CP-003 | {{ACTIVITY_NAME}} | {{DAYS}} | 0 |

**Total Critical Path Duration:** {{DAYS}} days

### Near-Critical Paths

| Activity ID | Activity Name | Float (days) | Risk Level |
|-------------|---------------|--------------|------------|
| NC-001 | {{ACTIVITY_NAME}} | {{FLOAT}} | {{High/Medium/Low}} |

---

## 5. Milestone List

| Milestone ID | Milestone Name | Activity ID | Target Date | Status |
|--------------|---------------|-------------|-------------|--------|
| MS-001 | {{MILESTONE_NAME}} | ACT-XXX | {{DATE}} | {{Draft/Confirmed/Achieved}} |
| MS-002 | {{MILESTONE_NAME}} | ACT-XXX | {{DATE}} | {{Draft/Confirmed/Achieved}} |

---

## 6. Lead and Lag Summary

| Activity ID | Lead/Lag Value | Reason | Risk Assessment |
|-------------|----------------|--------|-----------------|
| ACT-XXX | {{+2 days lead}} | {{REASON}} | {{RISK_NOTES}} |

---

## 7. Network Diagram Assumptions and Constraints

### Assumptions
- {{ASSUMPTION_1}}
- {{ASSUMPTION_2}}

### Constraints
- **Hard Deadline:** {{DATE}} — {{DESCRIBE_IMPACT}}
- **External Dependency:** {{DEPENDENCY_DESCRIPTION}}

---

## 8. Validation and Review

| Review Item | Owner | Date | Status |
|-------------|-------|------|--------|
| Dependency logic validated | {{NAME}} | {{DATE}} | {{Complete/Pending}} |
| Resource feasibility confirmed | {{NAME}} | {{DATE}} | {{Complete/Pending}} |
| Critical path reviewed | {{NAME}} | {{DATE}} | {{Complete/Pending}} |

---

## Notes

{{ADDITIONAL_NOTES}}