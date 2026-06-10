#!/usr/bin/env python3
"""Generate PM-370 Benefits Realization Tracking document from template."""

import re
from pathlib import Path

def generate_project_info():
    return {
        "project": "Project Alpha - Enterprise System Upgrade",
        "reporting_period": "2026-05-01 to 2026-05-20",
        "benefits_owner": "Patricia Brown"
    }

def generate_benefits_register():
    return [
        ("B001", "Cost reduction through automation", "$150,000", "$112,500", "75", "2026-06-30", "On Track"),
        ("B002", "Improved response time", "40%", "35%", "87.5", "2026-07-31", "On Track"),
        ("B003", "Customer satisfaction score", "4.5/5", "4.2/5", "93", "2026-08-31", "On Track"),
        ("B004", "Process efficiency gains", "25%", "20%", "80", "2026-09-30", "At Risk"),
        ("B005", "Employee productivity", "15%", "12%", "80", "2026-09-30", "On Track"),
    ]

def generate_financial_benefits():
    return [
        ("Cost Savings", "$200,000", "$250,000", "$187,500", "-25%", "Underway, on track for full realization"),
        ("Revenue Increase", "$500,000", "$600,000", "$480,000", "-20%", "Phase 2 pending"),
        ("ROI", "150%", "180%", "135%", "-25%", "Expected to meet target"),
        ("Payback Period", "18 months", "15 months", "16 months", "-1 month", "Slight delay due to scope change"),
    ]

def generate_operational_benefits():
    return [
        ("Cycle Time", "10 days", "6 days", "7 days", "-30%", "Improved from baseline"),
        ("Error Rate", "5%", "1%", "1.5%", "-70%", "Significant improvement achieved"),
        ("Throughput", "100 units/day", "150 units/day", "140 units/day", "+40%", "On track for target"),
        ("Productivity", "80%", "95%", "92%", "+15%", "Slight gap remaining"),
    ]

def generate_strategic_benefits():
    return [
        ("Market Expansion", "New markets entered", "3 markets", "2 markets", "67"),
        ("Innovation Index", "New products launched", "5 products", "4 products", "80"),
        ("Brand Recognition", "Brand awareness score", "75/100", "72/100", "96"),
    ]

def generate_timeline():
    return [
        ("Benefit B001 - Phase 1", "2026-04-30", "2026-04-28", "Achieved", "Phase 1 complete ahead of schedule"),
        ("Benefit B001 - Phase 2", "2026-06-30", "", "In Progress", "On track for completion"),
        ("Benefit B002 - Phase 1", "2026-05-31", "2026-05-30", "Achieved", "Phase 1 complete"),
        ("Full Realization", "2026-12-31", "", "In Progress", "Overall project on track"),
    ]

def generate_kpis():
    return [
        ("Cost per Transaction", "$50", "$35", "$38", "$3", "Improving"),
        ("Customer Retention", "85%", "92%", "90%", "-2%", "Improving"),
        ("Time to Market", "6 months", "4 months", "4.5 months", "-0.5 months", "Improving"),
    ]

def generate_dependencies():
    return [
        ("B001", "System integration completion", "Met", "Integration delay could impact cost savings", "Phase 2 acceleration planned"),
        ("B002", "Training completion", "Pending", "Low risk - training on track", "Monitoring weekly"),
        ("B004", "Process redesign approval", "Met", "Process changes approved", "Implementation underway"),
    ]

def generate_lessons():
    return [
        ("Early stakeholder engagement improves benefits tracking accuracy", "Planning", "High", "Involve benefits owners in initial scope definition"),
        ("Regular monitoring prevents benefits realization gaps", "Execution", "Medium", "Implement monthly benefits reviews"),
        ("Quantifiable targets improve measurement reliability", "Planning", "Medium", "Use SMART criteria for benefit definitions"),
    ]

def generate_sustainability():
    return [
        ("Cost Savings", "Staff turnover could impact sustained savings", "Cross-train team members", "2026-12-01"),
        ("Process Efficiency", "Technology changes may require process updates", "Document procedures, plan for technology upgrades", "2026-09-01"),
    ]

def generate_signoff():
    from datetime import date
    return [
        ("B001 - Cost reduction", "Patricia Brown", date.today().strftime("%Y-%m-%d"), "Phase 1 achieved"),
        ("B002 - Response time", "John Davidson", date.today().strftime("%Y-%m-%d"), "On track"),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace project information
    info = generate_project_info()
    content = re.sub(r'\*\*Project:\*\*\s*\n', f'**Project:** {info["project"]}\n', content)
    content = re.sub(r'\*\*Reporting Period:\*\*\s*\n', f'**Reporting Period:** {info["reporting_period"]}\n', content)
    content = re.sub(r'\*\*Benefits Owner:\*\*\s*\n', f'**Benefits Owner:** {info["benefits_owner"]}\n', content)
    
    # Replace benefits register rows
    benefits = generate_benefits_register()
    for benefit in benefits:
        row_pattern = r'\|\s*B\d+\s*\|\s*\|(\s*\|){5,6}\s*\n'
        row_replacement = f"| {benefit[0]} | {benefit[1]} | {benefit[2]} | {benefit[3]} | {benefit[4]} | {benefit[5]} | {benefit[6]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace financial benefits rows
    financial = generate_financial_benefits()
    for row in financial:
        row_pattern = r'\|\s*Cost Savings\s*\|\s*\$\s*\|\s*\$\s*\|\s*\$\s*\|\s*%\s*\|\s*\n'
        row_replacement = f"| {row[0]} | ${row[1]} | ${row[2]} | ${row[3]} | {row[4]} | {row[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace operational benefits rows
    operational = generate_operational_benefits()
    for row in operational:
        row_pattern = r'\|\s*Cycle Time\s*\|\s*\|\s*\|\s*%\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace strategic benefits rows
    strategic = generate_strategic_benefits()
    for row in strategic:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*%\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace timeline rows
    timeline = generate_timeline()
    for row in timeline:
        row_pattern = r'\|\s*Benefit B001 - Phase 1\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace KPI rows
    kpis = generate_kpis()
    for row in kpis:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*☐\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace dependency rows
    deps = generate_dependencies()
    for dep in deps:
        row_pattern = r'\|\s*\|\s*\|\s*☐.*☐\s*\|\s*\|\s*\n'
        row_replacement = f"| {dep[0]} | {dep[1]} | {dep[2]} | {dep[3]} | {dep[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace lessons learned rows
    lessons = generate_lessons()
    for lesson in lessons:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {lesson[0]} | {lesson[1]} | {lesson[2]} | {lesson[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace sustainability rows
    sustainability = generate_sustainability()
    for row in sustainability:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace signoff rows
    signoffs = generate_signoff()
    for signoff in signoffs:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {signoff[0]} | {signoff[1]} | {signoff[2]} | {signoff[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    return content

if __name__ == "__main__":
    import sys
    
    template_path = Path(__file__).parent / "template.md"
    output_path = Path(__file__).parent.parent / "pm-370-benefits-realization-tracking-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")