#!/usr/bin/env python3
"""Generate Feasibility Study Report from template."""

import datetime
import os
import re

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.md")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "feasibility-study-report.md")

def get_date():
    return datetime.date.today().strftime("%Y-%m-%d")

def generate():
    with open(TEMPLATE_PATH, "r") as f:
        content = f.read()

    replacements = {
        "{{PROJECT_NAME}}": "Demo Project Alpha",
        "{{DOCUMENT_VERSION}}": "1.0",
        "{{REPORT_DATE}}": get_date(),
        "{{PREPARED_BY}}": "Project Manager",
        "{{PREPARED_BY_ROLE}}": "Senior Project Manager",
        "{{PROJECT_OVERVIEW_SUMMARY}}": "This project aims to modernize internal systems to improve efficiency and reduce operational costs.",
        "{{TECH_MATURITY_RATING}}": "🟢 Green",
        "{{TECH_MATURITY_NOTES}}": "Technology is mature and well-supported",
        "{{ARCH_FIT_RATING}}": "🟢 Green",
        "{{ARCH_FIT_NOTES}}": "Architecture aligns with enterprise standards",
        "{{INTEGRATION_COMPLEXITY_RATING}}": "🟡 Amber",
        "{{INTEGRATION_COMPLEXITY_NOTES}}": "Some complexity with legacy systems",
        "{{INTERNAL_CAPABILITY_RATING}}": "🟢 Green",
        "{{INTERNAL_CAPABILITY_NOTES}}": "Team has relevant experience",
        "{{TECH_GAP_1}}": "Legacy API integration",
        "{{IMPACT_1}}": "Medium",
        "{{OWNER_1}}": "Technical Lead",
        "{{TARGET_DATE_1}}": "2026-06-15",
        "{{TECH_GAP_2}}": "",
        "{{IMPACT_2}}": "",
        "{{OWNER_2}}": "",
        "{{TARGET_DATE_2}}": "",
        "{{TECH_GAP_3}}": "",
        "{{IMPACT_3}}": "",
        "{{OWNER_3}}": "",
        "{{TARGET_DATE_3}}": "",
        "{{TECH_RISK_1}}": "Data migration delays",
        "{{LIKELIHOOD_1}}": "Medium",
        "{{IMPACT_RISK_1}}": "High",
        "{{MITIGATION_1}}": "Phased migration with rollback plan",
        "{{TECH_RISK_2}}": "",
        "{{LIKELIHOOD_2}}": "",
        "{{IMPACT_RISK_2}}": "",
        "{{MITIGATION_2}}": "",
        "{{CAPEX_LOW}}": "$50,000",
        "{{CAPEX_HIGH}}": "$75,000",
        "{{CAPEX_NOTES}}": "Hardware and software licenses",
        "{{OPEX_Y1_LOW}}": "$25,000",
        "{{OPEX_Y1_HIGH}}": "$35,000",
        "{{OPEX_Y1_NOTES}}": "Year 1 operational costs",
        "{{OPEX_ONGOING_LOW}}": "$15,000",
        "{{OPEX_ONGOING_HIGH}}": "$20,000",
        "{{OPEX_ONGOING_NOTES}}": "Annual maintenance",
        "{{TCO_LOW}}": "$90,000",
        "{{TCO_HIGH}}": "$130,000",
        "{{BENEFIT_1}}": "Operational efficiency gains",
        "{{VALUE_TYPE_1}}": "Cost reduction",
        "{{ESTIMATED_VALUE_1}}": "$40,000/year",
        "{{BENEFIT_TIMING_1}}": "Year 2 onwards",
        "{{BENEFIT_2}}": "Reduced manual work",
        "{{VALUE_TYPE_2}}": "Labor savings",
        "{{ESTIMATED_VALUE_2}}": "20 hours/week",
        "{{BENEFIT_TIMING_2}}": "Year 1",
        "{{PRELIMINARY_ROI}}": "45",
        "{{ROI_NOTES}}": "Based on conservative estimates",
        "{{PAYBACK_PERIOD}}": "18",
        "{{PAYBACK_NOTES}}": "Within project threshold",
        "{{NPV_INDICATIVE}}": "$35,000",
        "{{NPV_NOTES}}": "10-year projection",
        "{{IRR_INDICATIVE}}": "22",
        "{{IRR_NOTES}}": "Above cost of capital",
        "{{LICENSE_STATUS}}": "Compliant",
        "{{LICENSE_DETAILS}}": "All required licenses identified",
        "{{PRIVACY_STATUS}}": "Compliant",
        "{{PRIVACY_DETAILS}}": "GDPR assessment completed",
        "{{IP_STATUS}}": "Compliant",
        "{{IP_DETAILS}}": "No IP concerns identified",
        "{{CONTRACT_STATUS}}": "Review required",
        "{{CONTRACT_DETAILS}}": "Vendor contracts under review",
        "{{REGULATORY_STATUS}}": "Compliant",
        "{{REGULATORY_DETAILS}}": "No regulatory approvals needed",
        "{{LEGAL_OPEN_ITEM_1}}": "Vendor contract negotiation",
        "{{LEGAL_OWNER_1}}": "Legal Counsel",
        "{{LEGAL_RESOLUTION_DATE_1}}": "2026-06-01",
        "{{PROCESS_FIT_RATING}}": "🟢 Green",
        "{{PROCESS_FIT_NOTES}}": "Fits current processes",
        "{{CM_IMPACT_RATING}}": "🟡 Amber",
        "{{CM_IMPACT_NOTES}}": "Training required for adoption",
        "{{TRAINING_NEEDS_RATING}}": "🟡 Amber",
        "{{TRAINING_NEEDS_NOTES}}": "2-day training program planned",
        "{{ORG_READINESS_RATING}}": "🟢 Green",
        "{{ORG_READINESS_NOTES}}": "Stakeholder support confirmed",
        "{{PROCESS_OWNER_NAME}}": "Operations Manager",
        "{{PROCESS_OWNER_COMMITMENT}}": "Confirmed",
        "{{OPS_LEAD_NAME}}": "Operations Lead",
        "{{OPS_LEAD_COMMITMENT}}": "Confirmed",
        "{{MILESTONE_1}}": "Requirements definition",
        "{{MILESTONE_1_DATE}}": "2026-05-30",
        "{{MILESTONE_1_FEASIBILITY}}": "🟢 Green",
        "{{MILESTONE_2}}": "Design completion",
        "{{MILESTONE_2_DATE}}": "2026-06-30",
        "{{MILESTONE_2_FEASIBILITY}}": "🟢 Green",
        "{{MILESTONE_3}}": "Development complete",
        "{{MILESTONE_3_DATE}}": "2026-08-15",
        "{{MILESTONE_3_FEASIBILITY}}": "🟡 Amber",
        "{{GO_LIVE_DATE}}": "2026-09-01",
        "{{GO_LIVE_FEASIBILITY}}": "🟢 Green",
        "{{SCHEDULE_RISK_1}}": "Resource availability",
        "{{SCHEDULE_RISK_1_IMPACT}}": "Medium",
        "{{SCHEDULE_RISK_1_MITIGATION}}": "Cross-training and backup resources",
        "{{RESOURCE_CONSTRAINTS_NOTES}}": "No major constraints identified. Team capacity confirmed.",
        "{{TECH_SCORE}}": "🟢 Green",
        "{{TECH_FINDING}}": "Technically feasible with minor risks",
        "{{ECON_SCORE}}": "🟢 Green",
        "{{ECON_FINDING}}": "Economically viable with positive ROI",
        "{{LEGAL_SCORE}}": "🟡 Amber",
        "{{LEGAL_FINDING}}": "Compliant with minor open items",
        "{{OPS_SCORE}}": "🟢 Green",
        "{{OPS_FINDING}}": "Operationally feasible with training",
        "{{SCHEDULE_SCORE}}": "🟢 Green",
        "{{SCHEDULE_FINDING}}": "Schedule is realistic",
        "{{SHOWSTOPPERS_DESCRIPTION}}": "No showstoppers identified",
        "{{CONDITION_1}}": "Complete vendor contract review",
        "{{CONDITION_OWNER_1}}": "Legal Counsel",
        "{{CONDITION_DUE_DATE_1}}": "2026-06-01",
        "{{CONDITION_2}}": "",
        "{{CONDITION_OWNER_2}}": "",
        "{{CONDITION_DUE_DATE_2}}": "",
        "{{RECOMMENDATION_RATIONALE}}": "Project meets all key criteria and is recommended to proceed to chartering phase.",
        "{{SPONSOR_NAME}}": "Executive Sponsor",
        "{{SPONSOR_DATE}}": get_date(),
        "{{PM_NAME}}": "Project Manager",
        "{{PM_DATE}}": get_date(),
        "{{TECH_LEAD_NAME}}": "Technical Lead",
        "{{TECH_LEAD_DATE}}": get_date(),
        "{{ASSUMPTION_1}}": "Budget will be approved as proposed",
        "{{ASSUMPTION_OWNER_1}}": "Finance",
        "{{ASSUMPTION_REVIEW_DATE_1}}": "2026-06-15",
        "{{ASSUMPTION_2}}": "Resources will be available as planned",
        "{{ASSUMPTION_OWNER_2}}": "Project Manager",
        "{{ASSUMPTION_REVIEW_DATE_2}}": "2026-06-01",
        "{{OPEN_ITEM_1}}": "Finalize vendor contracts",
        "{{OPEN_ITEM_OWNER_1}}": "Legal",
        "{{OPEN_ITEM_TARGET_DATE_1}}": "2026-06-01",
        "{{DOCUMENT_ID}}": "FS-2026-001",
        "{{LAST_UPDATED}}": get_date(),
    }

    for key, value in replacements.items():
        content = content.replace(key, value)

    # Remove empty table rows (| | |)
    content = re.sub(r'\|\s*\|\s*\|\s*\n', '', content)

    with open(OUTPUT_PATH, "w") as f:
        f.write(content)

    print(f"Generated: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate()