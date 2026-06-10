#!/usr/bin/env python3
"""Generate PM-330 Quality Assurance Deliverables document from template."""

import re
from pathlib import Path

def generate_sprint_info():
    return {
        "sprint": "Sprint 14",
        "qa_lead": "Elena Rodriguez",
        "date": "2026-05-20"
    }

def generate_test_deliverables():
    return [
        ("Unit Testing", "Complete", "James Wilson"),
        ("Integration Testing", "In Progress", "Sarah Chen"),
        ("System Testing", "In Progress", "Marcus Johnson"),
        ("UAT Coordination", "Not Started", "Elena Rodriguez"),
        ("Performance Testing", "Not Started", "DevOps Team"),
    ]

def generate_test_results():
    return {
        "coverage_target": "85",
        "coverage_actual": "82",
        "defect_density": "0.3",
        "critical": "0",
        "high": "2",
        "medium": "7",
        "low": "12"
    }

def generate_defects():
    return [
        ("DEF-101", "Login session timeout", "High", "High", "Open", "James Wilson", "2026-05-22"),
        ("DEF-102", "Report export formatting", "Medium", "Medium", "In Progress", "Sarah Chen", "2026-05-21"),
        ("DEF-103", "API response latency", "High", "High", "Open", "Marcus Johnson", "2026-05-23"),
    ]

def generate_quality_gates():
    return [
        ("Code Review", "Complete", "David Park"),
        ("Static Analysis", "Complete", "Elena Rodriguez"),
        ("Unit Tests", "Complete", "James Wilson"),
        ("Integration Tests", "In Progress", "Sarah Chen"),
        ("Security Scan", "Complete", "Security Team"),
        ("Performance", "Not Started", "DevOps Team"),
    ]

def generate_environments():
    return [
        ("Dev", "Available", "Ready"),
        ("QA", "Available", "Ready"),
        ("Staging", "Available", "Not Ready"),
        ("Production", "Restricted", "Not Ready"),
    ]

def generate_signoffs():
    from datetime import date
    return [
        ("Backend Services Module", "Elena Rodriguez", "Maria Santos", date.today().strftime("%Y-%m-%d")),
        ("Frontend Components", "Elena Rodriguez", "Maria Santos", date.today().strftime("%Y-%m-%d")),
    ]

