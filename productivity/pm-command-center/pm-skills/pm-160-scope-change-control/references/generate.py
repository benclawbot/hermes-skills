#!/usr/bin/env python3
"""Generate filled Scope Change Control document from template."""

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
        '{{CR_ID}}': 'CR-001',
        '{{SUBMITTED_BY}}': 'Product Owner',
        '{{CHANGE_DESCRIPTION}}': 'Add inventory management module to replace third-party system',
        '{{SCOPE_IMPACT}}': 'Add 3 new features, extend timeline by 2 weeks',
        '{{SCHEDULE_IMPACT}}': '+10 days, new milestone: Inventory Module MVP - Aug 15',
        '{{COST_IMPACT}}': '+$45,000 labor + $15,000 licensing',
        '{{RESOURCES_IMPACT}}': '2 additional developers, 1 QA resource',
        '{{PM_NAME}}': 'Sarah Mitchell',
        '{{TECH_LEAD_NAME}}': 'David Chen',
        '{{SPONSOR_NAME}}': 'John Richardson',
        '{{PO_NAME}}': 'Lisa Park',
        '{{DECISION}}': 'Approved',
        '{{IMPLEMENTATION_STATUS}}': 'In Progress',
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