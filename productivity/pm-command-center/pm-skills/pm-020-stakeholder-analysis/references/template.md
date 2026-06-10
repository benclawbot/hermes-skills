# Stakeholder Analysis Register

**Project Name:** {{PROJECT_NAME}}
**Analysis Date:** {{ANALYSIS_DATE}}
**Analyst:** {{ANALYST_NAME}}
**Version:** {{DOCUMENT_VERSION}}

---

## 1. Power/Interest Grid Classification

### Grid Placement Legend
- **X-axis:** Power (Low → High)
- **Y-axis:** Interest (Low → High)

```
                    HIGH INTEREST
                        │
          ┌─────────────┼─────────────┐
          │   MONITOR   │ MANAGE      │
          │  (Low Power,│ CLOSELY     │
          │  High Int.) │(High Power, │
          │             │ High Int.)  │
LOW POWER ├─────────────┼─────────────┤ HIGH POWER
          │  KEEP       │ KEEP        │
          │  INFORMED   │ SATISFIED   │
          │  (Low Power,│ (High Power,│
          │  Low Int.)  │ Low Int.)   │
          └─────────────┼─────────────┘
                        │
                    LOW INTEREST
```

### 1.1 Quadrant Summary

| Quadrant | Description | Count |
|----------|-------------|
| Manage Closely | High Power, High Interest — Key decision-makers and champions | {{MC_COUNT}} |
| Keep Satisfied | High Power, Low Interest — Needs updates only on major decisions | {{KS_COUNT}} |
| Keep Informed | Low Power, High Interest — Interested parties, regular updates | {{KI_COUNT}} |
| Monitor | Low Power, Low Interest — Minimal engagement, optional updates | {{M_COUNT}} |

---

## 2. Stakeholder Register

### 2.1 Manage Closely (High Power / High Interest)

| Stakeholder Name | Role | Organization | Power Level | Interest Level | Engagement Strategy | Communication Frequency | Relationship Owner | Escalation Path |
|------------------|------|--------------|-------------|----------------|---------------------|------------------------|-------------------|-----------------|
| {{NAME_1}} | {{ROLE_1}} | {{ORG_1}} | High | High | {{ENGAGEMENT_STRAT_1}} | {{COMM_FREQ_1}} | {{OWNER_1}} | {{ESCALATION_1}} |
| {{NAME_2}} | {{ROLE_2}} | {{ORG_2}} | High | High | {{ENGAGEMENT_STRAT_2}} | {{COMM_FREQ_2}} | {{OWNER_2}} | {{ESCALATION_2}} |
| {{NAME_3}} | {{ROLE_3}} | {{ORG_3}} | High | High | {{ENGAGEMENT_STRAT_3}} | {{COMM_FREQ_3}} | {{OWNER_3}} | {{ESCALATION_3}} |

### 2.2 Keep Satisfied (High Power / Low Interest)

| Stakeholder Name | Role | Organization | Power Level | Interest Level | Engagement Strategy | Communication Frequency | Relationship Owner | Escalation Path |
|------------------|------|--------------|-------------|----------------|---------------------|------------------------|-------------------|-----------------|
| {{NAME_1}} | {{ROLE_1}} | {{ORG_1}} | High | Low | {{ENGAGEMENT_STRAT_1}} | {{COMM_FREQ_1}} | {{OWNER_1}} | {{ESCALATION_1}} |
| {{NAME_2}} | {{ROLE_2}} | {{ORG_2}} | High | Low | {{ENGAGEMENT_STRAT_2}} | {{COMM_FREQ_2}} | {{OWNER_2}} | {{ESCALATION_2}} |

### 2.3 Keep Informed (Low Power / High Interest)

| Stakeholder Name | Role | Organization | Power Level | Interest Level | Engagement Strategy | Communication Frequency | Relationship Owner | Escalation Path |
|------------------|------|--------------|-------------|----------------|---------------------|------------------------|-------------------|-----------------|
| {{NAME_1}} | {{ROLE_1}} | {{ORG_1}} | Low | High | {{ENGAGEMENT_STRAT_1}} | {{COMM_FREQ_1}} | {{OWNER_1}} | {{ESCALATION_1}} |
| {{NAME_2}} | {{ROLE_2}} | {{ORG_2}} | Low | High | {{ENGAGEMENT_STRAT_2}} | {{COMM_FREQ_2}} | {{OWNER_2}} | {{ESCALATION_2}} |

### 2.4 Monitor (Low Power / Low Interest)

