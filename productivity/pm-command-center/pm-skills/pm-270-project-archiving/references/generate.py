#!/usr/bin/env python3
"""Generate PM-270 Project Archiving document from template."""

import re
from pathlib import Path

def generate_project_info():
    return {
        "project_name": "Project Alpha - Enterprise System Upgrade",
        "project_manager": "John Davidson",
        "archive_date": "2026-05-20",
        "archive_location": "/archive/project-alpha-2026"
    }

def generate_documentation():
    return [
        ("Planning", "Project Charter", "1.2", "2025-09-01", "/archive/planning/", "7 years"),
        ("Planning", "Requirements Document", "2.1", "2025-10-15", "/archive/planning/", "7 years"),
        ("Execution", "Design Specifications", "3.0", "2025-12-01", "/archive/execution/", "5 years"),
        ("Execution", "Test Reports", "1.5", "2026-05-10", "/archive/execution/", "5 years"),
        ("Monitoring", "Status Reports", "1.0", "2026-05-15", "/archive/monitoring/", "3 years"),
        ("Closure", "Project Closure Report", "1.0", "2026-05-15", "/archive/closure/", "7 years"),
    ]

def generate_deliverables():
    return [
        ("ERP System Installation Files", "Digital", "/archive/deliverables/erp/", "2.5 GB", "Project Team"),
        ("User Documentation Package", "Digital", "/archive/deliverables/docs/", "150 MB", "Public - Read Only"),
        ("Training Video Archive", "Digital", "/archive/deliverables/training/", "8 GB", "Training Team"),
    ]

def generate_project_data():
    return [
        ("Code/Source", "All source code and dependencies", "ZIP", "500 MB", "/archive/data/source/"),
        ("Databases", "Test and production databases", "SQL", "1.2 GB", "/archive/data/databases/"),
        ("Media files", "Screenshots and presentations", "Various", "250 MB", "/archive/data/media/"),
        ("Reports", "All generated reports", "PDF", "50 MB", "/archive/data/reports/"),
        ("Correspondence", "Email and chat logs", "PST", "100 MB", "/archive/data/comm/"),
    ]

def generate_archive_metadata():
    return {
        "project_id": "PRJ-2025-034",
        "start_date": "2025-09-01",
        "end_date": "2026-05-15",
        "total_budget": "$498,500",
        "num_deliverables": "3",
        "num_documents": "47",
        "archive_size": "12.75 GB",
        "format": "Both",
        "encryption": "Yes"
    }

def generate_retention_policy():
    return [
        ("Financial records", "7 years", "Tax and audit compliance", "Secure shred"),
        ("Contracts", "10 years", "Legal reference", "Physical archive"),
        ("Technical documentation", "5 years", "Future maintenance", "Digital retention"),
        ("Legal documents", "10 years", "Compliance requirements", "Physical + Digital"),
        ("Communications", "3 years", "Business context", "Digital deletion"),
    ]

def generate_compliance():
    return [
        ("Data privacy compliance", "Met", "GDPR documentation complete"),
        ("Industry regulations", "Met", "SOX compliance verified"),
        ("Internal policies", "Met", "Records retention policy followed"),
        ("Contractual requirements", "Met", "All client requirements met"),
    ]

def generate_access_control():
    return [
        ("Project Manager", "Admin", "John Davidson"),
        ("Sponsor", "Read", "Maria Garcia"),
        ("Audit", "Read", "Internal Audit Team"),
        ("Public", "None", "N/A"),
    ]

def generate_access_procedure():
    return "Submit request via ServiceNow portal → Records Manager approval → 48-hour access grant → Log maintained for compliance"

def generate_indexing():
    return {
        "project_name": "Project Alpha - Enterprise System Upgrade",
        "client_name": "Metro Financial Group",
        "industry_sector": "Financial Services",
        "key_technologies": "SAP ERP, SQL Server, React, Azure",
        "team_members": "John Davidson, Sarah Mitchell, Mike Chen",
        "keywords": "ERP, finance, HR, inventory, deployment"
    }

def generate_transfer_checklist():
    return [
        ("All documents indexed", "Complete", "Patricia Brown", "2026-05-18"),
        ("Metadata complete", "Complete", "Patricia Brown", "2026-05-18"),
        ("Storage media verified", "Complete", "David Martinez", "2026-05-19"),
        ("Access controls set", "Complete", "IT Security", "2026-05-19"),
        ("Retention policy applied", "Complete", "Records Manager", "2026-05-20"),
        ("Backup confirmed", "Complete", "Backup Team", "2026-05-20"),
    ]

def generate_archive_locations():
    return {
        "primary": "Enterprise Document Management System (EDMS)",
        "secondary": "AWS S3 - us-west-2 region",
        "offsite": "Yes",
        "location": "Iron Mountain - Chicago Facility"
    }

def generate_destruction_policy():
    return [
        ("Training videos", "2029-05-15", "Physical Destroy", "Records Manager"),
        ("Development artifacts", "2028-05-15", "Delete", "Project Manager"),
    ]

