#!/usr/bin/env python3
"""Generate filled Risk Response Planning document from template."""

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
        '{{RISK_ID}}': 'R001',
        '{{RISK_DESCRIPTION}}': 'Key resource departure before critical milestone',
        '{{STRATEGY}}': 'Mitigate',
        '{{ACTION}}': 'Cross-train backup resource, document knowledge transfer',
        '{{OWNER}}': 'Project Manager',
        '{{TRIGGER}}': 'Resignation notice received',
        '{{DEADLINE}}': '2026-06-15',
        '{{STATUS}}': 'Active',
        '{{RISK_ID_2}}': 'R002',
        '{{RISK_DESCRIPTION_2}}': 'Budget overrun due to scope expansion',
        '{{STRATEGY_2}}': 'Transfer',
        '{{ACTION_2}}': 'Purchase contingency insurance, establish reserve fund',
        '{{OWNER_2}}': 'Finance Lead',
        '{{TRIGGER_2}}': 'Cost exceeds 110% of baseline',
        '{{DEADLINE_2}}': '2026-07-01',
        '{{STATUS_2}}': 'Monitoring',
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