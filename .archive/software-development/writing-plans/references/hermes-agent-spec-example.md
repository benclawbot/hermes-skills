# Worked Example: Substrate Design Spec for Hermes-Agent

Reference example showing the shape of a real spec produced using this skill
on 2026-06-26. Use it as a template when writing your own plan for hermes-agent.

## Source

Saved at `~/.hermes/hermes-agent/.plans/2026-06-26_205046-xenobot-inspired-substrate-design.md`.

Six tasks, ~790 LOC + ~30 SKILL.md metadata edits. Each task independent, all
additive, all fail-open by default. Common shape across tasks:

```
Task N: <Verb + noun>
  - Objective (1 sentence)
  - Files (Create / Modify / Test — exact paths)
  - Step 1: Write failing test (full code block)
  - Step 2: Run test, expect failure (exact command + expected error)
  - Step 3: Implement (full code block)
  - Step 4: Run test, expect pass
  - Step 5: Manual smoke (exact command + expected output)
  - Step 6: Commit (exact git command)
```

## Conventions Used (hermes-agent-specific)

- **Plans directory**: `.plans/` at project root (NOT `plans/`, NOT `.hermes/plans/`).
- **Filename**: `.plans/YYYY-MM-DD_HHMMSS-<slug>.md`.
- **Source paths in code blocks**: `~/.hermes/hermes-agent/agent/...`, `~/.hermes/hermes-agent/tools/...`, `~/.hermes/hermes-agent/skills/...`. The `~` is intentional — keeps paths readable in the plan body. Implementer resolves to absolute.
- **Test paths**: `tests/skills/test_<name>.py` (matches existing convention under `tests/skills/`).
- **Activation**: `cd ~/.hermes/hermes-agent && source .venv/bin/activate` before any `pytest` / `python -c`.
- **Commits**: conventional commits with `feat(...)`, `fix(...)`, `docs(...)` scopes.

## Frontmatter / Scope Pattern (Task 1)

When adding substrate-level constraints to SKILL.md frontmatter:

```yaml
scope:
  paths: ["~/.hermes/skills/**", "/tmp/hermes-scratch/**"]
  paths_deny: ["~/.ssh/**", "~/.gnupg/**"]
  allowed_tools: ["terminal", "read_file", "write_file"]
  allowed_child_skills: ["other-skill", "research/last30days"]
  max_tokens: 8000
```

All constraints fail OPEN — empty list / missing key = no constraint. Validator
only REJECTS malformed values, never requires presence. This is critical: it
means existing skills keep working without edits.

## Status Convention

| Marker | Meaning |
|---|---|
| 🟢 | Pure additive — no breaking changes |
| 🟡 | Additive but introduces a new enforcement boundary |

Used in the task index table. Optional but helps reviewers triage.

## Task Sizing Math

- Each task should be implementable end-to-end in one focused session (15-45 min).
- 2-5 minute steps inside each task are the unit.
- 6 tasks at this granularity is the sweet spot for `subagent-driven-development`
  to execute without losing context between dispatches.

## What This Plan Did NOT Do (YAGNI reminders)

- Did not introduce new dependencies.
- Did not change `run_agent.py` core loop.
- Did not add telemetry / metrics (left to a separate spec).
- Did not auto-install anything on `setup.sh` (user wires their own cron specialists).
- Did not bundle a `--dry-run` flag into memory TTL (asked as open question instead).

## Open-Questions Section Is Not Optional

End every plan with a "Risks & Tradeoffs" + "Open Questions for the User
Before Implementation" section. The implementer (or subagent) cannot make
UX-affecting decisions on your behalf. List them, offer defaults, and confirm
before dispatching subagents.