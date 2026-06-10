#!/usr/bin/env python3
"""Generate PM-340 Burndown Chart Tracking document from template."""

import re
from pathlib import Path

def generate_sprint_info():
    return {
        "sprint": "Sprint 14",
        "start_date": "2026-05-06",
        "end_date": "2026-05-20",
        "team": "Alpha Development Team"
    }

def generate_burndown_data():
    return [
        (0, "2026-05-06", 100, 100, 0, "Sprint Start"),
        (1, "2026-05-07", 93, 95, -2, ""),
        (2, "2026-05-08", 86, 88, -2, ""),
        (3, "2026-05-09", 79, 82, -3, ""),
        (4, "2026-05-10", 72, 75, -3, ""),
        (5, "2026-05-11", 65, 68, -3, ""),
        (6, "2026-05-12", 58, 60, -2, ""),
        (7, "2026-05-13", 51, 52, -1, "Standup"),
        (8, "2026-05-14", 44, 46, -2, ""),
        (9, "2026-05-15", 37, 38, -1, ""),
        (10, "2026-05-16", 30, 32, -2, ""),
        (11, "2026-05-17", 23, 25, -2, ""),
        (12, "2026-05-18", 16, 18, -2, ""),
        (13, "2026-05-19", 9, 12, -3, ""),
        (14, "2026-05-20", 2, 5, -3, "Sprint End"),
    ]

def generate_sprint_scope():
    return {
        "total_points": 100,
        "stories_committed": 24,
        "stories_completed": 21,
        "points_completed": 87
    }

def generate_velocity_analysis():
    return [
        ("Sprint N-3", 92, 88, 88, -4),
        ("Sprint N-2", 95, 91, 91, -4),
        ("Sprint N-1", 98, 94, 94, -4),
        ("Sprint N", 100, 87, 87, -13),
        ("Average", 96.25, 90, 90, -6),
    ]

def generate_team_performance():
    return [
        ("Alice Johnson", 25, 22, 88),
        ("Bob Smith", 25, 21, 84),
        ("Carol Williams", 25, 23, 92),
        ("David Brown", 25, 21, 84),
    ]

def generate_scope_changes():
    from datetime import date
    return [
        (date.today().strftime("%Y-%m-%d"), "Add", 5, "Emergency feature request", "Product Owner"),
        (date.today().strftime("%Y-%m-%d"), "Remove", 3, "Out of scope", "Product Owner"),
    ]

def generate_risk_items():
    return [
        ("Integration complexity with legacy system", "Medium", "Assigned dedicated integration resource"),
        ("Key developer availability in final days", "High", "Cross-training and documentation"),
    ]

def generate_predictions():
    return {
        "on_track": "May 20, 2026",
        "on_track_conf": 85,
        "current_pace": "May 21, 2026",
        "current_pace_conf": 70,
        "best_case": "May 20, 2026",
        "best_case_conf": 95,
        "worst_case": "May 22, 2026",
        "worst_case_conf": 50,
    }

def generate_action_items():
    from datetime import date, timedelta
    return [
        ("Complete story SU-142 code review", "Alice Johnson", (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")),
        ("Update sprint board for scope changes", "Bob Smith", (date.today()).strftime("%Y-%m-%d")),
    ]

def fill_template(template_path: str) -> str:
    content = Path(template_path).read_text()
    
    # Replace sprint info
    info = generate_sprint_info()
    content = re.sub(r'\*\*Sprint:\*\*\s*\n', f'**Sprint:** {info["sprint"]}\n', content)
    content = re.sub(r'\*\*Start Date:\*\*\s*\n', f'**Start Date:** {info["start_date"]}\n', content)
    content = re.sub(r'\*\*End Date:\*\*\s*\n', f'**End Date:** {info["end_date"]}\n', content)
    content = re.sub(r'\*\*Team:\*\*\s*\n', f'**Team:** {info["team"]}\n', content)
    
    # Replace burndown data rows
    burndown = generate_burndown_data()
    for row in burndown:
        row_pattern = r'\|\s*\d+\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\n'
        row_replacement = f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace sprint scope
    scope = generate_sprint_scope()
    content = re.sub(r'\|\s*Total Story Points Committed\s*\|[^|]*\|', f"| Total Story Points Committed | {scope['total_points']} |", content)
    content = re.sub(r'\|\s*Stories Committed\s*\|[^|]*\|', f"| Stories Committed | {scope['stories_committed']} |", content)
    content = re.sub(r'\|\s*Stories Completed\s*\|[^|]*\|', f"| Stories Completed | {scope['stories_completed']} |", content)
    content = re.sub(r'\|\s*Points Completed\s*\|[^|]*\|', f"| Points Completed | {scope['points_completed']} |", content)
    
    # Replace velocity analysis rows
    velocity = generate_velocity_analysis()
    for v in velocity:
        row_pattern = r'\|\s*Sprint[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\n'
        row_replacement = f"| {v[0]} | {v[1]} | {v[2]} | {v[3]} | {v[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace team performance rows
    team = generate_team_performance()
    for member in team:
        row_pattern = r'\|\s*\|[^|]*\|[^|]*\|[^|]*\|\n'
        row_replacement = f"| {member[0]} | {member[1]} | {member[2]} | {member[3]}% |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace total row
    total_points = sum(m[1] for m in team)
    total_completed = sum(m[2] for m in team)
    content = re.sub(r'\|\s*\*\*Total\*\*\s*\|[^|]*\|[^|]*\|[^|]*\|', f"| **Total** | {total_points} | {total_completed} | 100% |", content)
    
    # Replace scope change rows
    changes = generate_scope_changes()
    for change in changes:
        row_pattern = r'\|\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\n'
        impact_str = f"+{change[2]}" if change[1] == "Add" else f"-{change[2]}"
        row_replacement = f"| {change[0]} | {change[1]} | {impact_str} | {change[3]} | {change[4]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace risk items
    risks = generate_risk_items()
    for risk in risks:
        row_pattern = r'\|\s*\|[^|]*\|[^|]*\|\n'
        row_replacement = f"| {risk[0]} | {risk[1]} | {risk[2]} |\n"
        content = re.sub(row_pattern, row_replacement, content, count=1)
    
    # Replace sprint predictions
    predictions = generate_predictions()
    content = re.sub(r'\|\s*On Track\s*\|[^|]*\|[^|]*%', f"| On Track | {predictions['on_track']} | {predictions['on_track_conf']}%", content)
    content = re.sub(r'\|\s*At Current Pace\s*\|[^|]*\|[^|]*%', f"| At Current Pace | {predictions['current_pace']} | {predictions['current_pace_conf']}%", content)
    content = re.sub(r'\|\s*Best Case\s*\|[^|]*\|[^|]*%', f"| Best Case | {predictions['best_case']} | {predictions['best_case_conf']}%", content)
    content = re.sub(r'\|\s*Worst Case\s*\|[^|]*\|[^|]*%', f"| Worst Case | {predictions['worst_case']} | {predictions['worst_case_conf']}%", content)
    
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
    output_path = Path(__file__).parent.parent / "pm-340-burndown-chart-tracking-output.md"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    filled_content = fill_template(template_path)
    output_path.write_text(filled_content)
    print(f"Generated: {output_path}")