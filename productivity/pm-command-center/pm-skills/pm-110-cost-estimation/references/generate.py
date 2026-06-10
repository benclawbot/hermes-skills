#!/usr/bin/env python3
"""Generate filled Cost Estimation document from template."""

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
        '{{ROM / DETAILED / FINAL}}': 'Detailed',
        '{{+/-XX%}}': '+/-10%',
        '{{$AMOUNT}}': '$450,000',
        '{{CURRENCY}}': 'USD',
        '{{NAME}}': 'John Smith',
        '{{WBS}}': '1.1.2',
        '{{ROLE}}': 'Business Analyst',
        '{{HRS}}': '200',
        '{{$RATE}}': '$95',
        '{{$COST}}': '$19,000',
        '{{TOTAL_HRS}}': '800',
        '{{$TOTAL_LABOR}}': '$76,000',
        '{{MATERIAL_ITEM}}': 'ERP Software Licenses',
        '{{QTY}}': '50',
        '{{$UNIT}}': '$2,000',
        '{{$TOTAL}}': '$100,000',
        '{{VENDOR}}': 'TechCorp Inc.',
        '{{EQUIPMENT_ITEM}}': 'Development Servers',
        '{{$MATERIAL_TOTAL}}': '$150,000',
        '{{CONTRACT_ID}}': 'CT-2026-001',
        '{{SERVICE}}': 'ERP Implementation Services',
        '{{$VENDOR_TOTAL}}': '$200,000',
        '{{TRAVEL_DESCRIPTION}}': 'On-site consulting visits (estimated 10 trips)',
        '{{TRAINING_DESCRIPTION}}': 'End-user training sessions',
        '{{SOFTWARE_DESCRIPTION}}': 'Additional productivity tools',
        '{{FACILITIES_DESCRIPTION}}': 'Temporary office space during cutover',
        '{{$OTHER_TOTAL}}': '$30,000',
        '{{METHOD}}': 'Fixed Percentage',
        '{{RATE}}': '8%',
        '{{BASE}}': 'Total Direct Costs',
        '{{$INDIRECT_TOTAL}}': '$36,480',
        '{{DELIVERABLE}}': 'Project Management',
        '{{$}}': '$45,000',
        '{{$BAC}}': '$492,480',
        '{{%}}': '30%',
        '{{MONTH/QUARTER}}': 'Q1 2026',
        '{{$}}': '$125,000',
        '{{NOTES}}': 'Within expected range',
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