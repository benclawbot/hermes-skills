# System Health Check

Quick diagnostic to run when Thomas says "check your system", "system status", "is everything running", or similar. Catches gateway issues, cron failures, disk pressure, and skill rot before they become problems.

## One-shot checklist

```bash
# 1. Gateway log — last 50 lines, check for errors
tail -50 ~/.hermes/logs/gateway.log

# 2. Cron jobs — all should be ok or running
hermes cron list

# 3. System resources
df -h ~ | tail -1          # disk free
free -h | tail -3          # memory + swap
systemctl --user status hermes-gateway 2>&1 | head -15  # gateway alive?

# 4. Session store size
du -sh ~/.hermes/sessions/
find ~/.hermes/sessions/ -name "*.json" ! -name "sessions.json" | wc -l

# 5. Skill inventory — detect empty or stale skills
for d in ~/.hermes/skills/*/; do
  name=$(basename "$d")
  count=$(find "$d" -type f 2>/dev/null | wc -l)
  has_skill=$([ -f "$d/SKILL.md" ] && echo "YES" || echo "no")
  has_desc=$([ -f "$d/DESCRIPTION.md" ] && echo "YES" || echo "no")
  [ "$count" -eq 0 ] || [ "$has_skill" = "no" ] && [ "$has_desc" = "no" ] && echo "EMPTY/SHELL: $name ($count files)"
done

# 6. RTK gain
rtk gain 2>/dev/null || echo "rtk not found in PATH"
```

## Triage rules

| Finding | Action |
|---------|--------|
| Gateway log shows ERROR/WARNING | Investigate, fix, restart gateway |
| Cron job last_status ≠ ok | Run job manually, diagnose, apply 5 Whys |
| Disk < 20% free | Enable `auto_prune: true` in config.yaml, run `hermes sessions prune` |
| Sessions folder > 200MB | Enable `auto_prune: true`, check `retention_days` setting |
| Empty skill dir (0 files, no SKILL.md) | Remove — skeleton skills cause confusion |
| RTK hook not installed for Claude Code | Run `rtk init -g --auto-patch` for Claude Code specifically |
| Telegram polling conflict in logs | Self-resolves once — repeated conflicts = investigate |

## Improvement areas to flag

For detailed triage classification (active vs inactive vs category-directory skills), see `references/skill-audit.md`.