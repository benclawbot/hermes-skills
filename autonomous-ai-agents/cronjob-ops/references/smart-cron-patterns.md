---
name: smart-cron
description: "Create self-healing cron jobs that auto-fix common failures silently and only report when human input is needed. Auto-fix patterns: git uncommitted, service down, disk full, memory high. Silent on success."
version: 1.0.0
---

# Smart Cron Creation

Create cron jobs that heal themselves and stay quiet unless human intervention is needed.

## Pattern

Every cron job created through this skill follows the **Silent → Auto-fix → Escalate** triangle:

```
[Run] → all clear? → SILENT (no message)
      → fixable?  → FIX AUTOMATICALLY + brief "Fixed: X"
      → human?    → REPORT: what happened + what was done + what needs you
```

## Rules

1. **Silent on health** — stdout = "NO_ANOMALIES" (or empty) → no Telegram delivery
2. **Auto-fix common patterns** — include fix logic in the script, don't just detect
3. **Escalate with context** — report what was fixed AND what still needs attention
4. **Human gates** — anything needing a decision (merge conflicts, API key rotation, breaking changes) → report, don't guess

## Auto-fix Reference

| Problem | Fix | When to auto-fix |
|---------|-----|-----------------|
| Uncommitted files | `git add . && git commit && git push` | Safe, non-breaking changes only |
| Stashed changes | `git stash` then `git stash drop` | Clean working tree needed |
| Service down | `systemctl --user restart <service>` | Low-risk services |
| Disk near full | `trash-empty` or `docker system prune -y` | Known cleanup commands |
| Memory high | `sync && echo 3 > /proc/sys/vm/drop_caches` | Read-only cleanup |
| Cron job failed | Retry once with exponential backoff | Transient failures |
| Stale lock files | Remove stale lock | Known lock file paths |
| Push without pre-check | Run `git status && git diff --cached --name-only` before push | **Always — credential leaks are irreversible** |

## Creating a Smart Cron Job

When creating a cron job, write the script so it:

1. **Checks** — detect issues
2. **Fixes** — attempt auto-fix for known patterns
3. **Reports** — stdout is the delivery; "NO_ANOMALIES" means silent

### Script Template

```python
#!/usr/bin/env python3
"""
Smart watchdog: detect → auto-fix → report.
stdout = delivery. "NO_ANOMALIES" = silent.
"""
import subprocess, sys, time

FIXES_APPLIED = []

def run(cmd, **kw):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def check_and_fix_git_uncommitted(repo_path):
    """Auto-fix: commit and push uncommitted changes to fork."""
    rc, diff, _ = run("git diff --name-only", cwd=repo_path)
    if rc == 0 and diff:
        files = [f for f in diff.strip().splitlines() if f.strip()]
        if files:
            run("git add .", cwd=repo_path)
            rc2, msg, _ = run(
                f'git commit -m "chore: auto-commit from watchdog"',
                cwd=repo_path
            )
            if rc2 == 0:
                # Push to fork (hardcoded for benclawbot/hermes-agent)
                rc3, out3, err3 = run(
                    "git push https://benclawbot:ghp_TOKEN@github.com/benclawbot/hermes-agent.git HEAD:main",
                    cwd=repo_path
                )
                if rc3 == 0:
                    FIXES_APPLIED.append(f"Committed {len(files)} file(s)")
                else:
                    return f"Commit ok but push failed: {err3[:100]}"
            else:
                return f"Commit failed: {msg[:100]}"
    return None

def main():
    # === CHECKS + FIXES ===
    # Example for hermes-agent:
    err = check_and_fix_git_uncommitted("/home/thomas/Desktop/hermes-agent")
    
    # === ESCALATE? ===
    if FIXES_APPLIED:
        msg = "✅ *Auto-fixed*\n" + "\n".join(f"  • {f}" for f in FIXES_APPLIED)
        if err:
            msg += f"\n⚠️ *Needs attention*\n  • {err}"
        msg += f"\n\n_Checked {time.strftime('%H:%M:%S')}_"
        print(msg)
        return

    # Nothing happened — silent
    print("NO_ANOMALIES", file=sys.stderr)

if __name__ == "__main__":
    main()
```

## Cron Creation Checklist

When creating a new cron via `cronjob create`:

- [ ] Set `no_agent=true` for pure watchdogs (checks only, no LLM)
- [ ] Set `no_agent=false` for jobs needing reasoning/decision-making
- [ ] Embed `NO_ANOMALIES` silent pattern in every script
- [ ] Include auto-fix for every fixable failure mode
- [ ] Put `origin` as deliver target for jobs that may need human input
- [ ] Put `local` for pure data-collection that chains into other jobs
- [ ] Include `--name` with `-watchdog` suffix for health-check jobs

## Reference Implementations

All `no_agent` watchdogs should use **Sandy** (deterministic scenario replay) instead of direct shell/python scripts. See `sandy` skill for setup and `references/scenario-library.md` for deployed scenario list.

- `references/obsidian-vault-backup.md` — git-based vault backup cron: script pattern, cron config, creation workflow, and a detailed incident log
- `references/vault-weekly-digest.md` — weekly vault consolidation script: structure, output sections, git commit/push pattern, NO_ANOMALIES skip logic

## Updating Existing Crons

If an existing cron reports failures and you fix it by editing the script:
1. Edit the script at `~/.hermes/scripts/<script_name>.sh` or `~/.hermes/scripts/<script_name>.py`
2. Add auto-fix logic for the failure type
3. Cron picks up changes on next run — no restart needed

For `no_agent` watchdogs: prefer updating the Sandy scenario JSON (`~/.hermes/sandy/scenarios/<name>.json`) over editing the raw script — scenarios are version-controlled and the wrapper shell is already in place.
