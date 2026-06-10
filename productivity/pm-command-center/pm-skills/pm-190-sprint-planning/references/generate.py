#!/usr/bin/env python3
"""Generate filled Sprint Planning document from template."""

import os
import sys
from datetime import datetime

TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), 'template.md')

def get_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_sprint_start():
    return datetime.now().strftime("%Y-%m-%d")

def get_sprint_end():
    end = datetime.now()
    from datetime import timedelta
    end = end + timedelta(days=13)
    return end.strftime("%Y-%m-%d")

def generate():
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Error: Template not found at {TEMPLATE_FILE}")
        sys.exit(1)
    
    with open(TEMPLATE_FILE, 'r') as f:
        content = f.read()
    
    # Replace placeholders
    replacements = {
        '{{DATE}}': get_date(),
        '{{SPRINT_START}}': get_sprint_start(),
        '{{SPRINT_END}}': get_sprint_end(),
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Sprint Information filled
    content = content.replace('**Sprint #**:   ', '**Sprint #**: 14')
    content = content.replace('Start:  / End:  ', f'Start: {get_sprint_start()} / End: {get_sprint_end()}')
    content = content.replace('**Sprint Goal**:   ', '**Sprint Goal**: Complete user authentication module and begin payment integration')
    
    # Capacity Planning filled
    content = content.replace('| | | | | | |', '| Alice Johnson | Lead Developer | 10 | 8 | 80 | 100%')
    content = content.replace('| | | | | | |', '| Bob Martinez | Backend Developer | 10 | 8 | 80 | 100%')
    content = content.replace('| | | | | | |', '| Carol Williams | Frontend Developer | 8 | 8 | 64 | 80%')
    content = content.replace('| **Total** | |', '| **Total** | | | | 224 |')
    
    # Velocity Calculation filled
    content = content.replace('| Total Team Hours | |', '| Total Team Hours | 224')
    content = content.replace('| Expected Velocity (story points) | |', '| Expected Velocity (story points) | 34')
    content = content.replace('| Historical Velocity | |', '| Historical Velocity | 32')
    content = content.replace('| Velocity This Sprint | |', '| Velocity This Sprint | TBD')
    
    # Commitment filled
    content = content.replace('| 1 | |', '| 1 | US-245 User Authentication | 8 | Alice Johnson | Core feature')
    content = content.replace('| 2 | |', '| 2 | US-246 Login API | 5 | Bob Martinez | Depends on US-245')
    content = content.replace('| 3 | |', '| 3 | US-247 Password Reset Flow | 5 | Carol Williams | UI integration')
    content = content.replace('| 4 | |', '| 4 | US-248 Session Management | 8 | Bob Martinez | Security critical')
    content = content.replace('| 5 | |', '| 5 | US-249 OAuth Integration | 8 | Alice Johnson | Stretch goal')
    content = content.replace('| **Total Committed** | |', '| **Total Committed** | 34 | |')
    
    # Backlog Grooming Notes filled
    content = content.replace('- Items reviewed:', '- Items reviewed: 15 backlog items')
    content = content.replace('- Priorities confirmed:', '- Priorities confirmed: Top 10 items prioritized')
    content = content.replace('- Estimates updated:', '- Estimates updated: 8 items re-estimated')
    
    # Output to references folder as output.md
    output_path = os.path.join(os.path.dirname(__file__), 'output.md')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    generate()