#!/usr/bin/env python3
"""Generate filled Sprint Execution document from template."""

import os
import sys
from datetime import datetime, timedelta

TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), 'template.md')

def get_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_past_date(days_ago):
    d = datetime.now() - timedelta(days=days_ago)
    return d.strftime("%Y-%m-%d")

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
    
    # Sprint Board filled
    content = content.replace('| US-001 | |', '| US-001 | | | X | |')
    content = content.replace('| US-002 | |', '| US-002 | | X | | |')
    content = content.replace('| US-003 | |', '| US-003 | X | | | Blocked on API |')
    content = content.replace('| US-004 | |', '| US-004 | X | | | |')
    content = content.replace('| US-005 | |', '| US-005 | | | X | |')
    
    # Daily Standup - Day 1
    content = content.replace('### Day 1 - [Date]', f'### Day 1 - {get_past_date(4)}')
    content = content.replace('**Attendance**: \n\n| |', '**Attendance**: Alice, Bob, Carol\n\n| Alice | Completed auth module design | Working on US-001 | None |')
    content = content.replace('| | | | |\n|| |', '| Bob | Reviewed API specs | Starting US-002 | None |')
    content = content.replace('| | | | |', '| Carol | Created UI components | US-003 blocked on API | Waiting for endpoint |')
    
    # Blocker Log filled
    content = content.replace('| B001 | |', '| B001 | US-003 | Payment API not ready | Day 1 | Day 3 | API deployed to staging |')
    content = content.replace('| B002 | |', '| B002 | US-004 | Database migration delayed | Day 2 | | Pending DBA review |')
    
    # Defects Found filled
    content = content.replace('| | |', '| DEF-001 | Login form validation error | Medium | Bob | Open |')
    content = content.replace('| | |', '| DEF-002 | Session timeout too short | Low | Carol | Fixed |')
    
    # Notes filled
    content = content.replace('- \n\n---', '- Sprint progressing well\n- One blocker identified and resolved\n- Daily standups effective\n\n---')
    
    # Output to references folder as output.md
    output_path = os.path.join(os.path.dirname(__file__), 'output.md')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    generate()