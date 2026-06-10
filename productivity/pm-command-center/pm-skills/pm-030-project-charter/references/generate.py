#!/usr/bin/env python3
"""Generate Project Charter from template."""

import datetime
import os
import re

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.md")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "project-charter.md")

def get_date():
    return datetime.date.today().strftime("%Y-%m-%d")

def generate():
    with open(TEMPLATE_PATH, "r") as f:
        content = f.read()

    replacements = {
        "{{PROJECT_NAME}}": "Demo Project Alpha",
        "{{PROJECT_MANAGER}}": "Project Manager",
        "{{DATE}}": get_date(),
        "{{VERSION}}": "1.0",
        "{{PURPOSE}}": "This project aims to modernize internal systems to improve operational efficiency and reduce costs.",
        "{{BACKGROUND}}": "The current system is outdated and requires significant maintenance. This project will replace it with a modern solution that meets business needs.",
        "{{OBJECTIVE_1}}": "Modernize internal systems",
        "{{DESCRIPTION_1}}": "Replace legacy systems with modern, scalable solutions",
        "{{SUCCESS_CRITERIA_1}}": "System operational by Q4 2026",
        "{{OBJECTIVE_2}}": "Reduce operational costs",
        "{{DESCRIPTION_2}}": "Achieve 20% cost reduction through automation",
        "{{SUCCESS_CRITERIA_2}}": "Cost savings realized within 12 months",
        "{{OBJECTIVE_3}}": "Improve data accessibility",
        "{{DESCRIPTION_3}}": "Enable real-time data access for stakeholders",
        "{{SUCCESS_CRITERIA_3}}": "Dashboard available within 3 months",
        "{{IN_SCOPE_1}}": "Core system development",
        "{{IN_SCOPE_2}}": "Data migration",
        "{{IN_SCOPE_3}}": "User training",
        "{{OUT_OF_SCOPE_1}}": "Hardware procurement",
        "{{OUT_OF_SCOPE_2}}": "Third-party integrations (Phase 2)",
        "{{DELIVERABLE_1}}": "Modernized platform",
        "{{DELIVERABLE_DESC_1}}": "Production-ready system with all core features",
        "{{DELIVERABLE_DUE_1}}": "2026-09-01",
        "{{DELIVERABLE_2}}": "Documentation",
        "{{DELIVERABLE_DESC_2}}": "Complete user and technical documentation",
        "{{DELIVERABLE_DUE_2}}": "2026-08-15",
        "{{DELIVERABLE_3}}": "Training materials",
        "{{DELIVERABLE_DESC_3}}": "End-user training guides and sessions",
        "{{DELIVERABLE_DUE_3}}": "2026-08-20",
        "{{MILESTONE_1}}": "Requirements complete",
        "{{MILESTONE_DATE_1}}": "2026-05-30",
        "{{MILESTONE_STATUS_1}}": "In Progress",
        "{{MILESTONE_2}}": "Design approved",
        "{{MILESTONE_DATE_2}}": "2026-06-20",
        "{{MILESTONE_STATUS_2}}": "Pending",
        "{{MILESTONE_3}}": "Development complete",
        "{{MILESTONE_DATE_3}}": "2026-08-15",
        "{{MILESTONE_STATUS_3}}": "Pending",
        "{{MILESTONE_4}}": "Go-Live",
        "{{MILESTONE_DATE_4}}": "2026-09-01",
        "{{MILESTONE_STATUS_4}}": "Pending",
        "{{BUDGET_CATEGORY_1}}": "Software Development",
        "{{BUDGET_AMOUNT_1}}": "$50,000",
        "{{BUDGET_CATEGORY_2}}": "Infrastructure",
        "{{BUDGET_AMOUNT_2}}": "$20,000",
        "{{BUDGET_CATEGORY_3}}": "Training",
        "{{BUDGET_AMOUNT_3}}": "$10,000",
        "{{BUDGET_TOTAL}}": "$80,000",
        "{{RISK_1}}": "Resource availability",
        "{{RISK_IMPACT_1}}": "High",
        "{{RISK_LIKELIHOOD_1}}": "Medium",
        "{{RISK_MITIGATION_1}}": "Cross-train team members",
        "{{RISK_2}}": "Scope creep",
        "{{RISK_IMPACT_2}}": "Medium",
        "{{RISK_LIKELIHOOD_2}}": "Medium",
        "{{RISK_MITIGATION_2}}": "Strict change control process",
        "{{STAKEHOLDER_1}}": "Executive Sponsor",
        "{{STAKEHOLDER_ROLE_1}}": "Approver",
        "{{STAKEHOLDER_INTEREST_1}}": "High",
        "{{STAKEHOLDER_INFLUENCE_1}}": "High",
        "{{STAKEHOLDER_2}}": "Business Unit Director",
        "{{STAKEHOLDER_ROLE_2}}": "User",
        "{{STAKEHOLDER_INTEREST_2}}": "High",
        "{{STAKEHOLDER_INFLUENCE_2}}": "Medium",
        "{{STAKEHOLDER_3}}": "IT Director",
        "{{STAKEHOLDER_ROLE_3}}": "Technical Owner",
        "{{STAKEHOLDER_INTEREST_3}}": "Medium",
        "{{STAKEHOLDER_INFLUENCE_3}}": "High",
        "{{APPROVAL_ROLE_1}}": "Project Sponsor",
        "{{APPROVAL_NAME_1}}": "Executive Sponsor",
        "{{APPROVAL_SIGNATURE_1}}": "",
        "{{APPROVAL_DATE_1}}": get_date(),
        "{{APPROVAL_ROLE_2}}": "Project Manager",
        "{{APPROVAL_NAME_2}}": "Project Manager",
        "{{APPROVAL_SIGNATURE_2}}": "",
        "{{APPROVAL_DATE_2}}": get_date(),
    }

    for key, value in replacements.items():
        content = content.replace(key, value)

    with open(OUTPUT_PATH, "w") as f:
        f.write(content)

    print(f"Generated: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate()