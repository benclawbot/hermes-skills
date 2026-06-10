---
name: pm-270-project-archiving
description: Archive all project records, artifacts, and documentation into the official organizational repository with proper retention and access controls.
triggers:
  - "How do we archive project files?"
  - "Project records retention"
  - "Where do project documents go after closure?"
  - "Project documentation storage"
  - "Closing out project files"
tags:
  - tier-1
  - closure
  - documentation
  - records-management
  - retention
  - governance
category: pm
---

# PM-270: Project Archiving

Project Archiving is a Tier 1 closure activity that consolidates all project records, artifacts, and documentation into the official organizational repository with proper indexing, retention schedules, and access controls.

---

## What Is Project Archiving?

The systematic process of:
1. Identifying all project artifacts and records
2. Confirming completeness and accuracy before archiving
3. Classifying records by type and retention period
4. Transferring records to the official repository
5. Setting access controls and retention schedules
6. Maintaining an index so records can be retrieved

---

## Prerequisites

Before archiving begins:
```
□ All project deliverables accepted
□ Closure Report approved
□ Team demobilization completed or nearing completion
□ All stakeholder communications concluded
□ No active legal hold on project records
□ Retention policy confirmed for all record types
```

---

## Step-by-Step: Archive Project Records

### Step 1: Identify All Artifacts

Create a comprehensive inventory of project records:

```
1. Project Charter and foundational documents
2. Plans (schedule, cost, quality, risk, communication, procurement)
3. WBS and dictionary
4. Requirements and specifications
5. Design documents and drawings
6. Test plans and test results
7. Meeting minutes and decisions
8. Status reports (all periods)
9. Change requests and change log
10. Issue log and risk register
11. Financial records (invoices, receipts, budget tracking)
12. Contracts and procurement documents
13. Stakeholder register and communications
14. Lessons learned documentation
15. Closure report
16. Acceptance sign-offs
17. Training materials and user guides
18. Software, models, and code (if applicable)
19. Media files (photos, videos from project events)
20. Correspondence (email threads, letters)
```

### Step 2: Classify Records by Retention Category

| Record Type | Typical Retention | Rationale |
|-------------|-------------------|-----------|
| Financial records | 7 years | Tax, audit, legal requirements |
| Contracts | Contract term + 5 years | Legal reference |
| Acceptance documents | Project life + 3 years | Dispute resolution |
| Technical documentation | Permanent or project life + 10 years | Knowledge retention |
| HR/personnel records | Employment + 5 years | Employment law |
| Project Charter/closure | Permanent | Governance evidence |
| Status reports | 3-5 years | Historical reference |
| Meeting minutes | 3 years | Decision traceability |
| Risk/issue logs | 3 years | Lessons learned |
| Lessons learned | Permanent | Organizational learning |

> **Note:** Retention periods vary by jurisdiction and industry — confirm with Legal/Compliance before setting.

### Step 3: Prepare Records for Archive

```
□ Remove duplicates and redundant copies
□ Verify file naming conventions (use organizational standard)
□ Organize into logical folder structure
□ Confirm all documents have appropriate metadata:
  - Project name and ID
  - Document type
  - Author
  - Date created
  - Version number
  - Status (final/draft)
□ Convert to standard format if required (PDF/A for long-term storage)
□ Scan physical documents to digital if no digital original exists
□ Verify no sensitive personal data (PII) remains in records
□ Check for any legal holds or confidentiality markings
```

### Step 4: Transfer to Official Repository

```
□ Identify the correct repository/filing system for each record type
□ Apply organizational naming conventions
□ Set folder hierarchy: [Year] / [Project ID] / [Document Type]
□ Verify write access during transfer (do not archive with open edits)
□ Perform checksum/hash verification for critical documents
□ Confirm all files transferred successfully (no corruption)
□ Create backup copy if repository does not auto-backup
```

### Step 5: Set Access Controls

```
□ Define who can access archived records:
  - Project Manager (read/write)
  - Sponsor (read)
  - Auditors (read, time-limited)
  - Operations/maintenance (read)
□ Restrict modification rights (archived records = immutable)
□ Document access request procedure for future retrieval
□ Assign an archive owner (project manager or records manager)
```

### Step 6: Create the Archive Index

```
Archive Index should include:
- Project name and ID
- Project manager
- Closure date
- Total record volume (GB/pages)
- Retention period applied
- Repository location/URL
- Access contact
- Brief description of contents by folder
- Any restrictions or special handling notes
```

---

## Archive Index Template

```
════════════════════════════════════════════════════
          PROJECT ARCHIVE INDEX
════════════════════════════════════════════════════
Project Name:    [Name]
Project ID:      [ID]
Archive Date:    [YYYY-MM-DD]
Archived By:    [Name]
Repository:     [URL or File Path]

RETENTION SUMMARY
────────────────────────────────────────────────────
Financial Records:  Retain until [Date] | Location: [path]
Contracts:          Retain until [Date] | Location: [path]
Technical Docs:     Retain until [Date] | Location: [path]
General Project:    Retain until [Date] | Location: [path]

FOLDER CONTENTS
────────────────────────────────────────────────────
/Project Charter          — Original charter, amendments
/Plans                    — All project plans (final versions)
/WBS                      — WBS and dictionary
/Requirements             — Business and technical requirements
/Design                   — Design documents and diagrams
/Test                     — Test plans, cases, results
/Schedule                 — Baselines, schedule versions
/Cost                     — Budgets, invoices, expenditure reports
/Risk                     — Risk register (all versions)
/Issues                   — Issue log (all versions)
/Changes                  — Change requests and approvals
/Contracts                — SOWs, vendor contracts, POs
/Comms                    — Stakeholder communications, presentations
/Status                   — All status reports
/Closure                  — Closure report, acceptance sign-offs
/Lessons                  — Lessons learned documentation
/KT                       — Knowledge transfer materials
/UserDocs                 — End user guides, training materials

ACCESS CONTROLS
────────────────────────────────────────────────────
Default Access: [Organization unit or role]
Restricted Items: [List any confidential items and access requirements]
Retrieval Contact: [Name/Role] | [Email/Phone]

TOTAL SIZE: [X GB] | Total Files: [N] | Total Pages (scanned): [M]
════════════════════════════════════════════════════
```

---

## Common Pitfalls

- **Archiving incomplete records** — future audits or disputes reveal gaps
- **Not converting to PDF/A** — proprietary formats become unreadable over time
- **Missing retention policy alignment** — archiving too short = legal risk, too long = cost
- **Storing on personal drives or local folders** — not accessible to future teams
- **Forgetting passwords/credentials in archived files** — document separately in secure vault
- **Not updating the project register** — the archive exists but nobody knows where
- **Physical records not scanned** — fire/flood destroys original evidence

---

## Verification Steps

```
1. Confirm all planned record categories are present (use folder checklist)
2. Spot-check files for readability (open 3-5 files per category)
3. Verify naming conventions are consistent throughout
4. Confirm access controls are applied (attempt unauthorized access — should fail)
5. Cross-check archive index against repository to confirm all listed items exist
6. Verify backup copy exists if repository does not auto-backup
7. Confirm project is removed from active project registers/portals
8. Confirm records retention periods are documented per category
```

---

## Related Skills

- pm-250-project-closure-report: Closure report is archived as key artifact
- pm-260-team-demobilization: Team members often hold records needing archival
- pm-280-lessons-learned: Lessons learned document is archived for organizational learning
- pm-290-status-reporting: All status reports are archived
- pm-120-risk-identification: Risk register is archived for future project reference
