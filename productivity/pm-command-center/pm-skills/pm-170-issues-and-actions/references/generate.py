#!/usr/bin/env python3
"""Generate filled Issues and Actions Log document from template."""

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
        '{{DATE}}': get_date(),
        '{{PROJECT_NAME}}': 'Enterprise ERP Implementation',
        '{{ISSUE_ID}}': 'I001',
        '{{ISSUE_DATE}}': '2026-05-15',
        '{{ISSUE_DESCRIPTION}}': 'Integration testing environment not ready, blocking UAT',
        '{{ISSUE_OWNER}}': 'Infrastructure Lead',
        '{{ISSUE_PRIORITY}}': 'Critical',
        '{{ISSUE_STATUS}}': 'In Progress',
        '{{RESOLUTION}}': 'Provisioning new environment, ETA 2 days',
        '{{CLOSED_DATE}}': '',
        '{{ACTION_ID}}': 'A001',
        '{{ACTION_DATE}}': '2026-05-18',
        '{{ACTION_DESCRIPTION}}': 'Schedule follow-up with vendor for contract renegotiation',
        '{{ACTION_OWNER}}': 'Procurement Manager',
        '{{DUE_DATE}}': '2026-05-25',
        '{{ACTION_STATUS}}': 'Open',
        '{{NOTES}}': 'Pending budget approval from finance',
        '{{VERSION}}': '1.0',
        '{{PREPARED_BY}}': 'Project Management Office',
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