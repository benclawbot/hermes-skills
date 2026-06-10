#!/usr/bin/env python3
"""Generate PM-250 Project Closure Report document from template."""

import re
from pathlib import Path

def generate_project_summary():
    return {
        "project_name": "Project Alpha - Enterprise System Upgrade",
        "project_manager": "John Davidson",
        "sponsor": "Maria Garcia",
        "start_date": "2025-09-01",
        "original_end_date": "2026-06-30",
        "actual_end_date": "2026-05-15",
        "final_budget": "$498,500"
    }

def generate_deliverables():
    return [
        ("Enterprise Resource Planning System", "Full functionality per spec", "Complete", "2026-05-10"),
        ("User Documentation", "Complete user and admin guides", "Complete", "2026-05-12"),
        ("Training Materials", "Video tutorials and guides", "Complete", "2026-05-14"),
    ]

def generate_success_criteria():
    return [
        ("Scope", "100% of requirements delivered", "Yes", "Signed acceptance document"),
        ("Schedule", "Within 10% of original timeline", "Yes", "Project tracking logs"),
        ("Budget", "Within 5% of original budget", "Yes", "Final financial report"),
        ("Quality", "Less than 2% defect rate", "Yes", "QA test results"),
        ("Customer Satisfaction", "Score above 4.0/5.0", "Yes", "Survey results"),
    ]

def generate_scope_summary():
    return {
        "original": "Full ERP system with finance, HR, and inventory modules",
        "final": "Full ERP system with finance, HR, inventory, and reporting modules",
        "changes": "+1 module (reporting) due to approved change request CR-012"
    }

def generate_uncompleted_scope():
    return [
        ("Mobile App", "Out of scope - added to Phase 2", "Low - Phase 2 addresses this need"),
    ]

def generate_scope_creep():
    return [
        ("CR-012: Reporting Module", "Added 4 weeks, $45,000 - approved by sponsor"),
    ]

def generate_financial_summary():
    return [
        ("Labor", "$280,000", "$275,000", "-$5,000"),
        ("Materials", "$80,000", "$82,500", "+$2,500"),
        ("Equipment", "$60,000", "$58,000", "-$2,000"),
        ("Contractors", "$70,000", "$73,000", "+$3,000"),
        ("Other", "$10,000", "$10,000", "$0"),
        ("Total", "$500,000", "$498,500", "-$1,500"),
    ]

def generate_financial_explanation():
    return "Under budget by $1,500 due to efficient contractor utilization and materials cost savings."

def generate_timeline_review():
    return [
        ("Planning", "2025-09-01", "2025-09-15", "On Schedule"),
        ("Requirements", "2025-09-16", "2025-10-15", "+3 days"),
        ("Design", "2025-10-16", "2025-11-30", "+1 week"),
        ("Development", "2025-12-01", "2026-03-31", "+2 weeks"),
        ("Testing", "2026-04-01", "2026-05-10", "On Schedule"),
        ("Deployment", "2026-05-11", "2026-05-15", "On Schedule"),
    ]

def generate_schedule_explanation():
    return "Overall 2.5 week delay due to vendor delivery issues in Development phase. Mitigation strategies recovered schedule in Testing phase."

def generate_quality_metrics():
    return [
        ("Defects Found", "< 50", "38"),
        ("Rework Hours", "< 100", "82"),
        ("Customer Satisfaction Score", "> 4.0", "4.5"),
    ]

def generate_team_demobilization():
    return [
        ("John Davidson", "Project Manager", "2026-05-20", "Released"),
        ("Sarah Mitchell", "Lead Developer", "2026-05-18", "Released"),
        ("Mike Chen", "Business Analyst", "2026-05-16", "Released"),
    ]

def generate_asset_transfer():
    return [
        ("ERP System Documentation", "IT Department", "2026-05-15", "Complete"),
        ("Development Tools License", "Legal", "2026-05-15", "Complete"),
    ]

def generate_documentation_completion():
    return [
        ("Final Report", "Complete", "/archive/project-alpha/final-report.pdf"),
        ("As-built Drawings", "Complete", "/archive/project-alpha/as-built/"),
        ("Operations Manual", "Complete", "/archive/project-alpha/ops-manual.pdf"),
        ("Training Materials", "Complete", "/archive/project-alpha/training/"),
        ("Warranties", "Complete", "/archive/project-alpha/warranties/"),
    ]

def generate_administrative_closure():
    return [
        ("Contracts closed", "Complete", "2026-05-15"),
        ("Purchase orders closed", "Complete", "2026-05-15"),
        ("Final invoice submitted", "Complete", "2026-05-17"),
        ("Insurance coverage ended", "Complete", "2026-05-31"),
    ]

def generate_lessons_learned():
    return {
        "successes": [
            "Early stakeholder engagement reduced change requests by 40%",
            "Weekly demos kept sponsor aligned and reduced revision cycles",
            "Agile approach allowed flexible response to vendor delays"
        ],
        "improvements": [
            "More rigorous vendor vetting process needed",
            "Better buffer needed for integration testing phases",
            "More frequent communication with remote team members"
        ],
        "recommendations": [
            "Implement vendor scorecard for future projects",
            "Add 15% time buffer for integration phases",
            "Establish weekly virtual social events for remote teams"
        ]
    }

def generate_team_recognition():
    return {
        "members": "John Davidson, Sarah Mitchell, Mike Chen, Lisa Park, Tom Wilson",
        "contributions": "Outstanding leadership and technical expertise delivered project 2 weeks ahead of recovery schedule"
    }

