# Skill Authoring Guide

*Absorbed from `hermes-agent-skill-authoring` — see that skill for full details.*

## Two Skill Trees

| Tree | Location | Creation method |
|------|----------|-----------------|
| User-local | `~/.hermes/skills/<category>/<name>/` | `skill_manage(action='create')` |
| In-repo (shipped) | `/home/bb/hermes-agent/skills/<category>/<name>/` | `write_file` + `git add` |

## Required Frontmatter

Source: `tools/skill_manager_tool.py::_validate_frontmatter`

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars
description: Use when <trigger>. <one-line behavior>.  # ≤1024 chars
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

## Size Limits

- Description: ≤ 1024 chars
- Full SKILL.md: ≤ 100,000 chars
- Peer skills in `software-development/`: 8-14k chars. If pushing past 20k, split into `references/*.md`.

## Peer-Matched Structure

```
# <Title>

## Overview
## When to Use
## <Topic sections>
## Common Pitfalls
## Verification Checklist
## One-Shot Recipes (optional)
```

## In-Repo Workflow

1. Survey peers: `ls skills/<category>/`
2. Draft with `write_file` to `skills/<category>/<name>/SKILL.md`
3. Validate locally (YAML frontmatter + size limits)
4. `git add skills/<category>/<name>/ && git commit`

## Key Rules

- **Never use `skill_manage(action='create')` for in-repo skills** — writes to `~/.hermes/skills/`, not the repo tree
- Frontmatter must start at byte 0 with `---` (no leading blank line)
- Descriptions must start with "Use when ..."
- Prefer extending existing skills over creating narrow siblings
- `related_skills` references from in-repo to user-local won't resolve for other users
