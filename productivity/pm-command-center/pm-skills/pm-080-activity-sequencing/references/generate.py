#!/usr/bin/env python3
"""Generate filled Activity Sequencing document from template."""

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
        '{{ACTIVITY_NAME}}': 'Requirements Documentation',
        '{{WBS_CODE}}': '1.1.2',
        '{{DESCRIPTION}}': 'Document all business requirements for ERP system',
        '{{ROLE}}': 'Business Analyst',
        '{{DAYS}}': '5',
        '{{NAME}}': 'Requirements Documentation',
        '{{FS/SS/FF/SF}}': 'FS',
        '{{LEAD_LAG}}': '+2 days lead',
        '{{NOTES}}': 'Predecessor must be completed before start',
        '{{ES}}': '0',
        '{{EF}}': '5',
        '{{LS}}': '0',
        '{{LF}}': '5',
        '{{FLOAT}}': '0',
        '{{Y/N}}': 'Y',
        '{{MILESTONE_NAME}}': 'Requirements Sign-off',
        '{{ASSUMPTION_1}}': 'All required stakeholders available for review',
        '{{ASSUMPTION_2}}': 'No scope changes during sequencing',
        '{{DESCRIBE_IMPACT}}': 'May require fast-tracking or additional resources',
        '{{DEPENDENCY_DESCRIPTION}}': 'External vendor delivers third-party integration',
        '{{ADDITIONAL_NOTES}}': 'Critical path reviewed and approved by PMO',
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