def generate_signoffs():
    from datetime import date
    return [
        ("Project Manager", "John Davidson", "_____________", date.today().strftime("%Y-%m-%d")),
        ("Sponsor", "Maria Garcia", "_____________", date.today().strftime("%Y-%m-%d")),
        ("Client Representative", "Robert Taylor", "_____________", date.today().strftime("%Y-%m-%d")),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace project summary table
    summary = generate_project_summary()
    content = re.sub(r'\|\s*Project Name\s*\|\s*\|\n', f"| Project Name | {summary['project_name']} |\n", content)
    content = re.sub(r'\|\s*Project Manager\s*\|\s*\|\n', f"| Project Manager | {summary['project_manager']} |\n", content)
    content = re.sub(r'\|\s*Sponsor\s*\|\s*\|\n', f"| Sponsor | {summary['sponsor']} |\n", content)
    content = re.sub(r'\|\s*Start Date\s*\|\s*\|\n', f"| Start Date | {summary['start_date']} |\n", content)
    content = re.sub(r'\|\s*Original End Date\s*\|\s*\|\n', f"| Original End Date | {summary['original_end_date']} |\n", content)
    content = re.sub(r'\|\s*Actual End Date\s*\|\s*\|\n', f"| Actual End Date | {summary['actual_end_date']} |\n", content)
    content = re.sub(r'\|\s*Final Budget\s*\|\s*\|\n', f"| Final Budget | {summary['final_budget']} |\n", content)
    
    # Replace deliverables rows
    deliverables = generate_deliverables()
    for d in deliverables:
        row_pattern = r'\|\s*\|\s*\|\s*☐.*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {d[0]} | {d[1]} | {d[2]} | {d[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace success criteria rows
    criteria = generate_success_criteria()
    for c in criteria:
        row_pattern = r'\|\s*\|\s*\|\s*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace scope summary
    scope = generate_scope_summary()
    content = re.sub(r'\*\*Original Scope\*\*:\s*\n', f"**Original Scope**: {scope['original']}\n", content)
    content = re.sub(r'\*\*Final Scope\*\*:\s*\n', f"**Final Scope**: {scope['final']}\n", content)
    content = re.sub(r'\*\*Changes.*\*\*\s*\n', f"**Changes (Increase/Decrease)**: {scope['changes']}\n", content)
    
    # Replace uncompleted scope rows
    uncompleted = generate_uncompleted_scope()
    for item in uncompleted:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {item[0]} | {item[1]} | {item[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace scope creep rows
    scope_creep = generate_scope_creep()
    for item in scope_creep:
        row_pattern = r'\|\s*\|\s*\n'
        row_replacement = f"| {item[0]} | {item[1]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace financial summary rows
    financial = generate_financial_summary()
    for row in financial:
        bold_row = row[0] == "Total"
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        if bold_row:
            row_replacement = f"| **{row[0]}** | **{row[1]}** | **{row[2]}** | **{row[3]}** |\n"
        else:
            row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace budget variance explanation
    content = re.sub(r'\*\*Budget Variance Explanation\*\*:\s*\n',
                    f"**Budget Variance Explanation**: {generate_financial_explanation()}\n", content)
    
    # Replace timeline review rows
    timeline = generate_timeline_review()
    for row in timeline:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace schedule explanation
    content = re.sub(r'\*\*Schedule Variance Explanation\*\*:\s*\n',
                    f"**Schedule Variance Explanation**: {generate_schedule_explanation()}\n", content)
    
    # Replace quality metrics rows
    quality = generate_quality_metrics()
    for row in quality:
        row_pattern = r'\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace team demobilization rows
    team = generate_team_demobilization()
    for member in team:
        row_pattern = r'\|\s*\|\s*\|\s*☐.*☐\s*\|\s*\|\s*\n'
        row_replacement = f"| {member[0]} | {member[1]} | {member[2]} | {member[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace asset transfer rows
    assets = generate_asset_transfer()
    for asset in assets:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*☐.*☐\s*\n'
        row_replacement = f"| {asset[0]} | {asset[1]} | {asset[2]} | {asset[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace documentation completion rows
    docs = generate_documentation_completion()
    for doc in docs:
        row_pattern = r'\|\s*\|\s*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {doc[0]} | {doc[1]} | {doc[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace administrative closure rows
    admin = generate_administrative_closure()
    for row in admin:
        row_pattern = r'\|\s*\|\s*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace lessons learned
    lessons = generate_lessons_learned()
    content = re.sub(r'\*\*Key Successes\*\*:\n1\.\s*\n2\.\s*\n',
                    f"**Key Successes**:\n1. {lessons['successes'][0]}\n2. {lessons['successes'][1]}\n3. {lessons['successes'][2]}\n", content)
    content = re.sub(r'\*\*Areas for Improvement\*\*:\n1\.\s*\n2\.\s*\n',
                    f"**Areas for Improvement**:\n1. {lessons['improvements'][0]}\n2. {lessons['improvements'][1]}\n3. {lessons['improvements'][2]}\n", content)
    content = re.sub(r'\*\*Recommendations for Future Projects\*\*:\n1\.\s*\n2\.\s*\n',
                    f"**Recommendations for Future Projects**:\n1. {lessons['recommendations'][0]}\n2. {lessons['recommendations'][1]}\n3. {lessons['recommendations'][2]}\n", content)
    
    # Replace team recognition
    recognition = generate_team_recognition()
    content = re.sub(r'\*\*Team Members Recognized\*\*:\s*\n', f"**Team Members Recognized**: {recognition['members']}\n", content)
    content = re.sub(r'\*\*Individual Contributions\*\*:\s*\n', f"**Individual Contributions**: {recognition['contributions']}\n", content)
    
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
    output_path = Path(__file__).parent.parent / "pm-250-project-closure-report-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")