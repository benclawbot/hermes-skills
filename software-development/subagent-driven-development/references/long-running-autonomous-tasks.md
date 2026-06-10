# Long-Running Autonomous Tasks

Pattern for delegating a task that takes hours to complete, with hourly status reports to Telegram and automatic continuation after subagent timeouts.

## When to Use

- Large implementation tasks (e.g., "implement X fully, all tests passing, no further input from me")
- Migrations or rewrites requiring 1000+ lines of code across multiple components
- Multi-phase builds where subsequent phases depend on prior phases completing
- Any task that exceeds the 1200s (20min) subagent timeout by a significant margin

## The Pattern

```
┌─────────────────────────────────────────────────────┐
│  1. Write GOAL.md + USER_STORIES.md                 │
│     (test-first: stories define done-ness)           │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  2. Set up watchdog cron                            │
│     • every 1h, no_agent=true                       │
│     • finds new files, reports line counts           │
│     • deliver to Telegram                           │
│     • no_agent=true so cron stays quiet when        │
│       nothing has changed                           │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  3. Dispatch subagent with:                          │
│     • Full current state (already-done files)       │
│     • GOAL.md + USER_STORIES.md in context           │
│     • Instruction: "continue from where I left off" │
│     • 15-20min timeout (half of hard 20min limit)   │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  4. On timeout:                                      │
│     • subagent exits, code already written is saved │
│     • Watchdog cron will fire in ≤60min              │
│     • Human reviews status report                   │
│     • Human relaunches subagent with resume context │
│       (what exists, what phase it was on)           │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  5. Repeat until all stories pass                   │
└─────────────────────────────────────────────────────┘
```

## Watchdog Cron: Minimal Script

```python
#!/usr/bin/env python3
"""Watchdog: report new/changed files since last run. Silent on nothing changed."""
import os
from datetime import datetime

CHECK_DIR = os.path.expanduser("~/clicky-windows")
STATE_FILE = "/tmp/wd_clicky_timestamp"

last = open(STATE_FILE).read().strip() if os.path.exists(STATE_FILE) else "1970-01-01"
os.system(f"find {CHECK_DIR} -type f -newer {last} -not -path '*/.git/*' | sort")
open(STATE_FILE, "w").write(datetime.now().isoformat())
```

**Delivery:** `no_agent=true` script that stays silent on no-change. Cron fires every 1h, delivers to Telegram. Human gets hourly status without any action needed.

## Subagent Resume Context Template

When relaunching after timeout, give the next subagent exact state:

```
CURRENT STATE:
- Phase N: [list files, line counts]
- Phase N+1: [started but incomplete]

REMAINING WORK:
- [phases/files still to do]

RULES:
- Do NOT rewrite complete, correct files
- Do NOT regenerate GOAL.md or USER_STORIES.md
- Python: `python3 -m py_compile *.py` must pass
- WPF: verify correctness by review (can't build on Linux)
```

## Story Validation Check

At end of each subagent run:
1. `wc -l **/*.cs **/*.xaml **/*.py` → compare to story file counts
2. List DONE stories
3. List IN PROGRESS stories
4. Report remaining work

This lets the human give precise resume context to the next subagent.

## Lessons from Clicky-Windows Session

| Lesson | Value |
|--------|-------|
| child_timeout_seconds: 600 (default) | causes mid-phase interruptions — always set to 1200 for multi-phase work |
| python -m py_compile | verifies Python without needing runtime |
| WPF can't build on Linux | verify C# by review, not compilation |
| code persists on disk after timeout | no work is lost |
| no auto-restart on timeout | human must relaunch manually |
| 20min subagent → ~3,500 lines in one run | reasonable throughput |
| check existing ports before rewriting | clicky-win (3,810 lines) was production-ready; WPF rewrite (3,555 lines) had critical gaps |

## Key Files Created per Project

| File | Purpose |
|------|---------|
| GOAL.md | 8-phase implementation plan |
| USER_STORIES.md | 38 test stories, done-ness definition |
| SPEC.md | authoritative spec, decisions locked at top |
| .gitignore | excludes bin/, obj/, __pycache__, *.log |

These travel with the codebase. Subagent reads them on every run.