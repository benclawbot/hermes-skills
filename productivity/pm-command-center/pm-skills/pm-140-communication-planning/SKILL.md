---
name: pm-140-communication-planning
description: Plan and document project communication — channels, cadence, audiences, and formats. Tier 2 PM skill.
triggers:
  - "communication plan"
  - "stakeholder communication"
  - "project status"
  - "reporting"
  - "pm-140"
steps:
  - Identify all stakeholders from the stakeholder register or RACI matrix.
  - For each stakeholder/stakeholder group: determine information needs, preferred format, frequency, and channel.
  - Define communication types: Status Reports, Steering Committee Updates, Risk Alerts, Change Notifications, Meeting Notes, Ad-hoc.
  - Set cadence: Daily (standups), Weekly (status), Bi-weekly (sprint review), Monthly (executive), Quarterly (strategic).
  - Document in a communication-plan.md file with: Stakeholder | Information | Format | Frequency | Channel | Owner.
  - Identify communication risks: information asymmetry, overload, channels going dark, sensitive information handling.
  - Create a communications calendar or reference it in the plan.
  - Validate with project sponsor and key stakeholders.
verification:
  - All identified stakeholders appear in the communication plan.
  - Each stakeholder has at least one communication entry (type, frequency, format).
  - Plan is approved by the project sponsor.
pitfalls:
  - Do not over-communicate — align frequency to stakeholder needs, not your anxiety.
  - Do not skip the "channel" column — email vs. meeting vs. Slack have very different effects.
  - Escalation paths must be documented, not assumed.
  - Include NDA/confidentiality handling for sensitive communications.
examples:
  - "Executive sponsor: Monthly PDF dashboard + 30-min video call — channel: email + Zoom."
  - "Development team: Daily standup notes in Slack — channel: #project-standup."
  - "External regulator: Ad-hoc compliance reports on request — channel: secure portal."
---
# Communication Planning — pm-140

## Standard Communication Types
| Type | Audience | Frequency | Format | Channel |
|---|---|---|---|---|
| Status Report | Project Sponsor, PMO | Weekly | PDF/HTML | Email |
| Steering Committee | Executives | Monthly | Slide deck | In-person/Zoom |
| Risk Alert | PM, Sponsor | As needed | Memo | Email + Call |
| Change Notice | All stakeholders | As needed | RFC document | Email + Meeting |
| Sprint Review | Dev + Product | Bi-weekly | Demo + notes | Confluence/Jira |
| Meeting Minutes | Attendees + PM | After each meeting | Notes doc | Email |

## Communication Principles
1. **Right information, right person, right time** — match content to audience needs.
2. **Escalate early** — bad news travels faster than good news; surface risks proactively.
3. **Document everything** — decisions without minutes are rumors.
4. **One source of truth** — use a single project portal/channel for status, not scattered emails.
