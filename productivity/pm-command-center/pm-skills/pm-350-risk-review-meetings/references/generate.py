#!/usr/bin/env python3
"""Generate PM-350 Risk Review Meetings document from template."""

import re
from pathlib import Path
from datetime import date, timedelta

def generate_meeting_info():
    return {
        "date": "2026-05-20",
        "sprint": "Sprint 14",
        "facilitator": "Thomas Anderson",
        "attendees": "Project Team Leads, QA Lead, Dev Leads"
    }

def generate_risks():
    return [
        ("R001", "Database migration timeline risk", "Medium", "High", "Medium", "Open", "David Chen", "Increase buffer time; parallel migration path"),
        ("R002", "Third-party API deprecation", "High", "High", "High", "Mitigated", "Sarah Park", "Completed API migration to new version"),
        ("R003", "Resource availability during holiday period", "Low", "Medium", "Low", "Open", "Mike Johnson", "Cross-training program initiated"),
        ("R004", "Security vulnerability in legacy module", "Medium", "High", "Medium", "Closed", "Security Team", "Module patched and verified"),
        ("R005", "Client requirement scope creep", "High", "Medium", "High", "Open", "Product Owner", "Change control board review scheduled"),
    ]

def generate_new_risks():
    return [
        ("Cloud infrastructure cost overrun", "Medium", "High", "High", "Finance Lead", "Implement cost monitoring and alerts"),
        ("Key developer on planned leave during release", "Low", "Medium", "Low", "Team Lead", "Document handoff procedures"),
    ]

