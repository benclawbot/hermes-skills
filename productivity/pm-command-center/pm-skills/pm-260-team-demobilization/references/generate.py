#!/usr/bin/env python3
"""Generate PM-260 Team Demobilization document from template."""

import re
from pathlib import Path

def generate_project_info():
    return {
        "project_name": "Project Alpha - Enterprise System Upgrade",
        "project_manager": "John Davidson",
        "demobilization_date": "2026-05-20",
        "total_team_size": "8"
    }

def generate_transition_announcement():
    return "2026-05-06"

def generate_team_members():
    return [
        ("John Davidson", "Project Manager", "Returning", "2026-05-20", "New Project: PM-300"),
        ("Sarah Mitchell", "Lead Developer", "Returning", "2026-05-18", "Available for assignment"),
        ("Mike Chen", "Business Analyst", "Returning", "2026-05-16", "Available for assignment"),
        ("Lisa Park", "QA Lead", "New Project", "2026-05-22", "Project Beta - QA Lead"),
        ("Tom Wilson", "Developer", "Returning", "2026-05-17", "Available for assignment"),
        ("Emma Davis", "Designer", "Terminated", "2026-05-15", "End of contract"),
        ("James Lee", "Developer", "Returning", "2026-05-19", "Available for assignment"),
        ("Anna Kim", "Business Analyst", "Returning", "2026-05-16", "Project Gamma - BA"),
    ]

def generate_handover_activities():
    return [
        ("Document transfer", "John Davidson", "2026-05-18", "Complete"),
        ("Knowledge transfer sessions", "Sarah Mitchell", "2026-05-19", "Complete"),
        ("Client relationship handoff", "Mike Chen", "2026-05-17", "Complete"),
        ("Open issue transfer", "Lisa Park", "2026-05-20", "Complete"),
    ]

def generate_equipment():
    return [
        ("Laptop - Dell XPS 15", "John Davidson", "2026-05-20", "Good", "Complete"),
        ("Laptop - MacBook Pro", "Sarah Mitchell", "2026-05-18", "Good", "Complete"),
        ("Access Badge #1234", "Mike Chen", "2026-05-16", "Returned", "Complete"),
        ("Phone - iPhone 14", "Lisa Park", "2026-05-22", "Good", "Pending"),
        ("Company Vehicle - Ford Transit", "Tom Wilson", "2026-05-17", "Good", "Complete"),
    ]

def generate_access_revocation():
    return [
        ("Email - john.davidson@company.com", "Full Access", "2026-05-20", "IT Security"),
        ("Project Systems - JIRA", "Admin", "2026-05-20", "IT Security"),
        ("VPN - GlobalConnect", "Standard", "2026-05-20", "IT Security"),
        ("Building Access - Floor 3", "Standard", "2026-05-21", "Facilities"),
        ("Client Systems - Alpha Portal", "Read-only", "2026-05-18", "Client IT"),
    ]

def generate_final_tasks():
    return [
        ("Complete documentation archive", "Sarah Mitchell", "2026-05-18", "Complete"),
        ("Submit final timesheet", "All Team Members", "2026-05-22", "Complete"),
        ("Return all equipment", "Lisa Park", "2026-05-22", "Pending"),
        ("Complete exit interview", "Emma Davis", "2026-05-15", "Complete"),
    ]

def generate_documentation_handover():
    return [
        ("Project files - shared drive", "John Davidson", "Mike Chen", "2026-05-18", "Complete"),
        ("Contacts list", "Sarah Mitchell", "Lisa Park", "2026-05-19", "Complete"),
        ("Procedures/Processes", "Mike Chen", "Anna Kim", "2026-05-17", "Complete"),
        ("Tools/Equipment manuals", "Tom Wilson", "John Davidson", "2026-05-17", "Complete"),
    ]

def generate_verbal_handover():
    return [
        ("Architecture decisions", "Sarah Mitchell", "James Lee", "2026-05-18", "Complete"),
        ("Client requirements context", "Mike Chen", "Anna Kim", "2026-05-16", "Complete"),
        ("Testing protocols", "Lisa Park", "QA Team", "2026-05-19", "Complete"),
    ]

def generate_performance_feedback():
    return [
        ("John Davidson", "Exceeds Expectations", "Leadership, stakeholder management", "Mentoring, technical depth",
         "Key contributor for future senior roles"),
        ("Sarah Mitchell", "Exceeds Expectations", "Technical excellence, team support", "Presentation skills",
         "Ready for tech lead position"),
        ("Mike Chen", "Meets Expectations", "Stakeholder communication, documentation", "Scope management",
         "Continue with complex projects"),
    ]

