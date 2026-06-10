#!/usr/bin/env python3
"""Generate filled Requirements Elicitation document from template."""

import os
import sys
from datetime import datetime

TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), 'template.md')

def get_date():
    return datetime.now().strftime("%Y-%m-%d")

def generate():
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Error: Template not found at {TEMPLATE_FILE}")
        sys.exit(1)
    
    with open(TEMPLATE_FILE, 'r') as f:
        content = f.read()
    
    # Replace placeholders
    replacements = {
        '{{PROJECT_NAME}}': 'Enterprise ERP Implementation',
        '{{DATE}}': get_date(),
        '{{PREPARED_BY}}': 'Business Analysis Team',
        '{{VERSION}}': '1.0',
        '{{INTERVIEW / WORKSHOP / JAD / DOCUMENT_ANALYSIS / OBSERVATION}}': 'Workshop',
        '{{FACILITATOR_NAME}}': 'John Chen',
        '{{NOTE_TAKER}}': 'Maria Garcia',
        '{{LOCATION_OR_VIDEO_LINK}}': 'Microsoft Teams',
        '{{NAME}}': 'Department Head',
        '{{ROLE}}': 'Sponsor',
        '{{DEPT}}': 'Executive',
        '{{H/M/L}}': 'H',
        '{{PRIMARY / SECONDARY / TERTIARY}}': 'Primary',
        '{{WHAT_YOU_WANT_TO_ACHIEVE}}': 'Gather comprehensive business requirements for ERP implementation including finance, HR, supply chain, and customer management modules.',
        '{{OPENING_QUESTION_1}}': 'What are the current pain points in your department?',
        '{{OPENING_QUESTION_2}}': 'What success looks like for this initiative?',
        '{{DISCOVERY_QUESTION_1}}': 'What features are essential for daily operations?',
        '{{DISCOVERY_QUESTION_2}}': 'What integrations are required with existing systems?',
        '{{DISCOVERY_QUESTION_3}}': 'What reports and dashboards are needed?',
        '{{CONSTRAINT_QUESTION_1}}': 'What budget or timeline constraints exist?',
        '{{CONSTRAINT_QUESTION_2}}': 'What technical limitations should we be aware of?',
        '{{WRAP_UP_QUESTION_1}}': 'Any other stakeholders we should interview?',
        '{{WRAP_UP_QUESTION_2}}': 'What next steps would you recommend?',
        '{{OUT_OF_SCOPE_ITEM_1}}': 'Mobile app development (Phase 2)',
        '{{OUT_OF_SCOPE_ITEM_2}}': 'Advanced AI/ML features (Future roadmap)',
        '{{STAKEHOLDER_NAME}}': 'Executive Steering Committee',
        '{{QUOTE_1}}': 'We need a system that can scale with our growth plans.',
        '{{QUOTE_2}}': 'Data integration across departments is our top priority.',
        '{{REQ_PARAPHRASED_1}}': 'System must support 500+ concurrent users during peak hours',
        '{{REQ_PARAPHRASED_2}}': 'Integration with legacy database required for 3 years migration period',
        '{{OWNER}}': 'Business Analyst',
        '{{QUESTION}}': 'What is the approval timeline for requirement sign-off?',
        '{{REQUIREMENT_TEXT}}': 'Real-time inventory tracking across all warehouse locations',
        '{{ACCEPTANCE_CRITERIA}}': 'Inventory accuracy within 99.5% within 24-hour sync cycle',
        '{{Must/Should/Could/Won\'t}}': 'Must',
        '{{Draft/Confirmed/Approved}}': 'Draft',
        '{{NOTES}}': 'Pending vendor demos to confirm feasibility',
        '{{OBJECTIVE}}': 'Enable data-driven decision making',
        '{{WBS_CODE}}': '1.1.2',
        '{{COUNT}}': '45',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Output to references folder as output.md
    output_path = os.path.join(os.path.dirname(__file__), 'output.md')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    generate()