def generate_status_changes():
    return [
        ("R002", "Open", "Mitigated", "API migration completed successfully", date.today().strftime("%Y-%m-%d")),
        ("R004", "Mitigated", "Closed", "Vulnerability patched and verified", (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")),
    ]

def generate_mitigation_progress():
    return [
        ("R001", "Update migration timeline to include buffer", "David Chen", (date.today() + timedelta(days=5)).strftime("%Y-%m-%d"), "In Progress", "Waiting for stakeholder approval"),
        ("R003", "Complete cross-training for 2 backup resources", "Mike Johnson", (date.today() + timedelta(days=10)).strftime("%Y-%m-%d"), "Open", "Training schedule drafted"),
        ("R005", "Schedule change control board review", "Product Owner", (date.today() + timedelta(days=2)).strftime("%Y-%m-%d"), "In Progress", "Invite sent to stakeholders"),
    ]

def generate_escalations():
    return [
        ("R005", "Client requirement scope creep may impact delivery", "Senior Management", date.today().strftime("%Y-%m-%d")),
    ]

def generate_summary():
    return {
        "risks_opened": 2,
        "risks_closed": 1,
        "risks_escalated": 1,
        "concerns": [
            "Cloud infrastructure costs trending above budget",
            "Resource coverage during upcoming holiday period",
            "Scope creep pressure from client"
        ]
    }

def generate_recommendations():
    return [
        "Implement proactive cost monitoring for cloud infrastructure",
        "Finalize cross-training program before holiday period",
        "Enforce change control process for any new scope requests"
    ]

def generate_action_items():
    return [
        ("Review and approve R001 mitigation plan", "Project Sponsor", (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")),
        ("Schedule cross-training sessions", "Team Lead", (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")),
        ("Prepare change control board presentation", "Product Owner", (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace meeting info
    info = generate_meeting_info()
    content = re.sub(r'\*\*Date:\*\*\s*\n', f'**Date:** {info["date"]}\n', content)
    content = re.sub(r'\*\*Sprint:\*\*\s*\n', f'**Sprint:** {info["sprint"]}\n', content)
    content = re.sub(r'\*\*Facilitator:\*\*\s*\n', f'**Facilitator:** {info["facilitator"]}\n', content)
    content = re.sub(r'\*\*Attendees:\*\*\s*\n', f'**Attendees:** {info["attendees"]}\n', content)
    
    # Replace risk register rows
    risks = generate_risks()
    for risk in risks:
        row_pattern = r'\|[^|]*\|[^|]*☐[^|]*☐[^|]*☐[^|]*☐[^|]*☐[^|]*☐[^|]*☐[^|]*\|\s*\|\s*\|\n'
        
        prob_checkbox = {
            "Low": "☐ Low ☐ Medium ☐ High",
            "Medium": "☐ Low ☑ Medium ☐ High",
            "High": "☐ Low ☐ Medium ☑ High",
        }.get(risk[2], "☐ Low ☐ Medium ☐ High")
        
        impact_checkbox = {
            "Low": "☐ Low ☐ Medium ☐ High",
            "Medium": "☐ Low ☑ Medium ☐ High",
            "High": "☐ Low ☐ Medium ☑ High",
        }.get(risk[3], "☐ Low ☐ Medium ☐ High")
        
        status_checkbox = {
            "Open": "☑ Open ☐ Mitigated ☐ Closed",
            "Mitigated": "☐ Open ☑ Mitigated ☐ Closed",
            "Closed": "☐ Open ☐ Mitigated ☑ Closed",
        }.get(risk[5], "☐ Open ☐ Mitigated ☐ Closed")
        
        score = {"Low": "Low", "Medium": "Medium", "High": "High"}.get(risk[4], risk[4])
        row_replacement = f"| {risk[0]} | {risk[1]} | {prob_checkbox} | {impact_checkbox} | {score} | {status_checkbox} | {risk[6]} | {risk[7]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace new risks
    new_risks = generate_new_risks()
    for risk in new_risks:
        row_pattern = r'\|[^|]*\|[^|]*☐[^|]*☐[^|]*☐[^|]*☐[^|]*☐[^|]*☐[^|]*\|\s*\|\n'
        
        prob_checkbox = {
            "Low": "☐ Low ☐ Medium ☐ High",
            "Medium": "☐ Low ☑ Medium ☐ High",
            "High": "☐ Low ☐ Medium ☑ High",
        }.get(risk[1], "☐ Low ☐ Medium ☐ High")
        
        impact_checkbox = {
            "Low": "☐ Low ☐ Medium ☐ High",
            "Medium": "☐ Low ☑ Medium ☐ High",
            "High": "☐ Low ☐ Medium ☑ High",
        }.get(risk[2], "☐ Low ☐ Medium ☐ High")
        
        score = {"Low": "Low", "Medium": "Medium", "High": "High"}.get(risk[3], risk[3])
        row_replacement = f"| {risk[0]} | {prob_checkbox} | {impact_checkbox} | {score} | {risk[4]} | {risk[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace status changes
    changes = generate_status_changes()
    for change in changes:
        row_pattern = r'\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\n'
        row_replacement = f"| {change[0]} | {change[1]} | {change[2]} | {change[3]} | {change[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace mitigation progress rows
    mitigation = generate_mitigation_progress()
    for m in mitigation:
        row_pattern = r'\|[^|]*\|[^|]*\|[^|]*\|[^|]*☐[^|]*☐[^|]*☐[^|]*\|\s*\|\n'
        
        status_checkbox = {
            "Open": "☑ Open ☐ In Progress ☐ Complete",
            "In Progress": "☐ Open ☑ In Progress ☐ Complete",
            "Complete": "☐ Open ☐ In Progress ☑ Complete",
        }.get(m[3], "☐ Open ☐ In Progress ☐ Complete")
        
        row_replacement = f"| {m[0]} | {m[1]} | {m[2]} | {m[3]} | {status_checkbox} | {m[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace escalation rows
    escalations = generate_escalations()
    for esc in escalations:
        row_pattern = r'\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\n'
        row_replacement = f"| {esc[0]} | {esc[1]} | {esc[2]} | {esc[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace summary section
    summary = generate_summary()
    content = re.sub(r'### Risks Opened This Period\n-', f"### Risks Opened This Period\n- {summary['risks_opened']} new risks identified", content)
    content = re.sub(r'### Risks Closed This Period\n-', f"### Risks Closed This Period\n- {summary['risks_closed']} risks closed", content)
    content = re.sub(r'### Risks Escalated This Period\n-', f"### Risks Escalated This Period\n- {summary['risks_escalated']} risks escalated", content)
    
    # Replace key concerns
    concerns_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(summary['concerns'])])
    content = re.sub(r'### Key Concerns\n1\.\n2\.\n3\.', f"### Key Concerns\n{concerns_text}", content)
    
    # Replace recommendations
    recs_text = "\n".join([f"{i+1}. {r}" for i, r in enumerate(generate_recommendations())])
    content = re.sub(r'## Recommendations\n1\.\n2\.\n3\.', f"## Recommendations\n{recs_text}", content)
    
    # Replace action items
    actions = generate_action_items()
    for action in actions:
        row_pattern = r'\|\s*\|[^|]*\|[^|]*\|\n'
        row_replacement = f"| {action[0]} | {action[1]} | {action[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    return content

if __name__ == "__main__":
    import sys
    
    template_path = Path(__file__).parent / "template.md"
    output_path = Path(__file__).parent.parent / "pm-350-risk-review-meetings-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")