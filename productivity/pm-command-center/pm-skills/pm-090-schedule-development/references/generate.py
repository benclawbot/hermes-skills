#!/usr/bin/env python3
"""Generate filled Schedule Development document from template."""

import os
import sys
from datetime import datetime, timedelta

TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), 'template.md')

def get_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_future_date(days):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

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
        '{{START_DATE}}': get_date(),
        '{{END_DATE}}': get_future_date(90),
        '{{DAYS}}': '90',
        '{{O}}': '3',
        '{{ML}}': '5',
        '{{P}}': '8',
        '{{EST}}': '5',
        '{{NAME}}': 'John Smith',
        '{{ROLE}}': 'Senior Developer',
        '{{HRS}}': '40',
        '{{RESOURCE}}': 'Senior Developer',
        '{{ACTIVITY}}': 'ACT-002',
        '{{ACTION}}': 'Reassigned to alternate resource with similar skills',
        '{{Leveling/FastTrack/Crashing}}': 'Leveling',
        '{{Resolved}}': 'Yes',
        '{{START}}': get_date(),
        '{{END}}': get_future_date(5),
        '{{DUR}}': '5',
        '{{%}}': '0',
        '{{DEPS}}': 'ACT-001',
        '{{MS-001}}': 'MS-001',
        '{{MS-002}}': 'MS-002',
        '{{PERT / BOTTOM_UP / HISTORICAL}}': 'PERT',
        '{{CONSTRAINT}}': 'Must complete by Q4',
        '{{RISK_REASON}}': 'Based on historical variance for similar projects',
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