| Stakeholder Name | Role | Organization | Power Level | Interest Level | Engagement Strategy | Communication Frequency | Relationship Owner | Escalation Path |
|------------------|------|--------------|-------------|----------------|---------------------|------------------------|-------------------|-----------------|
| {{NAME_1}} | {{ROLE_1}} | {{ORG_1}} | Low | Low | {{ENGAGEMENT_STRAT_1}} | {{COMM_FREQ_1}} | {{OWNER_1}} | {{ESCALATION_1}} |

---

## 3. Engagement Strategy by Quadrant

### 3.1 Manage Closely
**Priority:** CRITICAL — Active engagement required

| Action | Details |
|--------|---------|
| Communication Channel | {{MC_CHANNEL}} |
| Meeting Cadence | {{MC_CADENCE}} |
| Key Topics | {{MC_TOPICS}} |
| Owner Actions | - Weekly status review with sponsor<br>- Bi-weekly executive steering committee<br>- Ad-hoc calls for key decisions |

### 3.2 Keep Satisfied
**Priority:** HIGH — Maintain satisfaction on key milestones

| Action | Details |
|--------|---------|
| Communication Channel | {{KS_CHANNEL}} |
| Meeting Cadence | {{KS_CADENCE}} |
| Key Topics | {{KS_TOPICS}} |
| Owner Actions | - Quarterly governance updates<br>- Milestone completion notifications<br>- Major decision alerts |

### 3.3 Keep Informed
**Priority:** MEDIUM — Regular information sharing

| Action | Details |
|--------|---------|
| Communication Channel | {{KI_CHANNEL}} |
| Meeting Cadence | {{KI_CADENCE}} |
| Key Topics | {{KI_TOPICS}} |
| Owner Actions | - Monthly project newsletter<br>- Dashboard access<br>- Quarterly briefing |

### 3.4 Monitor
**Priority:** LOW — Minimal engagement

| Action | Details |
|--------|---------|
| Communication Channel | {{M_CHANNEL}} |
| Meeting Cadence | {{M_CADENCE}} |
| Key Topics | {{M_TOPICS}} |
| Owner Actions | - Project webpage/dashboard (optional)<br>- End-of-project summary |

---

## 4. Stakeholder-specific Concerns and Risks

| Stakeholder | Known Concern or Risk | Mitigation Strategy | Owner | Status |
|-------------|----------------------|---------------------|-------|--------|
| {{STAKEHOLDER_1}} | {{CONCERN_1}} | {{MITIGATION_1}} | {{CONCERN_OWNER_1}} | {{STATUS_1}} |
| {{STAKEHOLDER_2}} | {{CONCERN_2}} | {{MITIGATION_2}} | {{CONCERN_OWNER_2}} | {{STATUS_2}} |

---

## 5. Communication Responsibility Matrix

| Communication Type | Audience | Channel | Frequency | Owner | Sponsor Role |
|-------------------|----------|---------|-----------|-------|--------------|
| Executive Summary | Steering Committee, Executives | Email/Portal | Monthly | {{PM_NAME}} | Approve |
| Project Status Report | Core Team, Stakeholders | PDF/Slide Deck | Bi-weekly | {{PM_NAME}} | Review |
| Milestone Update | Governance Body | Email | At milestones | {{PM_NAME}} | Acknowledge |
| Issue Escalation | Sponsor, Decision-makers | Phone/Meeting | As needed | {{PM_NAME}} | Resolve |
| Newsletter | All Stakeholders | Email | Monthly | {{PM_NAME}} | Information Only |

---

## 6. Validation and Sign-Off

**Stakeholder Analysis Reviewed By:**

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Sponsor | {{SPONSOR_NAME}} | {{SPONSOR_DATE}} | |
| Project Manager | {{PM_NAME}} | {{PM_DATE}} | |
| Subject Matter Expert | {{SME_NAME}} | {{SME_DATE}} | |

**Next Review Date:** {{NEXT_REVIEW_DATE}}
**Review Trigger:** {{REVIEW_TRIGGER}} (e.g., quarterly, after major milestone)

---

## 7. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| {{VERSION_1}} | {{DATE_1}} | {{AUTHOR_1}} | Initial stakeholder analysis |
| {{VERSION_2}} | {{DATE_2}} | {{AUTHOR_2}} | {{CHANGES_2}} |

---

*Document ID: {{DOCUMENT_ID}}*
*Last Updated: {{LAST_UPDATED}}*