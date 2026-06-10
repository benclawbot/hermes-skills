#!/usr/bin/env python3
"""Generate PM-240 Earned Value Management document from template."""

import re
from pathlib import Path

def generate_project_name():
    return "Project Alpha - Enterprise System Upgrade"

def generate_project_manager():
    return "John Davidson"

def generate_report_period():
    return "May 1 - May 15, 2026"

def generate_report_date():
    from datetime import date
    return date.today().strftime("%Y-%m-%d")

def generate_baseline_data():
    return {
        "planned_value": "$450,000",
        "budget_at_completion": "$500,000"
    }

def generate_current_period():
    return {
        "pv": "$225,000",
        "ev": "$210,000",
        "ac": "$230,000"
    }

def generate_performance_indicators():
    return {
        "cv": "-$20,000",
        "sv": "-$15,000",
        "cpi": "0.91",
        "spi": "0.93",
        "cv_status": "Unfavorable",
        "sv_status": "Unfavorable",
        "budget_status": "Over Budget",
        "schedule_status": "Behind"
    }

def generate_variance_analysis():
    return [
        ("Requirements Definition", "$50,000", "$48,000", "$52,000", "-$4,000", "-$2,000", "Behind Schedule"),
        ("System Design", "$75,000", "$72,000", "$78,000", "-$6,000", "-$3,000", "Behind Schedule"),
        ("Development", "$150,000", "$90,000", "$100,000", "-$10,000", "-$10,000", "Behind Schedule"),
    ]

def generate_eac():
    return {
        "typical": "$549,451",
        "best_case": "$530,000",
        "worst_case": "$570,000"
    }

def generate_tcpi():
    return {
        "to_bac": "1.45",
        "to_eac": "1.35"
    }

def generate_forecasting():
    return {
        "eac": "$549,451",
        "vac": "-$49,451",
        "status": "Over Budget"
    }

def generate_trend_analysis():
    return [
        ("Week 1", "$50,000", "$48,000", "$45,000", "0.96", "0.94"),
        ("Week 2", "$100,000", "$95,000", "$98,000", "0.95", "0.93"),
        ("Week 3", "$175,000", "$162,000", "$185,000", "0.91", "0.90"),
    ]

def generate_root_cause():
    return {
        "cost_variance": "Integration testing revealed more defects than estimated, requiring additional resources",
        "schedule_variance": "Third-party vendor delays impacted dependent tasks"
    }

def generate_recommendations():
    return [
        "Implement pair programming to reduce defect discovery cost",
        "Escalate vendor delivery issues to sponsor for alternative vendor assessment",
        "Add 10% contingency to remaining work packages"
    ]