def generate_final_payroll():
    return [
        ("John Davidson", "2026-05-20", "Complete", "Clear", "2026-05-25"),
        ("Sarah Mitchell", "2026-05-18", "Complete", "Clear", "2026-05-23"),
        ("Emma Davis", "2026-05-15", "Complete", "Outstanding - $2,500", "2026-05-20"),
    ]

def generate_exit_interviews():
    return [
        ("Emma Davis", "HR Representative", "2026-05-15", "Positive experience, would recommend company",
         "Consider flexible contract terms for contractors"),
    ]

def generate_confirmation():
    return [
        ("All equipment returned", "Complete", "All items accounted for"),
        ("All access revoked", "Complete", "IT confirms removal"),
        ("All docs transferred", "Complete", "Shared drive archived"),
        ("All final payments processed", "Complete", "Payroll completed"),
        ("Exit interviews completed", "Complete", "1 interview conducted"),
    ]

def generate_signoffs():
    from datetime import date
    return [
        ("Project Manager", "John Davidson", "_____________", date.today().strftime("%Y-%m-%d")),
        ("HR Representative", "Patricia Brown", "_____________", date.today().strftime("%Y-%m-%d")),
        ("Resource Manager", "David Martinez", "_____________", date.today().strftime("%Y-%m-%d")),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace basic info
    info = generate_project_info()
    content = re.sub(r'\*\*Project Name\*\*:\s*\n', f'**Project Name**: {info["project_name"]}\n', content)
    content = re.sub(r'\*\*Project Manager\*\*:\s*\n', f'**Project Manager**: {info["project_manager"]}\n', content)
    content = re.sub(r'\*\*Demobilization Date\*\*:\s*\n', f'**Demobilization Date**: {info["demobilization_date"]}\n', content)
    content = re.sub(r'\*\*Total Team Size\*\*:\s*\n', f'**Total Team Size**: {info["total_team_size"]}\n', content)
    
    # Replace transition announcement
    content = re.sub(r'\*\*Transition Announcement Date\*\*:\s*\n',
                    f'**Transition Announcement Date**: {generate_transition_announcement()}\n', content)
    content = re.sub(r'\*\*Communication Recipients\*\*:\s*☐.*☐.*☐.*☐\s*\n',
                    '**Communication Recipients**: ☑ Team ☑ Stakeholders ☑ HR ☑ Finance\n', content)
    
    # Replace team member rows
    team = generate_team_members()
    for member in team:
        row_pattern = r'\|\s*\|\s*\|\s*☐.*☐.*☐\s*\|\s*\|\s*\n'
        row_replacement = f"| {member[0]} | {member[1]} | {member[2]} | {member[3]} | {member[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace handover activity rows
    handover = generate_handover_activities()
    for activity in handover:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*☐.*☐\s*\n'
        row_replacement = f"| {activity[0]} | {activity[1]} | {activity[2]} | {activity[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace equipment rows
    equipment = generate_equipment()
    for item in equipment:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*☐.*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {item[0]} | {item[1]} | {item[2]} | {item[3]} | {item[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace access revocation rows
    access = generate_access_revocation()
    for row in access:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace final tasks rows
    tasks = generate_final_tasks()
    for task in tasks:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*☐.*☐\s*\n'
        row_replacement = f"| {task[0]} | {task[1]} | {task[2]} | {task[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace documentation handover rows
    docs = generate_documentation_handover()
    for doc in docs:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*☐.*☐\s*\n'
        row_replacement = f"| {doc[0]} | {doc[1]} | {doc[2]} | {doc[3]} | {doc[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace verbal handover rows
    verbal = generate_verbal_handover()
    for row in verbal:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*☐.*☐\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace performance feedback rows
    feedback = generate_performance_feedback()
    for row in feedback:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace final payroll rows
    payroll = generate_final_payroll()
    for row in payroll:
        row_pattern = r'\|\s*\|\s*☐.*☐\s*\|\s*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace exit interview rows
    exit_int = generate_exit_interviews()
    for row in exit_int:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace confirmation rows
    confirm = generate_confirmation()
    for row in confirm:
        row_pattern = r'\|\s*\|\s*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace signoffs
    signoffs = generate_signoffs()
    for signoff in signoffs:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {signoff[0]} | {signoff[1]} | {signoff[2]} | {signoff[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    return content

if __name__ == "__main__":
    import sys
    
    template_path = Path(__file__).parent / "template.md"
    output_path = Path(__file__).parent.parent / "pm-260-team-demobilization-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")