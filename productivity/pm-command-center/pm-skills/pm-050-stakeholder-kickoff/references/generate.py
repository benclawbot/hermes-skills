#!/usr/bin/env python3
"""Generate filled Stakeholder Kickoff Meeting document from template."""

import os
import sys
from datetime import datetime, timedelta

TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), 'template.md')

def get_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_future_date(days=7):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

def generate():
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Error: Template not found at {TEMPLATE_FILE}")
        sys.exit(1)
    
    with open(TEMPLATE_FILE, 'r') as f:
        content = f.read()
    
    # Replace placeholders
    replacements = {
        '[Project Name]': 'Enterprise ERP Implementation',
        '[Date]': get_date(),
        '[Start Time]': '09:00 AM',
        '[End Time]': '11:00 AM',
        '[Location / Virtual Link]': 'Conference Room A / Microsoft Teams',
        '[Name]': 'Sarah Mitchell',
        '[Next step 1]': 'Distribute meeting notes and presentation materials',
        '[Next step 2]': 'Schedule follow-up stakeholder interviews',
        '[Next step 3]': 'Begin requirements gathering sessions',
        '[Resource 1]': 'Project Charter document',
        '[Resource 2]': 'Stakeholder Register template',
        '[Purpose]': 'Requirements review and scope validation',
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