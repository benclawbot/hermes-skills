#!/usr/bin/env python3
"""Generate filled Sprint Review document from template."""

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
    
    # Sprint Information filled
    content = content.replace('**Sprint #**:   ', '**Sprint #**: 14')
    content = content.replace('**Date**:   ', f'**Date**: {get_date()}')
    content = content.replace('** attendees**:  ', '** attendees**: Product Owner, Scrum Master, Development Team, Stakeholders')
    
    # Demo Items filled
    content = content.replace('| 1 | |', '| 1 | User Authentication Module | Alice | Great feedback on UX | X | | Ready for prod |')
    content = content.replace('| 2 | |', '| 2 | Login API Endpoint | Bob | Approved | X | | RESTful design |')
    content = content.replace('| 3 | |', '| 3 | Password Reset Flow | Carol | Minor tweaks needed | X | | Add email templates |')
    content = content.replace('| 4 | |', '| 4 | Session Management | Bob | Security review passed | X | | Performance optimized |')
    content = content.replace('| 5 | |', '| 5 | OAuth Integration | Alice | Deferred to next sprint | | X | Resource constraint |')
    
    # Feedback Summary filled
    content = content.replace('- \n- \n-', '- Team velocity improved this sprint\n- Code quality metrics above target\n- Stakeholder engagement positive')
    content = content.replace('- \n- \n-', '- Incomplete OAuth feature carry-over\n- Some UI polish needed\n- Documentation slightly behind')
    
    # Stakeholder Requests filled
    content = content.replace('| | | |', '| Add social login options | High | Facebook/Google OAuth')
    content = content.replace('| | | |', '| Mobile responsive design | Medium | Sprint 15 scope')
    
    # Stories Completed vs Committed filled
    content = content.replace('| Committed Points | |', '| Committed Points | 34')
    content = content.replace('| Completed Points | |', '| Completed Points | 29')
    content = content.replace('| Completion Rate | % |', '| Completion Rate | 85%')
    
    # Next Sprint Backlog filled
    content = content.replace('| | | |', '| Payment Gateway Integration | P1 | Critical path |')
    content = content.replace('| | | |', '| Complete OAuth Feature | P1 | Carry-over |')
    
    # Dependencies for Next Sprint filled
    content = content.replace('- \n-', '- External payment provider API documentation\n- Security team availability for review')
    
    # Risks for Next Sprint filled
    content = content.replace('- \n-', '- Third-party API dependency\n- Tight deadline for payment feature')
    
    # Action Items filled
    content = content.replace('| | | |', '| Update documentation | Alice | 2026-06-01')
    content = content.replace('| | | |', '| Schedule security review | Bob | 2026-06-03')
    
    # Output to references folder as output.md
    output_path = os.path.join(os.path.dirname(__file__), 'output.md')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    generate()