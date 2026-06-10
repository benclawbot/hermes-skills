# benclawbot Repo Health Monitoring

Three scripts monitor all 29 benclawbot repos on a weekly schedule (Sundays 10:00). All use the same pattern: `gh` at `/home/thomas/bin/gh`, formatted Markdown output, silent on no issues.

**Canonical gh path:** Always use `/home/thomas/bin/gh` — not `/usr/bin/gh` (doesn't exist on this system).

## Scripts

### `github-pr-digest.py`
- Scans all 29 repos for open PRs + CI status
- Only reports when PRs exist; silent if all repos are clean
- Used by cron: `github-pr-digest_sandy.sh` → delivers to Telegram

### `project-health-digest.py`
- Scans all 29 repos for: CI/workflow status, open issues, local test artifacts
- Uses `gh run list --json name,status,conclusion,updatedAt` for CI
- Uses `gh issue list --json number,title,labels,updatedAt` for issues
- Detects local test artifacts via glob patterns (`test-results/*.xml`, `.pytest_cache/`)
- Used by cron: `project-health-digest_sandy.sh` → delivers to Telegram

### `single-repo-digest.py`
- Single-repo deep dive for a specific benclawbot repo
- Runs `pytest --tb=no -q` locally if available
- Checks `gh pr list`, `gh issue list`, `gh run list`
- Also checks `git log --since="7 days ago"` for local commit count
- Used by cron: `single-repo-digest_sandy.sh` → delivers to Telegram

## Common Pattern

```python
GH_CLI = "/home/thomas/bin/gh"  # Canonical path

def check_gh_auth():
    rc, _, _ = run(f'{GH_CLI} auth status 2>&1')
    return rc == 0

def get_workflow_runs(owner_repo, limit=3):
    rc, out, err = run(
        f'{GH_CLI} run list --repo {owner_repo} --limit {limit} '
        f'--json name,status,conclusion,updatedAt',
        timeout=20
    )
    if rc == 0 and out and out.startswith('['):
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            pass
    return []
```

## Output Format

All three scripts output Thomas-compliant Markdown:
- Bold section headers per repo
- Emoji status indicators (✅ ❌ ⏳ 📋 🧪 📝)
- CI failures formatted as: `❌ workflow-name: conclusion (date)`
- Footer with `_N repos checked_`

Example output:
```
**🏥 Project Health — June 01, 2026**

**pi-mobile** — ✅ CI: success
  ✅ Mobile Build: success (2026-05-30)

**FastBot** — ❌ CI: failure
  ❌ npm_and_yarn in /., /packages/: failure (2026-05-29)

_29 repos checked_
```

## Silent Protocol

- `# Silent: no open PRs` → exit 0, no output → cron delivers nothing
- `# Silent: gh not authenticated` → exit 0, no output
- Real output → formatted Markdown → cron delivers to Telegram

## Known Repos (as of June 2026)

```python
REPOS = [
    "benclawbot/pi-mobile",
    "benclawbot/open-brain",
    "benclawbot/Video-Meeting-Minutes-Manager",
    "benclawbot/pm-command-center",
    "benclawbot/Pi-Agent-Optimus",
    "benclawbot/yoga-flow-builder",
    "benclawbot/Hermes-Backup",
    "benclawbot/agent-commit",
    "benclawbot/pi-mobile",
    "benclawbot/liquidity-pulse",
    "benclawbot/Claude-trading-bot",
    "benclawbot/dropsync-pwa",
    "benclawbot/uniapi-connector",
    "benclawbot/Specs-Generator",
    "benclawbot/MindDrop2-Opencode",
    "benclawbot/OmniCom",
    "benclawbot/TrailBlazer",
    "benclawbot/BrainstormFlow",
    "benclawbot/GanttMaker",
    "benclawbot/AI-Harness",
    "benclawbot/websend-landing",
    "benclawbot/WebSend",
    "benclawbot/android_app_factory",
    "benclawbot/FastBot",
    "benclawbot/brainstorm-trooper",
    "benclawbot/autonomos",
    "benclawbot/Daily-Rehab",
    "benclawbot/CV-Maestro",
    "benclawbot/To-do",
]
```

## Key Findings (June 2026)

- **FastBot** has failing CI: `npm_and_yarn` workflow failure on 2026-05-29
- **dropsync-pwa** has a cancelled deployment (2026-04-21) alongside successful ones
- All other repos: clean CI or no recent activity
- `gh` path discovery: `which gh` → `/home/thomas/bin/gh` (not in standard PATH)