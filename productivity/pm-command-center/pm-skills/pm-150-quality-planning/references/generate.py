#!/usr/bin/env python3
"""Generate filled Quality Planning document from template."""

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
        '{{CODE_COVERAGE_TARGET}}': '80%',
        '{{DEFECT_DENSITY}}': '< 5',
        '{{RESPONSE_TIME}}': '< 200ms',
        '{{FRAMEWORK}}': 'PyTest',
        '{{MIN_COVERAGE}}': '80%',
        '{{UAT_PARTICIPANTS}}': 'Business users (10 users)',
        '{{REQUIREMENTS_SIGN_OFF}}': 'BA Lead',
        '{{DESIGN_SIGN_OFF}}': 'Tech Lead',
        '{{VERSION}}': '1.0',
        '{{PREPARED_BY}}': 'Quality Assurance Lead',
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