def generate_signoffs():
    from datetime import date
    return [
        ("Project Manager", "John Davidson", "_____________", date.today().strftime("%Y-%m-%d")),
        ("Records Manager", "Patricia Brown", "_____________", date.today().strftime("%Y-%m-%d")),
        ("Sponsor", "Maria Garcia", "_____________", date.today().strftime("%Y-%m-%d")),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace basic info
    info = generate_project_info()
    content = re.sub(r'\*\*Project Name\*\*:\s*\n', f'**Project Name**: {info["project_name"]}\n', content)
    content = re.sub(r'\*\*Project Manager\*\*:\s*\n', f'**Project Manager**: {info["project_manager"]}\n', content)
    content = re.sub(r'\*\*Archive Date\*\*:\s*\n', f'**Archive Date**: {info["archive_date"]}\n', content)
    content = re.sub(r'\*\*Archive Location\*\*:\s*\n', f'**Archive Location**: {info["archive_location"]}\n', content)
    
    # Replace documentation rows
    docs = generate_documentation()
    for doc in docs:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {doc[0]} | {doc[1]} | {doc[2]} | {doc[3]} | {doc[4]} | {doc[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace deliverable rows
    deliverables = generate_deliverables()
    for d in deliverables:
        row_pattern = r'\|\s*\|\s*☐.*☐\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {d[0]} | {d[1]} | {d[2]} | {d[3]} | {d[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace project data rows
    data = generate_project_data()
    for row in data:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace archive metadata
    metadata = generate_archive_metadata()
    content = re.sub(r'\|\s*Project ID\s*\|\s*\|\n', f"| Project ID | {metadata['project_id']} |\n", content)
    content = re.sub(r'\|\s*Project Start Date\s*\|\s*\|\n', f"| Project Start Date | {metadata['start_date']} |\n", content)
    content = re.sub(r'\|\s*Project End Date\s*\|\s*\|\n', f"| Project End Date | {metadata['end_date']} |\n", content)
    content = re.sub(r'\|\s*Total Budget\s*\|\s*\|\n', f"| Total Budget | {metadata['total_budget']} |\n", content)
    content = re.sub(r'\|\s*Number of deliverables\s*\|\s*\|\n', f"| Number of deliverables | {metadata['num_deliverables']} |\n", content)
    content = re.sub(r'\|\s*Number of documents\s*\|\s*\|\n', f"| Number of documents | {metadata['num_documents']} |\n", content)
    content = re.sub(r'\|\s*Archive size \(GB/TB\)\s*\|\s*\|\n', f"| Archive size (GB/TB) | {metadata['archive_size']} |\n", content)
    content = re.sub(r'\|\s*Archive format\s*\|\s*☐.*☐.*☐\s*\n',
                    f"| Archive format | ☐ Digital ☐ Physical ☑ Both |\n", content)
    content = re.sub(r'\|\s*Encryption\s*\|\s*☐.*☐\s*\n',
                    f"| Encryption | ☐ No ☑ Yes |\n", content)
    
    # Replace retention policy rows
    retention = generate_retention_policy()
    for row in retention:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace compliance rows
    compliance = generate_compliance()
    for row in compliance:
        row_pattern = r'\|\s*\|\s*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace access control rows
    access = generate_access_control()
    for row in access:
        row_pattern = r'\|\s*\|\s*☐.*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace access procedure
    content = re.sub(r'\*\*Procedure\*\*:\s*\n', f"**Procedure**: {generate_access_procedure()}\n", content)
    
    # Replace indexing fields
    indexing = generate_indexing()
    content = re.sub(r'\|\s*Project name\s*\|\s*\|\n', f"| Project name | {indexing['project_name']} |\n", content)
    content = re.sub(r'\|\s*Client name\s*\|\s*\|\n', f"| Client name | {indexing['client_name']} |\n", content)
    content = re.sub(r'\|\s*Industry sector\s*\|\s*\|\n', f"| Industry sector | {indexing['industry_sector']} |\n", content)
    content = re.sub(r'\|\s*Key technologies\s*\|\s*\|\n', f"| Key technologies | {indexing['key_technologies']} |\n", content)
    content = re.sub(r'\|\s*Team members\s*\|\s*\|\n', f"| Team members | {indexing['team_members']} |\n", content)
    content = re.sub(r'\|\s*Keywords\s*\|\s*\|\n', f"| Keywords | {indexing['keywords']} |\n", content)
    
    # Replace transfer checklist rows
    checklist = generate_transfer_checklist()
    for row in checklist:
        row_pattern = r'\|\s*\|\s*☐\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace archive location details
    locations = generate_archive_locations()
    content = re.sub(r'\*\*Primary Storage\*\*:\s*\n', f"**Primary Storage**: {locations['primary']}\n", content)
    content = re.sub(r'\*\*Secondary Storage \(Backup\)\*\*:\s*\n', f"**Secondary Storage (Backup)**: {locations['secondary']}\n", content)
    content = re.sub(r'\*\*Offsite Storage\*\*:\s*☐.*☐\s*\n', f"**Offsite Storage**: ☑ Yes ☐ No\n", content)
    content = re.sub(r'\*\*Location\*\*:\s*\n', f"**Location**: {locations['location']}\n", content)
    
    # Replace destruction policy rows
    destruction = generate_destruction_policy()
    for row in destruction:
        row_pattern = r'\|\s*\|\s*\|\s*☐.*☐.*☐\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n"
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
    output_path = Path(__file__).parent.parent / "pm-270-project-archiving-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")