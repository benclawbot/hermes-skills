#!/usr/bin/env python3
"""Generate filled Sprint Retrospective document from template."""

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
    content = content.replace('**Facilitator**:  ', '**Facilitator**: Scrum Master')
    
    # What Went Well filled
    content = content.replace('|| Team | | |', '|| Team | Cross-functional collaboration improved | Sprint demo feedback |')
    content = content.replace('|| Process | | |', '|| Process | Daily standups more focused | Reduced meeting time by 15 min |')
    content = content.replace('|| Tools | | |', '|| Tools | New CI/CD pipeline working well | Faster deployments |')
    content = content.replace('|| Communication | | |', '|| Communication | Better stakeholder updates | Positive feedback |')
    content = content.replace('|| Technical | | |', '|| Technical | Code review process efficient | 100% coverage |')
    content = content.replace('|| Customer | | |', '|| Customer | User feedback incorporated | NPS +10 |')
    
    content = content.replace('1. \n2. \n3. ', '1. Team collaboration significantly improved\n2. CI/CD pipeline reduced deploy time by 50%\n3. Customer satisfaction up')
    
    # What Didn't Go Well filled
    content = content.replace('|| Team | | |', '|| Team | Some scope creep in middle of sprint | Medium |')
    content = content.replace('|| Process | | |', '|| Process | Backlog grooming took longer than planned | Low |')
    content = content.replace('|| Tools | | |', '|| Tools | Integration testing environment instability | Medium |')
    content = content.replace('|| Communication | | |', '|| Communication | External vendor delays not communicated | High |')
    content = content.replace('|| Technical | | |', '|| Technical | Technical debt in auth module | Low |')
    content = content.replace('|| Customer | | |', '|| Customer | Late change requests impacted velocity | Medium |')
    
    content = content.replace('1. \n2. \n3. ', '1. Vendor communication gap caused blocker\n2. Scope changes mid-sprint\n3. Test environment reliability')
    
    # Action Items filled
    content = content.replace('| 1 | |', '| 1 | Implement vendor sync meetings | Process | Scrum Master | High | Sprint 15 | Open |')
    content = content.replace('| 2 | |', '| 2 | Add change request protocol | Process | Product Owner | Medium | Sprint 15 | Open |')
    content = content.replace('| 3 | |', '| 3 | Stabilize test environment | Tools | DevOps | High | Sprint 15 | Open |')
    
    # Team Health Check filled
    content = content.replace('| Communication | |', '| Communication | 4 | Weekly team surveys positive |')
    content = content.replace('| Collaboration | |', '| Collaboration | 4 | Pair programming increased |')
    content = content.replace('| Work-life balance | |', '| Work-life balance | 3 | Some overtime noted |')
    content = content.replace('| Technical growth | |', '| Technical growth | 5 | New skills acquired |')
    content = content.replace('| Meeting efficiency | |', '| Meeting efficiency | 4 | Standups shortened |')
    
    # Focus Areas filled
    content = content.replace('**Team Focus**: ', '**Team Focus**: Improve work-life balance, reduce overtime')
    content = content.replace('**Process Focus**: ', '**Process Focus**: Better change management and vendor coordination')
    content = content.replace('**Technical Focus**: ', '**Technical Focus**: Reduce auth module technical debt')
    
    # Celebration filled
    content = content.replace('- Team member(s) recognized: ', '- Team member(s) recognized: Alice Johnson')
    content = content.replace('- Reason: ', '- Reason: Outstanding leadership on authentication feature')
    
    # Output to references folder as output.md
    output_path = os.path.join(os.path.dirname(__file__), 'output.md')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    generate()