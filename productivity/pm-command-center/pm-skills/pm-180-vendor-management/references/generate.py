#!/usr/bin/env python3
"""Generate filled Vendor Management document from template."""

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
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Vendor Assessment filled
    content = content.replace('| Vendor A | |', '| Vendor A | Data Migration Services | 2026-06-15 | 4 | 5 | Paid | On track |')
    content = content.replace('| Vendor B | |', '| Vendor B | Infrastructure Setup | 2026-06-30 | 3 | 4 | Invoiced | Minor delays |')
    content = content.replace('| Vendor C | |', '| Vendor C | Security Audit | 2026-07-15 | 5 | 5 | Pending | Excellent performance |')
    
    # Deliverable Tracking filled
    content = content.replace('| D001 | |', '| D001 | Phase 1 Data Migration | Sprint 3 | 2026-06-10 | 2026-06-12 | BA Sign-off |')
    content = content.replace('| D002 | |', '| D002 | Cloud Infrastructure Deployment | Sprint 4 | 2026-06-25 | | Pending |')
    
    # Vendor Meeting Notes filled
    content = content.replace('**Date**:  ', f'**Date**: {get_date()}')
    content = content.replace('**Vendor**:  ', '**Vendor**: Vendor A')
    content = content.replace('**Attendees**:  ', '**Attendees**: John Smith, Sarah Johnson, Michael Chen')
    content = content.replace('1. \n2. \n3. ', f'1. Progress review - 70% complete\n2. Resource allocation discussion\n3. Timeline adjustment for phase 2')
    content = content.replace('- \n-', '- Review Q2 deliverables\n- Confirm payment schedule')
    content = content.replace('**Next Meeting**:  ', f'**Next Meeting**: {get_date()} + 14 days')
    
    # Output to references folder as output.md
    output_path = os.path.join(os.path.dirname(__file__), 'output.md')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    generate()