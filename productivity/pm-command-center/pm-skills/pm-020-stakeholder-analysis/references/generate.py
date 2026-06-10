#!/usr/bin/env python3
"""Generate Stakeholder Analysis Register from template."""

import datetime
import os
import re

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.md")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "stakeholder-analysis-register.md")

def get_date():
    return datetime.date.today().strftime("%Y-%m-%d")

def generate():
    with open(TEMPLATE_PATH, "r") as f:
        content = f.read()

    replacements = {
        "{{PROJECT_NAME}}": "Demo Project Alpha",
        "{{ANALYSIS_DATE}}": get_date(),
        "{{ANALYST_NAME}}": "Project Manager",
        "{{DOCUMENT_VERSION}}": "1.0",
        "{{MC_COUNT}}": "3",
        "{{KS_COUNT}}": "2",
        "{{KI_COUNT}}": "3",
        "{{M_COUNT}}": "2",
        # Manage Closely (High Power, High Interest)
        "{{NAME_1}}": "Executive Sponsor",
        "{{ROLE_1}}": "Project Sponsor",
        "{{ORG_1}}": "Executive Team",
        "{{ENGAGEMENT_STRAT_1}}": "Weekly updates, direct escalation",
        "{{COMM_FREQ_1}}": "Weekly",
        "{{OWNER_1}}": "Project Manager",
        "{{ESCALATION_1}}": "Steering Committee",
        "{{NAME_2}}": "Business Unit Director",
        "{{ROLE_2}}": "Business Owner",
        "{{ORG_2}}": "Operations",
        "{{ENGAGEMENT_STRAT_2}}": "Bi-weekly reviews",
        "{{COMM_FREQ_2}}": "Bi-weekly",
        "{{OWNER_2}}": "Project Manager",
        "{{ESCALATION_2}}": "Steering Committee",
        "{{NAME_3}}": "IT Director",
        "{{ROLE_3}}": "Technical Owner",
        "{{ORG_3}}": "IT",
        "{{ENGAGEMENT_STRAT_3}}": "Weekly technical sync",
        "{{COMM_FREQ_3}}": "Weekly",
        "{{OWNER_3}}": "Technical Lead",
        "{{ESCALATION_3}}": "Project Manager",
        # Keep Satisfied (High Power, Low Interest)
        "{{NAME_1}}": "CFO",
        "{{ROLE_1}}": "Finance Approver",
        "{{ORG_1}}": "Finance",
        "{{ENGAGEMENT_STRAT_1}}": "Quarterly updates",
        "{{COMM_FREQ_1}}": "Quarterly",
        "{{OWNER_1}}": "Project Manager",
        "{{ESCALATION_1}}": "Executive Sponsor",
        "{{NAME_2}}": "Legal Counsel",
        "{{ROLE_2}}": "Compliance",
        "{{ORG_2}}": "Legal",
        "{{ENGAGEMENT_STRAT_2}}": "Milestone updates",
        "{{COMM_FREQ_2}}": "As needed",
        "{{OWNER_2}}": "Project Manager",
        "{{ESCALATION_2}}": "Executive Sponsor",
        # Keep Informed (Low Power, High Interest)
        "{{NAME_1}}": "Team Lead",
        "{{ROLE_1}}": "End User Representative",
        "{{ORG_1}}": "Operations",
        "{{ENGAGEMENT_STRAT_1}}": "Monthly newsletter",
        "{{COMM_FREQ_1}}": "Monthly",
        "{{OWNER_1}}": "Project Manager",
        "{{ESCALATION_1}}": "Business Unit Director",
        "{{NAME_2}}": "QA Manager",
        "{{ROLE_2}}": "Quality Assurance",
        "{{ORG_2}}": "Quality",
        "{{ENGAGEMENT_STRAT_2}}": "Bi-weekly updates",
        "{{COMM_FREQ_2}}": "Bi-weekly",
        "{{OWNER_2}}": "Technical Lead",
        "{{ESCALATION_2}}": "IT Director",
        # Monitor (Low Power, Low Interest)
        "{{NAME_1}}": "External Auditor",
        "{{ROLE_1}}": "Audit",
        "{{ORG_1}}": "External",
        "{{ENGAGEMENT_STRAT_1}}": "End-of-project summary",
        "{{COMM_FREQ_1}}": "As needed",
        "{{OWNER_1}}": "Project Manager",
        "{{ESCALATION_1}}": "Project Manager",
        "{{MC_CHANNEL}}": "Weekly steering committee meetings",
        "{{MC_CADENCE}}": "Weekly",
        "{{MC_TOPICS}}": "Status, risks, decisions, budget",
        "{{KS_CHANNEL}}": "Quarterly governance reports",
        "{{KS_CADENCE}}": "Quarterly",
        "{{KS_TOPICS}}": "Milestone status, budget",
        "{{KI_CHANNEL}}": "Monthly project newsletter",
        "{{KI_CADENCE}}": "Monthly",
        "{{KI_TOPICS}}": "Progress, achievements",
        "{{M_CHANNEL}}": "Dashboard (optional)",
        "{{M_CADENCE}}": "Quarterly",
        "{{M_TOPICS}}": "Project completion summary",
        "{{STAKEHOLDER_1}}": "CFO",
        "{{CONCERN_1}}": "Budget overruns",
        "{{MITIGATION_1}}": "Monthly budget tracking and reporting",
        "{{CONCERN_OWNER_1}}": "Project Manager",
        "{{STATUS_1}}": "Mitigated",
        "{{STAKEHOLDER_2}}": "IT Director",
        "{{CONCERN_2}}": "Integration complexity",
        "{{MITIGATION_2}}": "Phased approach with testing phases",
        "{{CONCERN_OWNER_2}}": "Technical Lead",
        "{{STATUS_2}}": "Mitigated",
        "{{PM_NAME}}": "Project Manager",
        "{{SPONSOR_NAME}}": "Executive Sponsor",
        "{{SPONSOR_DATE}}": get_date(),
        "{{PM_DATE}}": get_date(),
        "{{SME_NAME}}": "Subject Matter Expert",
        "{{SME_DATE}}": get_date(),
        "{{NEXT_REVIEW_DATE}}": "2026-07-20",
        "{{REVIEW_TRIGGER}}": "Quarterly or after major milestone",
        "{{VERSION_1}}": "1.0",
        "{{DATE_1}}": get_date(),
        "{{AUTHOR_1}}": "Project Manager",
        "{{VERSION_2}}": "",
        "{{DATE_2}}": "",
        "{{AUTHOR_2}}": "",
        "{{CHANGES_2}}": "",
        "{{DOCUMENT_ID}}": "SA-2026-001",
        "{{LAST_UPDATED}}": get_date(),
    }

    for key, value in replacements.items():
        content = content.replace(key, value)

    # Remove empty table rows
    content = re.sub(r'\|\s*\|\s*\|\s*\n', '', content)

    with open(OUTPUT_PATH, "w") as f:
        f.write(content)

    print(f"Generated: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate()