# Skill Audit — Inventory & Triage

Run when: Thomas says "check your system", or during any system health check.

## Audit command

```bash
for d in ~/.hermes/skills/*/; do
  name=$(basename "$d")
  count=$(find "$d" -type f 2>/dev/null | wc -l)
  has_skill=$([ -f "$d/SKILL.md" ] && echo "YES" || echo "no")
  has_desc=$([ -f "$d/DESCRIPTION.md" ] && echo "YES" || echo "no")
  echo "$name: $count files, SKILL.md=$has_skill, DESC=$has_desc"
done
```

## Triage classification

| Type | Meaning | Action |
|------|---------|--------|
| `0 files` | Genuinely empty dir | Remove (rmdir) unless it has subdirectories |
| `DESCRIPTION.md only` | Skeleton/placeholder | Low priority — harmless, document but don't delete |
| `SKILL.md + scripts/` | Fully operational | Active skill |
| `SKILL.md + references/` | Class-level with docs | Active skill |
| Category dir (sub-skills inside) | Not empty — a grouping | Keep. Examples: `software-development/`, `autonomous-ai-agents/`, `communication/`, `github/`, `productivity/`, `research/`, `note-taking/`, `mcp/` |

## Skills that are category directories (NOT empty shells)

These have nested sub-skills inside — do NOT flag as empty or delete:

```
software-development/     → plan, requesting-code-review, spike, subagent-driven-development,
                            test-driven-development, tool-output-compression, writing-plans
communication/           → html-to-telegram, one-question-at-a-time
autonomous-ai-agents/    → claude-code, cronjob-ops, hermes-agent
github/                  → codebase-inspection, github-auth, github-pr-workflow
productivity/            → ~20 sub-skills (airtable, cli-anything, cron-avoid-hammer, deep-research-obsidian,
                            fast-research-digest, google-workspace, linear, maps, nano-pdf, notion,
                            ocr-and-documents, pm-command-center, powerpoint, research-ingestion, sandy,
                            session-continuity, teams-meeting-pipeline, web-design-guidance, youtube-transcriber)
research/                → last30days
note-taking/             → obsidian (sub-skill)
mcp/                     → native-mcp
csl-policy/              → SKILL.md + scripts + policies (active documentation)
```

## Active skills (with SKILL.md, class-level)

These are the primary class-level skills that govern major workflows:

- `memory-vault` — auto-capture preferences/corrections
- `session-reflex` — proactive session recall
- `context-prune` — context truncation
- `csl-policy` — Z3 safety enforcement (plugin not active, documentation only)
- `dogfood` — exploratory QA
- `no-replay` — skip re-acknowledgment
- `one-shot-review` — post-task code review
- `tool-result-summarize` — compress tool output
- `notebooklm-research` — NotebookLM CLI research
- `cron-avoid-hammer` — cron job mistake prevention
- `sandy` — deterministic MCP replay

## Known minimal/inactive skills (DESCRIPTION.md only, no SKILL.md)

These are harmless stubs — don't delete, don't prioritize:
`apple`, `inference-sh`, `domain`, `gaming`, `gifs`, `email`, `media`, `smart-home`, `social-media`, `diagramming`, `creative`, `data-science`, `mlops`, `note-taking` (has obsidian sub-skill)

## csl-policy status

- SKILL.md: comprehensive, up to date
- scripts/: `load_guard.py`, `verify_policies.py` exist
- policies/: `safety.csl`, `agent-behavior.csl`, `workflow.csl` exist
- Plugin (`~/.hermes/plugins/csl_enforce/`): EMPTY — no `__init__.py`, no `plugin.yaml`
- Enforcement: NOT ACTIVE. The Z3 engine is documented but not wired to a running plugin.

## Skill evolution storage

`~/.hermes/.pi/skill-memory.json` — created with structure:
```json
{ "lessons": [], "gaps": [], "patterns": [], "evaluations": [], "sessions": [], "evolutions": [] }
```
No active mining process — storage slot ready for future session-mining cron.