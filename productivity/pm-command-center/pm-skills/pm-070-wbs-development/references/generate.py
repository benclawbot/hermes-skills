#!/usr/bin/env python3
"""Generate filled WBS document from template."""

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
        '{{PREPARED_BY}}': 'Project Management Office',
        '{{VERSION}}': '1.0',
        '{{PREFIX}}': 'ERP',
        '{{DELIVERABLE_BASED / PHASE_BASED / ORGANIZATIONAL}}': 'Deliverable-Based',
        '{{COUNT}}': '5',
        '{{PROJECT_TITLE}}': 'Enterprise ERP Implementation',
        '{{OBJECTIVE_TEXT}}': 'Implement integrated ERP system to streamline business operations and enable data-driven decision making across all departments.',
        '{{SUCCESS_CRITERIA}}': '40% reduction in manual processes, 99% data accuracy, user adoption rate >85%',
        '{{MAJOR_DELIVERABLE_NAME}}': 'Project Management & Planning',
        '{{DELIVERABLE_DESCRIPTION}}': 'All planning, governance, and management deliverables for the ERP implementation project',
        '{{ROLE/DEPARTMENT}}': 'PMO',
        '{{SUB_DELIVERABLE_NAME}}': 'Requirements Management',
        '{{DESCRIPTION}}': 'Elicitation, analysis, and documentation of all business requirements',
        '{{ROLE}}': 'Business Analyst',
        '{{DEPENDENCIES}}': 'None at start',
        '{{QUALITY_CRITERIA}}': 'Approved requirements sign-off document',
        '{{HOURS}}': '200',
        '{{WORK_PACKAGE_NAME}}': 'Stakeholder interviews and workshop facilitation',
        '{{ROLE/INDIVIDUAL}}': 'Senior Business Analyst',
        '{{LIST_DEPENDENCIES}}': 'Stakeholder calendar availability',
        '{{ACCEPTANCE_SIGN-OFF}}': 'Project Sponsor',
        '{{TEAM}}': 'Business Analysis',
        '{{NAME, TITLE}}': 'Executive Sponsor',
        '{{ADDITIONAL_NOTES}}': 'WBS to be reviewed and updated during planning phase',
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