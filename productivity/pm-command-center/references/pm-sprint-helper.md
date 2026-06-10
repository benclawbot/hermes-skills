---
name: pm-sprint-helper
description: Sprint planning prep and status report drafting for Senior IT PM workflows. Loads sprint data, velocity history, and backlog context to auto-generate planning inputs and weekly status reports. Use when Thomas asks to prep a sprint plan, draft a status report, or review sprint health.
version: 1.0.0
metadata:
  hermes:
    tags: [project-management, scrum, sprint, reporting, automation]
    trigger: [sprint planning, status report, sprint review, weekly status, sprint prep, backlog review, sprint health]
    trigger_context: "Thomas as a Senior IT PM preparing for sprint planning, writing weekly status reports, or reviewing sprint health"
---

# PM Sprint Helper

A skill for automating sprint preparation and recurring PM reporting for Senior IT PM workflows.

## What it does

1. **Sprint Planning Prep** — Before the sprint planning meeting, generate:
   - Capacity calculation (team availability, planned time off, holidays)
   - Velocity trend (last 5 sprints, average, trend direction)
   - Recommended sprint commitment (based on velocity + capacity)
   - Top backlog items pre-loaded with acceptance criteria
   - Sprint goal draft from backlog context

2. **Weekly Status Report** — Draft a status report for stakeholder distribution:
   - Sprint progress summary (burndown, velocity, stories completed)
   - Blockers and impediments
   - Risks that have emerged
   - Next week's plan
   - Format: plain text suitable for email, Teams, or Linear comment

3. **Sprint Health Check** — Mid-sprint health snapshot:
   - Current burndown vs ideal
   - Days remaining vs work remaining
   - Blockers count and age
   - Scope creep flag (items added mid-sprint)
   - Recommendation: on-track / at-risk / compromised

## Data sources

