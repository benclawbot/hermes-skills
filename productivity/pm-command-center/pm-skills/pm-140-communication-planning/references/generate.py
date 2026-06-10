#!/usr/bin/env python3
"""Generate filled Communication Planning document from template."""

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
        '{{STEERING_COMMITTEE_FREQUENCY}}': 'Bi-weekly',
        '{{STEERING_COMMITTEE_CHANNEL}}': 'Meeting',
        '{{TEAM_FREQUENCY}}': 'Daily',
        '{{TEAM_CHANNEL}}': 'Teams',
        '{{VERSION}}': '1.0',
        '{{PREPARED_BY}}': 'Project Management Office',
        '{{SPONSOR_MESSAGE}}': 'Status update, blockers, decisions needed',
        '{{TEAM_MESSAGE}}': 'Sprint goals, assignments, impediments',
        '{{VENDOR_MESSAGE}}': 'Deliverables review, issues, invoices',
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