# PM Skill Invocation Patterns

## How to Call PM Skills

PM skills are callable as **Hermes skills**, NOT as slash commands. They surface via natural language or the skill loader — not via `/pm-risk-identification`.

### Quick CLI Wrapper (recommended for power users)

Create `/home/thomas/.local/bin/pm`:

```bash
#!/bin/bash
SKILL_MAP="
risk-identification:pm-120-risk-identification
status-report:pm-290-status-reporting
sprint-planning:pm-190-sprint-planning
..."
INPUT_CMD="$1"; shift
# look up short name → full skill name
hermes chat -s "$SKILL_FULL" -q "$*"
```

Usage:
```bash
pm risk-identification "Summarize the scoring matrix"
pm status-report        # opens interactive session with skill loaded
```

Run `pm` without args to list all 37 available commands.

### Direct Hermes

```bash
hermes chat -s pm-120-risk-identification -q "Summarize the risk scoring matrix"
```

### Natural Language (no setup)

Just describe what you need:
- "Generate a risk register for our IT project"
- "Draft the weekly status report for the API Gateway migration"
- "Build a sprint burndown chart for sprint 27"

Hermes loads the appropriate pm-* skill automatically based on the task.

## What DOES NOT Work

❌ `pm risk-identification` if the script isn't on `$PATH`
❌ `hermes risk-identification` — that's not a CLI subcommand
❌ `/risk-identification` in chat — that's not a slash command

PM skills live in `~/.hermes/skills/productivity/pm-*/SKILL.md` and are loaded via `-s` or natural language trigger.

## Automation Tier Decision Guide

| Tier | Call Style |
|------|-----------|
| Tier 1 (Hermes does it, human reviews) | Natural language — "generate X" |
| Tier 2 (Hermes drafts, human refines) | `pm <command>` for speed |
| Tier 3 (Hermes surfaces options) | `hermes chat -s <skill>` for full control |