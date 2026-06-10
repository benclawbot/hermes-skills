#!/usr/bin/env python3
"""Generate PM-230 Procurement Planning document from template."""

import re
from pathlib import Path

def generate_project_name():
    return "Project Alpha - Enterprise System Upgrade"

def generate_procurement_lead():
    return "Sarah Mitchell"

def generate_date():
    from datetime import date
    return date.today().strftime("%Y-%m-%d")

def generate_procurement_objectives():
    return [
        "Acquire qualified vendors for software licensing and hardware procurement",
        "Negotiate favorable contract terms ensuring cost-effectiveness",
        "Establish reliable supply chain for timely delivery of components"
    ]

def generate_items_procured():
    return [
        ("1", "Enterprise Software Licenses", "50", "$125,000", "High", "Core business functionality"),
        ("2", "Server Hardware", "10 units", "$75,000", "High", "Infrastructure capacity"),
        ("3", "Network Equipment", "5 units", "$25,000", "Medium", "Network upgrade"),
    ]

def generate_vendors():
    return [
        ("TechCorp Solutions", "Strong reputation, 24/7 support", "Premium pricing", "$150,000", "A"),
        ("GlobalTech Inc", "Competitive pricing, fast delivery", "Limited local support", "$130,000", "B"),
        ("VendorC", "Innovative solutions", "Smaller company risk", "$140,000", "B+"),
    ]

def generate_selection_criteria():
    return [
        ("Cost", "30%", "$140,000", "$135,000", "$145,000"),
        ("Quality", "25%", "Excellent", "Good", "Excellent"),
        ("Delivery", "20%", "4 weeks", "3 weeks", "5 weeks"),
        ("Experience", "15%", "10+ years", "5+ years", "8+ years"),
        ("Support", "10%", "24/7", "Business hours", "24/7"),
    ]

def generate_contract_type():
    return [
        ("Software Licenses", "Fixed Price", "Predictable cost, minimal risk"),
        ("Hardware", "Time & Materials", "Flexibility for scope changes"),
        ("Services", "Cost Plus", "Transparency on labor costs"),
    ]

def generate_contract_terms():
    return {
        "payment_terms": "Net 30 days",
        "delivery_schedule": "4-6 weeks from PO",
        "warranty_period": "12 months",
        "penalties_bonuses": "5% bonus for early delivery, 2% penalty per week late"
    }

def generate_schedule():
    return [
        ("RFQ/RFP Release", "2026-06-01", "2026-06-15", "Procurement Lead", "Project approval"),
        ("Vendor Selection", "2026-06-16", "2026-07-15", "Selection Committee", "RFQ/RFP responses"),
        ("Contract Negotiation", "2026-07-16", "2026-07-31", "Legal + Procurement", "Vendor selection"),
        ("Contract Approval", "2026-08-01", "2026-08-07", "Executive Sponsor", "Legal review"),
        ("PO Issuance", "2026-08-08", "2026-08-10", "Procurement Lead", "Contract signing"),
    ]

def generate_risks():
    return [
        ("Vendor non-performance", "Medium", "High", "Require performance bonds; establish SLA with penalties"),
        ("Cost overrun", "Low", "High", "Fixed-price contracts where possible; contingency budget"),
        ("Delay in delivery", "Medium", "Medium", "Buffer time in schedule; alternative vendors identified"),
        ("Quality issues", "Low", "High", "Quality requirements in contract; inspection upon delivery"),
    ]

def generate_approvals():
    from datetime import date
    return [
        ("Project Manager", "John Davidson", "_____________", date.today().strftime("%Y-%m-%d")),
        ("Procurement Lead", "Sarah Mitchell", "_____________", date.today().strftime("%Y-%m-%d")),
        ("Finance", "Robert Chen", "_____________", date.today().strftime("%Y-%m-%d")),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace simple field placeholders
    content = re.sub(r'\*\*Project Name\*\*:\s*\n', f'**Project Name**: {generate_project_name()}\n', content)
    content = re.sub(r'\*\*Procurement Lead\*\*:\s*\n', f'**Procurement Lead**: {generate_procurement_lead()}\n', content)
    content = re.sub(r'\*\*Date\*\*:\s*\n', f'**Date**: {generate_date()}\n', content)
    
    # Replace objectives
    objectives = generate_procurement_objectives()
    for i, obj in enumerate(objectives, 1):
        content = re.sub(r'(\d+)\.\s*\n', f'{i}. {obj}\n', content, count=1)
    
    # Replace items to be procured table rows
    items = generate_items_procured()
    for item in items:
        row_pattern = r'\|\s*\d+\s*\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {item[0]} | {item[1]} | {item[2]} | {item[3]} | {item[4]} | {item[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace vendor rows
    vendors = generate_vendors()
    for vendor in vendors:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {vendor[0]} | {vendor[1]} | {vendor[2]} | {vendor[3]} | {vendor[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace selection criteria rows
    criteria = generate_selection_criteria()
    for criterion in criteria:
        row_pattern = r'\|\s*\|\s*%\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {criterion[0]} | {criterion[1]} | {criterion[2]} | {criterion[3]} | {criterion[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace contract type rows
    contracts = generate_contract_type()
    for contract in contracts:
        row_pattern = r'\|\s*\|\s*☐.*☐.*☐\s*\|\s*\n'
        checkbox_str = "☐ Fixed Price ☐ Time & Materials ☐ Cost Plus"
        if contract[1] == "Fixed Price":
            checkbox_str = "☐ Fixed Price ☑ Time & Materials ☐ Cost Plus"
        elif contract[1] == "Time & Materials":
            checkbox_str = "☐ Fixed Price ☑ Time & Materials ☐ Cost Plus"
        else:
            checkbox_str = "☐ Fixed Price ☐ Time & Materials ☑ Cost Plus"
        row_replacement = f"| {contract[0]} | {checkbox_str} | {contract[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace contract terms
    terms = generate_contract_terms()
    content = re.sub(r'\*\*Payment Terms\*\*:\s*\n', f"**Payment Terms**: {terms['payment_terms']}\n", content)
    content = re.sub(r'\*\*Delivery Schedule\*\*:\s*\n', f"**Delivery Schedule**: {terms['delivery_schedule']}\n", content)
    content = re.sub(r'\*\*Warranty Period\*\*:\s*\n', f"**Warranty Period**: {terms['warranty_period']}\n", content)
    content = re.sub(r'\*\*Penalties/Bonuses\*\*:\s*\n', f"**Penalties/Bonuses**: {terms['penalties_bonuses']}\n", content)
    
    # Replace schedule rows
    schedule = generate_schedule()
    for row in schedule:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace risk rows
    risks = generate_risks()
    for risk in risks:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {risk[0]} | {risk[1]} | {risk[2]} | {risk[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace approval rows
    approvals = generate_approvals()
    for approval in approvals:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {approval[0]} | {approval[1]} | {approval[2]} | {approval[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    return content

if __name__ == "__main__":
    import sys
    
    template_path = Path(__file__).parent / "template.md"
    output_path = Path(__file__).parent.parent / "pm-230-procurement-planning-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")
