#!/usr/bin/env python3
"""Generate filled RACI Matrix document from template."""

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
        '{{COUNT}}': '8',
        '{{NAME}}': 'TBD',
        '{{R/A/C/I}}': 'R',
        '{{ACTIVITY_NAME}}': 'Requirements Documentation',
        '{{ROLE}}': 'Business Analyst',
        '{{AUTHORITY_DESCRIPTION}}': 'Final decision authority on project direction and budget',
        '{{RESPONSIBILITIES}}': 'Overall project oversight, stakeholder management, executive reporting',
        '{{KEY_DECISIONS}}': 'Go/no-go decisions, scope changes, budget adjustments',
        '{{DESCRIPTION}}': 'Initial change to clarify RACI roles',
        '{{VER}}': '1.0',
        '{{ADDITIONAL_NOTES}}': 'RACI matrix reviewed and approved by all stakeholders',
        '{{ACTION_IF_YES}}': 'Assign immediately',
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