# PM-150: Quality Planning Template

## Overview
This template defines quality standards, metrics, and acceptance criteria for the project.

## Quality Standards

| Standard | Description | Target | Measurement Method |
|----------|-------------|--------|-------------------|
| Code Coverage | % of code covered by tests | 80% | Automated testing |
| Defect Density | Bugs per 1000 lines of code | < 5 | Static analysis |
| Response Time | System response under load | < 200ms | Performance testing |
| Accessibility | WCAG compliance level | AA | Audit tools |
| Documentation | % of features documented | 100% | Review checklist |

## QA Methods

### Unit Testing
- Framework: [Jest/PyTest/etc]
- Minimum coverage: 80%
- Run frequency: Every commit

### Integration Testing
- Environment: Staging
- Trigger: Nightly builds
- Approval: QA lead sign-off

### User Acceptance Testing (UAT)
- Participants: Business users
- Sign-off required: Yes
- Documentation: Test scripts and results

## Acceptance Criteria Template

| Feature | Given | When | Then | Verified By |
|---------|-------|------|------|-------------|
| Login | User is on login page | Credentials entered | Redirect to dashboard | QA |
| Search | Results exist | Search executed | Display relevant results | QA |

## Sign-off Requirements

| Deliverable | Required Sign-off | Approver | Deadline |
|-------------|-------------------|----------|----------|
| Requirements Doc | Initial | BA Lead | |
| Design Spec | Initial | Tech Lead | |
| Sprint Demo | Each sprint | Product Owner | |
| Final Release | Go-live | Sponsor | |

---
*Template Version: 1.0 | Last Updated: 2026-05-20*