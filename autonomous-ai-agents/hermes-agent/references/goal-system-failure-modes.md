# /goal Command — Failure Modes & Troubleshooting

Captured from session 2026-05-10. Diagnostics on a frozen CLI `/goal` session.

## What the /goal Loop Does

1. User sets standing goal: `/goal <text>`
2. After each assistant turn, a **judge** (auxiliary model call) asks: "is the goal satisfied?"
3. If `done: false` → injects `[Continuing toward your standing goal...]` as a user message, loop continues
4. If `done: true` → loop stops, goal marked "complete"
5. If judge fails to parse → consecutive_parse_failures counter increments; after 3 failures, loop pauses

**Goal state is persisted** in `state.db` keyed by `goal:<session_id>`. Resume with `/goal resume`.

## Failure Mode 1: Judge Returns Non-JSON

**Symptom:** Goal loops forever — judge keeps saying "continue" even when work is done. Session eventually hits max_turns.

**Root cause:** The configured judge model doesn't reliably return the required `{"done": <bool>, "reason": "<string>"}` JSON format.

**Diagnosis:**
```bash
# Check goal state in DB
python3 -c "
import sqlite3, json
db = sqlite3.connect('/home/thomas/.hermes/state.db')
cur = db.cursor()
cur.execute(\"SELECT key, value FROM state_meta WHERE key LIKE 'goal%'\")
for k, v in cur.fetchall():
    print(k, '->', v[:300])
"

# Check sessions.json for active goal sessions
cat ~/.hermes/sessions/sessions.json
```

**Fix:** Route goal_judge to a reliable model. As of 2026-05-10, working config:
```yaml
auxiliary:
  goal_judge:
    provider: minimax
    model: MiniMax-M2.5
```

Apply via `hermes config set auxiliary.goal_judge.provider minimax` etc., then restart gateway.

**Session that found this:** `session_20260510_091918_75518e` (88 messages, goal completed then looped).

## Failure Mode 2: "Windows Too Small" — TUI Freezes

**Symptom:** CLI appears frozen. No new output. Eventually prints "windows too small" or similar.

**Root cause:** Rich terminal output (Panels, Tables, long unbreakable strings) exceeds terminal column width. The TUI uses Rich for rendering — wide content either clips silently or blocks the render loop.

**Common triggers:**
- `/goal status` with a long goal text
- Skill content panels with un缩进的 content
- Diagnostic tables from rich-printed dicts
- Any single-line string longer than `console.width`

**The process may have already completed its work.** Check:
```bash
# Look for recent session files
ls -lt ~/.hermes/sessions/*.json | head -5

# Check if hermes process is still alive
ps aux | grep hermes | grep -v grep

# Read the session file — if messages exist, work completed
cat ~/.hermes/sessions/<session_id>.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
msgs = d.get('messages', [])
print(f'Messages: {len(msgs)}, last_updated: {d.get(\"last_updated\")}')
"
```

**Fix:** Kill the hung process, restart. Prevent by ensuring any Rich content is width-constrained:
```python
from rich.text import Text
from rich.panel import Panel
import textwrap

# Wrap long content before rendering
wrapped = textwrap.fill(long_string, width=console.width - 4)
panel = Panel(wrapped)
```

## Failure Mode 3: Session File Missing for Active Goal

**Symptom:** `state.db` has an active goal, but the session JSON file is gone.

**Root cause:** Sessions can be GC'd or moved while goal state persists. The goal tracker only reads from `state_meta` in the DB, not from session files.

**Fix:** Either:
- `/goal resume` in a new session to pick up the orphaned goal
- `/goal clear` to wipe the stuck goal state
- Manually clean DB: `DELETE FROM state_meta WHERE key LIKE 'goal%'`

## max_turns Interaction

`/goal` loops count against `agent.max_turns`. If max_turns is too low, the goal may exhaust budget before completing. With goal_judge misbehaving, you can hit the limit quickly.

Default: 90. Current lean config: 45.

If running long-running `/goal` tasks, consider setting `agent.max_turns` higher or ensuring goal_judge is working before starting.

## Useful Commands

```bash
# Check goal state
sqlite3 ~/.hermes/state.db "SELECT key, substr(value, 1, 300) FROM state_meta WHERE key LIKE 'goal%'"

# Find sessions with goal-related content
grep -l "Continuing toward your standing goal" ~/.hermes/sessions/*.json

# Check current goal_judge config
grep -A5 "goal_judge" ~/.hermes/config.yaml

# Kill frozen CLI
ps aux | grep "hermes$" | grep -v grep | awk '{print $2}' | xargs kill
```