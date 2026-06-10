# Work Breakdown Structure (WBS) Template

**Project Name:** {{PROJECT_NAME}}
**Date:** {{DATE}}
**Prepared By:** {{PREPARED_BY}}
**Version:** {{VERSION}}

---

## 1. WBS Overview

| Field | Value |
|-------|-------|
| WBS Code Prefix | {{PREFIX}} |
| Decomposition Approach | {{DELIVERABLE_BASED / PHASE_BASED / ORGANIZATIONAL}} |
| Number of Top-Level Nodes | {{COUNT}} |
| Total Work Packages | {{COUNT}} |
| WBS Baseline Version | {{VERSION}} |

---

## 2. Project Objective (Level 0)

**Project Title:** {{PROJECT_TITLE}}
**Objective Statement:** {{OBJECTIVE_TEXT}}
**Success Criteria:** {{SUCCESS_CRITERIA}}

---

## 3. WBS Dictionary

### Level 1 — Major Deliverables

#### 1.0 {{MAJOR_DELIVERABLE_NAME}}
- **Description:** {{DELIVERABLE_DESCRIPTION}}
- **Owner:** {{ROLE/DEPARTMENT}}
- **WBS Code:** 1.0

##### Level 2 — Sub-Deliverables

###### 1.1 {{SUB_DELIVERABLE_NAME}}
- **Description:** {{DESCRIPTION}}
- **Owner:** {{ROLE}}
- **Dependencies:** {{DEPENDENCIES}}
- **Quality Criteria:** {{QUALITY_CRITERIA}}
- **Effort Estimate:** {{HOURS}} hours
- **WBS Code:** 1.1

###### 1.2 {{SUB_DELIVERABLE_NAME}}
- **Description:** {{DESCRIPTION}}
- **Owner:** {{ROLE}}
- **Dependencies:** {{DEPENDENCIES}}
- **Quality Criteria:** {{QUALITY_CRITERIA}}
- **Effort Estimate:** {{HOURS}} hours
- **WBS Code:** 1.2

##### Level 3 — Work Packages

###### 1.1.1 {{WORK_PACKAGE_NAME}}
- **Description:** {{DESCRIPTION}}
- **Responsible Owner:** {{ROLE/INDIVIDUAL}}
- **Dependencies:** {{LIST_DEPENDENCIES}}
- **Quality Criteria:** {{QUALITY_CRITERIA}}
- **Acceptance Sign-off:** {{ROLE}}
- **Estimated Effort:** {{HOURS}} hours
- **WBS Code:** 1.1.1

###### 1.1.2 {{WORK_PACKAGE_NAME}}
- **Description:** {{DESCRIPTION}}
- **Responsible Owner:** {{ROLE/INDIVIDUAL}}
- **Dependencies:** {{LIST_DEPENDENCIES}}
- **Quality Criteria:** {{QUALITY_CRITERIA}}
- **Acceptance Sign-off:** {{ROLE}}
- **Estimated Effort:** {{HOURS}} hours
- **WBS Code:** 1.1.2

---

## 4. WBS Hierarchical Tree (Visual)

```
{{PROJECT_TITLE}} (0.0)
├── 1.0 {{DELIVERABLE_1}}
│   ├── 1.1 {{SUB_DELIVERABLE_1}}
│   │   ├── 1.1.1 {{WORK_PACKAGE}}
│   │   └── 1.1.2 {{WORK_PACKAGE}}
│   └── 1.2 {{SUB_DELIVERABLE_2}}
│       ├── 1.2.1 {{WORK_PACKAGE}}
│       └── 1.2.2 {{WORK_PACKAGE}}
└── 2.0 {{DELIVERABLE_2}}
    ├── 2.1 {{SUB_DELIVERABLE}}
    │   ├── 2.1.1 {{WORK_PACKAGE}}
    │   └── 2.1.2 {{WORK_PACKAGE}}
    └── 2.2 {{SUB_DELIVERABLE}}
        ├── 2.2.1 {{WORK_PACKAGE}}
        └── 2.2.2 {{WORK_PACKAGE}}
```

---

## 5. Scope Baseline Summary

| WBS Element | Description | Owner | Effort (hrs) | Duration (days) | Cost |
|-------------|-------------|-------|--------------|-----------------|------|
| 1.0 | {{DESCRIPTION}} | {{ROLE}} | {{HOURS}} | {{DAYS}} | {{$AMOUNT}} |
| 1.1 | {{DESCRIPTION}} | {{ROLE}} | {{HOURS}} | {{DAYS}} | {{$AMOUNT}} |
| 1.1.1 | {{DESCRIPTION}} | {{ROLE}} | {{HOURS}} | {{DAYS}} | {{$AMOUNT}} |
| | | | | | |
| **TOTAL** | | | **{{TOTAL_HOURS}}** | **{{TOTAL_DAYS}}** | **{{$TOTAL_COST}}** |

---

## 6. Requirements Traceability Matrix

| Requirement ID | Requirement Text | WBS Element(s) | Coverage Status |
|----------------|------------------|----------------|-----------------|
| REQ-001 | {{TEXT}} | 1.1.1, 1.2.1 | ✅ Covered |
| REQ-002 | {{TEXT}} | 1.2.2 | ✅ Covered |
| REQ-003 | {{TEXT}} | — | ⚠️ Gap — Assign WBS |

---

## 7. Control Account Plan

| Control Account Code | WBS Element | Responsible Team | Cost Account Manager | Budget |
|----------------------|-------------|------------------|----------------------|--------|
| CA-001 | 1.1 | {{TEAM}} | {{NAME}} | {{$AMOUNT}} |
| CA-002 | 1.2 | {{TEAM}} | {{NAME}} | {{$AMOUNT}} |
| CA-003 | 2.1 | {{TEAM}} | {{NAME}} | {{$AMOUNT}} |

---

## 8. Validation Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Manager | {{NAME}} | {{DATE}} | |
| Control Account Manager | {{NAME}} | {{DATE}} | |
| Project Sponsor | {{NAME}} | {{DATE}} | |

---

## Notes

{{ADDITIONAL_NOTES}}