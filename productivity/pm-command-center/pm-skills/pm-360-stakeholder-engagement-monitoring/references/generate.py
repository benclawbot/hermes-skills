#!/usr/bin/env python3
"""Generate PM-360 Stakeholder Engagement Monitoring document from template."""

import re
from pathlib import Path

def generate_project_info():
    return {
        "project": "Project Alpha - Enterprise System Upgrade",
        "reporting_period": "2026-05-01 to 2026-05-20",
        "pm": "John Davidson"
    }

def generate_stakeholder_registry():
    return [
        ("S001", "Sarah Mitchell", "Lead Developer", "Internal", "High", "High", "Active", "Email, Slack"),
        ("S002", "Mike Chen", "Business Analyst", "Internal", "High", "Low", "Engaged", "Email, Meetings"),
        ("S003", "Client Executive", "Steering Committee", "External", "High", "High", "Active", "Quarterly reviews"),
        ("S004", "Operations Team", "End Users", "External", "Low", "Low", "Passive", "Training sessions"),
        ("S005", "David Martinez", "Resource Manager", "Internal", "Medium", "Medium", "Engaged", "Email, Weekly sync"),
    ]

def generate_communication_log():
    return [
        ("2026-05-05", "Client Executive", "Video call", "Project status review", "Approved phase 2 scope", "John Davidson"),
        ("2026-05-08", "Sarah Mitchell", "Email", "Technical architecture", "Feedback provided", "John Davidson"),
        ("2026-05-10", "Mike Chen", "In-person", "Requirements update", "Document finalized", "Mike Chen"),
        ("2026-05-12", "David Martinez", "Slack", "Resource allocation", "Confirmed availability", "John Davidson"),
    ]

def generate_engagement_activities():
    return [
        ("Client Executive", "2026-05-05", "2026-05-19", "Status review", "Quarterly sync completed"),
        ("Sarah Mitchell", "2026-05-08", "2026-05-22", "Technical review", "Architecture sign-off pending"),
        ("Operations Team", "2026-04-28", "2026-05-25", "Training", "Training materials prepared"),
    ]

def generate_satisfaction_metrics():
    return [
        ("Client Executive", "4", "5", "4", "5", "Improving"),
        ("Sarah Mitchell", "5", "4", "5", "5", "Stable"),
        ("Mike Chen", "4", "5", "4", "4", "Stable"),
        ("Operations Team", "3", "4", "4", "3", "Improving"),
    ]

def generate_concerns():
    return [
        ("Client Executive", "Timeline extension request", "Medium", "Discussed with steering committee", "Resolved"),
        ("Operations Team", "Training schedule conflict", "Low", "Rescheduled training session", "Open"),
    ]

def generate_communication_compliance():
    return [
        ("Client Executive", "Monthly", "Monthly", "Compliant", "Quarterly review completed"),
        ("Sarah Mitchell", "Weekly", "Weekly", "Compliant", "All status updates delivered"),
        ("Operations Team", "As needed", "As needed", "Compliant", "Ad-hoc requests fulfilled"),
    ]

def generate_action_items():
    return [
        ("Schedule follow-up with Client Executive", "John Davidson", "2026-05-26"),
        ("Complete architecture review with Sarah", "John Davidson", "2026-05-21"),
        ("Prepare training materials for Operations", "Mike Chen", "2026-05-23"),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace project information
    info = generate_project_info()
    content = re.sub(r'\*\*Project:\*\*\s*\n', f'**Project:** {info["project"]}\n', content)
    content = re.sub(r'\*\*Reporting Period:\*\*\s*\n', f'**Reporting Period:** {info["reporting_period"]}\n', content)
    content = re.sub(r'\*\*PM:\*\*\s*\n', f'**PM:** {info["pm"]}\n', content)
    
    # Replace stakeholder registry rows
    stakeholders = generate_stakeholder_registry()
    for stakeholder in stakeholders:
        row_pattern = r'\|\s*S\d+\s*\|\s*\|(\s*\|){6,7}\s*\n'
        row_replacement = f"| {stakeholder[0]} | {stakeholder[1]} | {stakeholder[2]} | {stakeholder[3]} | {stakeholder[4]} {stakeholder[5]} | {stakeholder[6]} | {stakeholder[7]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace communication log rows
    comms = generate_communication_log()
    for comm in comms:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {comm[0]} | {comm[1]} | {comm[2]} | {comm[3]} | {comm[4]} | {comm[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace engagement activity rows
    activities = generate_engagement_activities()
    for activity in activities:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {activity[0]} | {activity[1]} | {activity[2]} | {activity[3]} | {activity[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace satisfaction metric rows
    satisfaction = generate_satisfaction_metrics()
    for row in satisfaction:
        row_pattern = r'\|\s*\|\s*☐.*☐.*☐.*☐.*☐.*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace concern/expectation rows
    concerns = generate_concerns()
    for concern in concerns:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*☐.*☐\s*\n'
        row_replacement = f"| {concern[0]} | {concern[1]} | {concern[2]} | {concern[3]} | {concern[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace communication compliance rows
    compliance = generate_communication_compliance()
    for row in compliance:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*☐.*☐.*☐.*\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace action item rows
    actions = generate_action_items()
    for action in actions:
        row_pattern = r'\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {action[0]} | {action[1]} | {action[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    return content

if __name__ == "__main__":
    import sys
    
    template_path = Path(__file__).parent / "template.md"
    output_path = Path(__file__).parent.parent / "pm-360-stakeholder-engagement-monitoring-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")