The skill reads from project data files in these locations (Thomas's conventions):

```
~/.hermes/pm-data/
├── team-roster.yaml        # Team members, roles, availability %
├── sprint-velocity.csv     # Historical velocity: sprint, committed, completed, dates
├── active-projects.yaml    # Current projects with status, owner, stage
└── sprint-backlog/         # Per-sprint folder with backlog items
    ├── sprint-25-backlog.md
    └── sprint-26-planning.md
```

**To set up for a new project:**
1. Create `~/.hermes/pm-data/active-projects.yaml` with current project info
2. Seed `sprint-velocity.csv` with at least 3 sprints of history
3. Create a `sprint-backlog/sprint-XX-planning.md` for the upcoming sprint

## Sprint Planning Prep — Step by Step

### Step 1: Gather team capacity

Read `~/.hermes/pm-data/team-roster.yaml` for each team member's availability % and any leave planned during the sprint.

Calculate:
```
Available person-days = Σ(member_capacity% × working_days_in_sprint)
Example: 5 people × 0.9 avg capacity × 10 working days = 45 person-days
```

### Step 2: Review velocity history

Read `~/.hermes/pm-data/sprint-velocity.csv`. Calculate:
- Average velocity (last 5 sprints)
- Velocity trend (improving / stable / declining)
- Velocity standard deviation (to set forecast range)

### Step 3: Generate commitment recommendation

```
Recommended story points = min(avg_velocity × capacity_factor, median_velocity)
Where capacity_factor = available_person_days / baseline_person_days
```

Flag if the recommendation differs from last sprint's actual by more than 20%.

### Step 4: Draft sprint goal

From the top 3-5 backlog items, synthesize a single sprint goal sentence:

> "Deliver [feature category] including [key item 1] and [key item 2], enabling [business outcome]."

### Step 5: Format planning inputs

Output a markdown-formatted briefing document with all the above sections, ready for the sprint planning meeting.

## Weekly Status Report — Step by Step

### Step 1: Read current sprint data

From `sprint-backlog/sprint-XX-planning.md` or the task system (Linear/Jira if connected via API).

### Step 2: Build sprint progress section

```
Sprint: [ID]  |  Day [N] of [total]
Items completed: [X] / [Y]
Story points: [A] / [B] committed
Burndown: [current remaining] pts vs [ideal remaining] pts
```

### Step 3: Identify blockers

List any open impediments with age and owner. If none, write "No open blockers."

### Step 4: Note new risks

Flag any risks that have emerged or escalated since last report.

### Step 5: Compose report

Assemble into a plain-text report formatted for email/Teams:

```
Subject: Sprint [XX] Status — Week [N]

Sprint Progress: [summary]
Completed: [list of key items done]
Blockers: [list or "None"]
Upcoming: [next week's plan]
Risks: [list or "None"]
```

## Sprint Health Check — Decision Logic

```
IF days_remaining / total_days < work_remaining / total_work:
  → "AT RISK: more work than time remaining"

IF blockers > 0 AND oldest_blocker_age > 3 days:
  → "AT RISK: stale blocker"

IF items_added_mid_sprint > 0:
  → "SCOPE CREEP DETECTED: [N] items added after sprint start"

IF velocity_so_far < projected_velocity × 0.7:
  → "TRACKING BEHIND: recommend scope review"

ELSE:
  → "ON TRACK"
```

## Sprint Health Check — Output Format

```
Sprint [XX] Health Check — [Date]
─────────────────────────────────
Status:        [ON TRACK / AT RISK / COMPROMISED]
Burndown:      [N] pts remaining, [D] days left (ideal: [N] pts)
Velocity pace: [X] pts/day vs 5-sprint avg [Y] pts/day
Blockers:      [N] open, oldest [D] days
Scope changes: [N] items added mid-sprint
Recommendation: [specific action]
```

## Umbrella

This skill is a sub-skill of `project-management`. Load that hub for the full PM SOP inventory and domain context.

## Setup Requirements

- `~/.hermes/pm-data/` directory must exist
- `team-roster.yaml` and `sprint-velocity.csv` must be seeded with project data
- See file templates below

## File Templates

### ~/.hermes/pm-data/team-roster.yaml
```yaml
team:
  - name: "Alice"
    role: "Developer"
    availability: 1.0   # 100%
    timezone: "CET"
  - name: "Bob"
    role: "Developer"
    availability: 0.8   # 80% (part-time)
    timezone: "EST"
```

### ~/.hermes/pm-data/sprint-velocity.csv
```csv
sprint,committed,completed,start_date,end_date
sprint-21,34,31,2026-03-03,2026-03-14
sprint-22,32,33,2026-03-17,2026-03-28
sprint-23,36,30,2026-03-31,2026-04-11
sprint-24,31,34,2026-04-14,2026-04-25
sprint-25,33,32,2026-04-28,2026-05-09
```

### ~/.hermes/pm-data/active-projects.yaml
```yaml
projects:
  - id: "PROJ-001"
    name: "EAP Integration"
    stage: "Execution"
    owner: "Thomas"
    sponsor: "Jane Doe"
    status: "green"  # green/yellow/red
    next_milestone: "2026-05-20"
    next_milestone_name: "UAT Sign-off"
```

## Known Limitations

- This skill does NOT replace the human judgment required for sprint planning conversations — it drafts inputs, the PM decides
- Sprint commitment decisions must be made collaboratively with the team, not auto-generated
- Status reports should always be reviewed before distribution; AI can introduce factual errors
- If no historical velocity data exists, recommendations will be conservative estimates

## Automation Level Summary

| Task | Tier | Notes |
|------|------|-------|
| Capacity calculation | 1-Eliminate | Fully automatable from roster + calendar |
| Velocity trend analysis | 1-Eliminate | Calculated from CSV history |
| Commitment recommendation | 2-Accelerate | AI drafts, human reviews & adjusts |
| Sprint goal drafting | 2-Accelerate | AI drafts from backlog context |
| Weekly status report | 1-Eliminate | Draft from sprint data, human reviews |
| Sprint health check | 2-Accelerate | Auto-analysis, human reviews recommendation |