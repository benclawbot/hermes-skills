#!/usr/bin/env python3
"""Generate filled Business Case document from template."""

import os
import sys
from datetime import datetime

TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), 'template.md')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'business-case-output.md')

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
        '[Project Name]': 'Enterprise ERP Implementation',
        '[Date]': get_date(),
        '[Name]': 'Project Management Office',
        '[Describe the problem or opportunity being addressed]': 'Current legacy systems are unable to support business growth and digital transformation initiatives. Manual processes create operational inefficiencies and data silos across departments.',
        '[Outline the proposed solution]': 'Implement integrated cloud-based ERP system to unify business processes, enable real-time reporting, and support scalable growth.',
        '[Brief summary of key benefits]': 'Improved operational efficiency (30%), reduced manual work (50%), better data visibility, and enhanced customer satisfaction.',
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