def generate_approvals():
    from datetime import date
    return [
        ("Project Manager", "John Davidson", "_____________", date.today().strftime("%Y-%m-%d")),
        ("Sponsor", "Maria Garcia", "_____________", date.today().strftime("%Y-%m-%d")),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace basic info
    content = re.sub(r'\*\*Project Name\*\*:\s*\n', f'**Project Name**: {generate_project_name()}\n', content)
    content = re.sub(r'\*\*Project Manager\*\*:\s*\n', f'**Project Manager**: {generate_project_manager()}\n', content)
    content = re.sub(r'\*\*Report Period\*\*:\s*\n', f'**Report Period**: {generate_report_period()}\n', content)
    content = re.sub(r'\*\*Report Date\*\*:\s*\n', f'**Report Date**: {generate_report_date()}\n', content)
    
    # Replace baseline data
    baseline = generate_baseline_data()
    content = re.sub(r'\|\s*Planned Value \(PV\)\s*\|\s*\|\s*\|\n', f"| Planned Value (PV) | {baseline['planned_value']} | |\n", content)
    content = re.sub(r'\|\s*Budget at Completion \(BAC\)\s*\|\s*\|\s*\|\n', f"| Budget at Completion (BAC) | {baseline['budget_at_completion']} | |\n", content)
    
    # Replace current period metrics
    period = generate_current_period()
    content = re.sub(r'\|\s*Planned Value \(PV\)\s*\|\s*\|\s*\|\n', f"| Planned Value (PV) | {period['pv']} | |\n", content)
    content = re.sub(r'\|\s*Earned Value \(EV\)\s*\|\s*\|\s*\|\n', f"| Earned Value (EV) | {period['ev']} | |\n", content)
    content = re.sub(r'\|\s*Actual Cost \(AC\)\s*\|\s*\|\s*\|\n', f"| Actual Cost (AC) | {period['ac']} | |\n", content)
    
    # Replace performance indicators
    indicators = generate_performance_indicators()
    # CV row
    cv_check = "☐ Favorable ☑ Unfavorable"
    content = re.sub(r'\|\s*Cost Variance \(CV\)\s*\|\s*EV - AC\s*\|\s*☐\s*☐\s*\n',
                     f"| Cost Variance (CV) | {indicators['cv']} | {cv_check}\n", content)
    # SV row
    sv_check = "☐ Favorable ☑ Unfavorable"
    content = re.sub(r'\|\s*Schedule Variance \(SV\)\s*\|\s*EV - PV\s*\|\s*☐\s*☐\s*\n',
                     f"| Schedule Variance (SV) | {indicators['sv']} | {sv_check}\n", content)
    # CPI row
    cpi_check = "☐ On Budget ☐ Over Budget ☑ Under Budget"
    content = re.sub(r'\|\s*Cost Performance Index \(CPI\)\s*\|\s*EV / AC\s*\|\s*☐.*☐.*☐\s*\n',
                     f"| Cost Performance Index (CPI) | {indicators['cpi']} | {cpi_check}\n", content)
    # SPI row
    spi_check = "☐ On Schedule ☐ Ahead ☑ Behind"
    content = re.sub(r'\|\s*Schedule Performance Index \(SPI\)\s*\|\s*EV / PV\s*\|\s*☐.*☐.*☐\s*\n',
                     f"| Schedule Performance Index (SPI) | {indicators['spi']} | {spi_check}\n", content)
    
    # Replace variance analysis rows
    var_rows = generate_variance_analysis()
    for row in var_rows:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace EAC rows
    eac = generate_eac()
    content = re.sub(r'\|\s*Typical.*\|\s*AC \+ \(BAC - EV\) / CPI\s*\|\s*\|\n',
                    f"| Typical (AC + (BAC - EV)) | AC + (BAC - EV) / CPI | {eac['typical']} |\n", content)
    content = re.sub(r'\|\s*Best Case.*\|\s*AC \+ \(BAC - EV\)\s*\|\s*\|\n',
                    f"| Best Case (AC + remaining work at budget rate) | AC + (BAC - EV) | {eac['best_case']} |\n", content)
    content = re.sub(r'\|\s*Worst Case.*\|\s*AC \+ \(BAC - EV\) / CPI\s*\|\s*\|\n',
                    f"| Worst Case (AC + remaining work at current rate) | AC + (BAC - EV) / CPI | {eac['worst_case']} |\n", content)
    
    # Replace TCPI rows
    tcpi = generate_tcpi()
    content = re.sub(r'\|\s*TCPI to meet BAC\s*\|\s*\(BAC - EV\) / \(BAC - AC\)\s*\|\s*\|\n',
                    f"| TCPI to meet BAC | (BAC - EV) / (BAC - AC) | {tcpi['to_bac']} |\n", content)
    content = re.sub(r'\|\s*TCPI to meet EAC\s*\|\s*\(EAC - EV\) / \(EAC - AC\)\s*\|\s*\|\n',
                    f"| TCPI to meet EAC | (EAC - EV) / (EAC - AC) | {tcpi['to_eac']} |\n", content)
    
    # Replace forecasting section
    forecast = generate_forecasting()
    content = re.sub(r'\*\*Estimated at Completion \(EAC\)\*\*:\s*\n',
                    f"**Estimated at Completion (EAC)**: {forecast['eac']}\n", content)
    content = re.sub(r'\*\*Project Status\*\*:\s*☐.*☐.*☐\n',
                    f"**Project Status**: ☐ On Budget ☐ Over Budget ☑ Under Budget\n", content)
    
    # Replace trend analysis rows
    trend = generate_trend_analysis()
    for row in trend:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace root cause analysis
    root_cause = generate_root_cause()
    content = re.sub(r'\*\*Cost Variance\*\*:\n\*\*Schedule Variance\*\*:\n',
                    f"**Cost Variance**:\n{root_cause['cost_variance']}\n\n**Schedule Variance**:\n{root_cause['schedule_variance']}\n", content)
    
    # Replace recommendations
    recs = generate_recommendations()
    content = re.sub(r'1\.\s*\n2\.\s*\n', f"1. {recs[0]}\n2. {recs[1]}\n3. {recs[2]}\n", content)
    
    # Replace approvals
    approvals = generate_approvals()
    for approval in approvals:
        row_pattern = r'\|\s*\|\s*\|\s*\|\s*\|\s*\n'
        row_replacement = f"| {approval[0]} | {approval[1]} | {approval[2]} | {approval[3]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    return content

if __name__ == "__main__":
    import sys
    
    template_path = Path(__file__).parent / "template.md"
    output_path = Path(__file__).parent.parent / "pm-240-earned-value-management-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")