def generate_action_items():
    from datetime import date, timedelta
    return [
        ("Fix critical DEF-101 by sprint end", "James Wilson", (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")),
        ("Complete integration testing for API layer", "Sarah Chen", (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")),
        ("Set up staging environment", "Marcus Johnson", (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace sprint info
    info = generate_sprint_info()
    content = re.sub(r'\*\*Sprint:\*\*\s*\n', f'**Sprint:** {info["sprint"]}\n', content)
    content = re.sub(r'\*\*QA Lead:\*\*\s*\n', f'**QA Lead:** {info["qa_lead"]}\n', content)
    content = re.sub(r'\*\*Date:\*\*\s*\n', f'**Date:** {info["date"]}\n', content)
    
    # Replace test deliverables rows
    deliverables = generate_test_deliverables()
    for d in deliverables:
        row_pattern = r'\|\s*\d+\s*\|[^|]*\|[^|]*☐[^|]*\|[^|]*\|[^|]*\|\n'
        status_checkbox = {
            "Not Started": "☐ Not Started ☐ In Progress ☐ Complete",
            "In Progress": "☐ Not Started ☑ In Progress ☐ Complete",
            "Complete": "☐ Not Started ☐ In Progress ☑ Complete"
        }.get(d[1], "☐ Not Started ☐ In Progress ☐ Complete")
        row_replacement = f"| {deliverables.index(d) + 1} | {d[0]} | {d[2]} | {status_checkbox} | {d[2]} | {info['date']} | On track |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace test results
    results = generate_test_results()
    content = re.sub(r'\|\s*Test Coverage\s*\|\s*%', f"| Test Coverage | {results['coverage_target']}%", content)
    content = re.sub(r'\|\s*Test Coverage\s*\|\s*%[^|]*\|\s*%', f"| Test Coverage | {results['coverage_target']}% | {results['coverage_actual']}%", content)
    content = re.sub(r'\|\s*Defect Density\s*\|[^|]*\|[^|]*\|\s*☐', f"| Defect Density | {results['defect_density']} | {results['defect_density']} | ☑", content)
    content = re.sub(r'\|\s*Critical Defects\s*\|[^|]*\|\s*\|\s*☐', f"| Critical Defects | 0 | {results['critical']} | ☑", content)
    content = re.sub(r'\|\s*High Defects\s*\|[^|]*\|[^|]*\|\s*☐', f"| High Defects | {results['high']} | {results['high']} | ☐", content)
    content = re.sub(r'\|\s*Medium Defects\s*\|[^|]*\|[^|]*\|\s*☐', f"| Medium Defects | {results['medium']} | {results['medium']} | ☐", content)
    content = re.sub(r'\|\s*Low Defects\s*\|[^|]*\|[^|]*\|\s*☐', f"| Low Defects | {results['low']} | {results['low']} | ☑", content)
    
    # Replace defect log rows
    defects = generate_defects()
    for defect in defects:
        row_pattern = r'\|\s*\|[^|]*☐[^|]*☐[^|]*☐[^|]*☐[^|]*\|[^|]*\|[^|]*\|[^|]*\|\n'
        severity_checkbox = {
            "Critical": "☑ Critical ☐ High ☐ Medium ☐ Low",
            "High": "☐ Critical ☑ High ☐ Medium ☐ Low",
            "Medium": "☐ Critical ☐ High ☑ Medium ☐ Low",
            "Low": "☐ Critical ☐ High ☐ Medium ☑ Low",
        }.get(defect[2], "☐ Critical ☐ High ☐ Medium ☐ Low")
        priority_checkbox = {
            "High": "☑ High ☐ Medium ☐ Low",
            "Medium": "☐ High ☑ Medium ☐ Low",
            "Low": "☐ High ☐ Medium ☑ Low",
        }.get(defect[3], "☐ High ☐ Medium ☐ Low")
        status = "In Progress" if "progress" in defect[4].lower() else defect[4]
        row_replacement = f"| {defect[0]} | {defect[1]} | {severity_checkbox} | {priority_checkbox} | {status} | {defect[5]} | {defect[6]} |跟踪中 |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace quality gates
    gates = generate_quality_gates()
    for gate in gates:
        row_pattern = r'\|[^|]*\|[^|]*☐[^|]*\|\s*\|\n'
        status_checkbox = {
            "Complete": "☐",
            "In Progress": "☐",
            "Not Started": "☐"
        }.get(gate[1], "☐")
        complete_mark = "☑" if gate[1] == "Complete" else "☐"
        row_replacement = f"| {gate[0]} | {gate[2]} | {complete_mark} | {gate[2][0] if gate[2] else 'N/A'} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace environment rows
    envs = generate_environments()
    for env in envs:
        row_pattern = r'\|[^|]*\|[^|]*☐[^|]*☐[^|]*\|\s*\|\n'
        ready_checkbox = "☑ Ready ☐ Not Ready" if env[2] == "Ready" else "☐ Ready ☑ Not Ready"
        row_replacement = f"| {env[0]} | {env[1]} | {ready_checkbox} | 配置完成 |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace sign-off rows
    signoffs = generate_signoffs()
    for signoff in signoffs:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {signoff[0]} | {signoff[1]} | {signoff[2]} | {signoff[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace action items
    actions = generate_action_items()
    for action in actions:
        row_pattern = r'\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {action[0]} | {action[1]} | {action[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    return content

if __name__ == "__main__":
    import sys
    
    template_path = Path(__file__).parent / "template.md"
    output_path = Path(__file__).parent.parent / "pm-330-quality-assurance-deliverables-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")