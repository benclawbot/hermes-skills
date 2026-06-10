# Hermes Performance Optimization

Applied in session 2026-05-05. Fast/slim/effective config for daily-use Hermes.

## Config Changes Applied

```bash
hermes config set compression.enabled true
hermes config set compression.threshold 0.40
hermes config set compression.target_ratio 0.15
hermes config set agent.max_turns 45
hermes config set display.show_reasoning false
hermes config set display.show_cost false
hermes config set memory.memory_enabled true    # re-enabled after user request
hermes config set checkpoints.enabled false
hermes config set security.redact_secrets false
```

## Impact Summary

| Setting | Default | New | Effect |
|---------|---------|-----|--------|
| compression.threshold | 0.50 | 0.40 | compress earlier |
| compression.target_ratio | 0.20 | 0.15 | leaner context |
| agent.max_turns | 90 | 45 | cut long loops off sooner |
| display.show_reasoning | true | false | less output noise |
| display.show_cost | true | false | less output noise |
| checkpoints.enabled | true | false | no /rollback overhead |
| security.redact_secrets | true | false | no parsing/masking latency |

**Note:** `memory.memory_enabled` was disabled then re-enabled per user preference.

**Honcho memory provider is NOT running.** Despite being configured in `config.yaml`, the Honcho backend process is not active. Session summaries are NOT being written to Obsidian automatically by the framework. The `save-session-to-obsidian` skill (watchdog cron + `watch_sessions.py`) is the working replacement for this functionality.

## Toolsets Disabled

```bash
for tool in browser image_gen video moa rl spotify yuanbao; do
  hermes tools disable "$tool"
done
```

Re-enable with `hermes tools enable <name>`.

## Skill Directories Pruned

Deleted unused skill categories from `~/.hermes/skills/`:
- creative, data-science, devops, diagramming, domain, email, gaming, gifs, inference-sh, media, mlops, red-teaming, research, smart-home, social-media, yuanbao, apple

**Keep:** autonomous-ai-agents, dogfood, github, mcp, note-taking, productivity, software-development

## Rationale
- Smaller context = faster LLM calls + lower token cost
- Disabled features that add parsing overhead (secret redaction, checkpoints)
- `max_turns: 45` is enough for most tasks without runaway loops
- Re-enabling memory because user wants cross-session persistence
