#!/usr/bin/env python3
"""Generate filled Milestone/Stage Gate document from template."""

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
        '{{GATE_NUMBER_NAME}}': 'Gate 2 - Design Complete',
        '{{GATE_DATE}}': get_date(),
        '{{GATE_LOCATION}}': 'Conference Room A',
        '{{GATE_CHAIR}}': 'Jane Doe',
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