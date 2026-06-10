# gh Path Requirement

**Always use `/home/thomas/bin/gh`** — not `/usr/bin/gh` and not just `gh`.

## The Problem

The standard assumption for `gh` path is `/usr/bin/gh` (the system's package manager location). On Thomas's system, that path doesn't exist. The actual binary is at `/home/thomas/bin/gh`.

When a Python script uses `GH_CLI = "/usr/bin/gh"`:
- `subprocess.run([GH_CLI, "auth", "status"], ...)` returns exit code 1
- The error is "No such file or directory" — not an auth failure
- But the calling code reads this as "gh not authenticated" → silently skips all GitHub operations

## How to Diagnose

When a `gh` command appears to return "not authenticated" but `gh auth status` works fine in the terminal:

```bash
ls -la /usr/bin/gh 2>/dev/null || echo "/usr/bin/gh does not exist"
which gh
/home/thomas/bin/gh --version
```

## The Fix

In every Python script that calls `gh`:

```python
GH_CLI = "/home/thomas/bin/gh"  # hardcoded, not discoverable
```

This applies to:
- `watch_repos.py`
- `github-pr-digest.py`
- `project-health-digest.py`
- `single-repo-digest.py`
- Any other script in `~/.hermes/scripts/` that invokes `gh`

## Why Not Rely on PATH

The scripts run via cron with a stripped environment. Even though `which gh` works in an interactive shell (shell RC files are sourced), cron jobs run with minimal env. Hardcoding the path is the only reliable approach.