# Sandy Scenarios — Deployed Library

## Location
`~/.hermes/sandy/scenarios/`

## Cron Job Scenarios (6 — migrated from shell/python scripts)

| Scenario File | Cron Job | Deliver | Description |
|---------------|----------|---------|-------------|
| `system-anomaly-watchdog.json` | `system-anomaly-watchdog` | origin | Runs `watch_anomalies.py` every 30min; alerts on anomaly detection |
| `project-health-watchdog.json` | `project-health-watchdog` | origin | Runs `watch_repos.py` every 2hr; auto-commits + reports CI failures |
| `obsidian-vault-backup.json` | `obsidian-vault-backup` | local | Runs `backup_obsidian.sh` daily 9am; commits + pushes vault to backup repo |
| `vault-weekly-digest.json` | `vault-weekly-digest` | local | Runs `vault-digest.py` Mondays 8pm; scans vault + builds weekly digest |
| `session-to-obsidian-watchdog.json` | `session-to-obsidian watchdog` | local | Runs `watch_sessions.py` every 15min; saves Hermes sessions to Obsidian |
| `daily-ai-digest.json` | `daily-ai-digest` | origin | Fetches HN/AI news + GitHub trending every day 6am |

## Ad-hoc Scenarios (2 — created as examples)

| Scenario File | Steps | Description |
|---------------|-------|-------------|
| `disk-space-check.json` | 2 | Check disk usage, conditional alert if above threshold |
| *(template)* | — | Copy and modify for new deterministic workflows |

## Wrapper Scripts

`~/.hermes/scripts/` contains Sandy wrapper shells:
- `watch_anomalies_sandy.sh` → `system-anomaly-watchdog.json`
- `watch_repos_sandy.sh` → `project-health-watchdog.json`
- `backup_obsidian_sandy.sh` → `obsidian-vault-backup.json`
- `vault-digest_sandy.sh` → `vault-weekly-digest.json`
- `watch_sessions_sandy.sh` → `session-to-obsidian-watchdog.json`
- `daily-ai-digest.sh` → `daily-ai-digest.json`

All wrappers follow the same pattern — silent on success, with 5-whys auto-fix on failure:
```bash
#!/bin/bash
# Silent on success (no output = no notification).
# On failure: 5-whys auto-fix loop, then propagate to stderr for notification.
PYTHON="/home/thomas/Desktop/hermes-agent/.venv/bin/python3"

output=$($PYTHON /home/thomas/.hermes/skill-assets/sandy/scripts/play.py ~/.hermes/sandy/scenarios/$(basename $0 .sh | sed 's/_sandy//').json 2>&1)
[ $? -eq 0 ] && exit 0

# Failure — attempt auto-fix
if echo "$output" | grep -q "ModuleNotFoundError"; then
    MODULE=$(echo "$output" | grep -oP "No module named '\K[^']+")
    [ -n "$MODULE" ] && uv pip install --python "$PYTHON" "$MODULE" 2>/dev/null
    $PYTHON /home/thomas/.hermes/skill-assets/sandy/scripts/play.py ~/.hermes/sandy/scenarios/$(basename $0 .sh | sed 's/_sandy//').json >/dev/null 2>&1
    [ $? -eq 0 ] && exit 0
fi

# Still failing — echo to stderr for cron delivery
echo "$output" >&2
exit 1
```

## Minimal Scenario Template

```json
{
  "version": "2.1",
  "metadata": {"name": "my-task"},
  "variables": {},
  "steps": [
    {
      "step": 1,
      "tool": "claude__bash",
      "id": "step1",
      "params": {"command": "echo hello"},
      "description": "Optional description"
    }
  ]
}
```

## Adding a New Cron Job Scenario

1. Create the JSON: `~/.hermes/sandy/scenarios/my-task.json`
2. Create wrapper: `~/.hermes/scripts/my-task_sandy.sh`
3. Test: `python3 ~/.hermes/skill-assets/sandy/scripts/play.py ~/.hermes/sandy/scenarios/my-task.json --debug`
4. Update cron job: `cron job update --job-id <id> --script my-task_sandy.sh`