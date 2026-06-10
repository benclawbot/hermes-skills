---
name: sandy
description: Deterministic MCP scenario replay — record workflows as JSON scenarios and replay them without LLM inference. Use for cron jobs, repeated workflows, and any deterministic multi-step task. Also supports native tools (bash, file ops, grep, web fetch) via claude__* tools.
triggers:
  - "run a scenario"
  - "replay workflow"
  - "deterministic replay"
  - "sandy scenario"
  - "cron job using sandy"
  - "scenario replay"
---

# Sandy Skill

Sandy accelerates AI agents by storing and replaying deterministic MCP tool sequences as **scenarios** — JSON files that execute without LLM inference.

## Core Concepts

- **Scenario**: JSON file describing a sequence of tool calls with variable substitution
- **Tool types**: `mcp__server__tool` (MCP servers), `claude__*` (native tools), `sandy__*` (internal)
- **Variables**: `{{VAR}}` substitutions from `variables` dict
- **Step outputs**: `{{step_id.field}}` references to previous step results

## Locations

```
~/.hermes/skill-assets/sandy/scripts/     # Sandy runtime
~/.hermes/sandy/scenarios/                # Scenario files
~/.hermes/sandy/config.json               # MCP server config (auto-detected)
```

## Usage

### Run a scenario (any step)

```bash
python3 ~/.hermes/skill-assets/sandy/scripts/play.py \
  /path/to/scenario.json \
  --var KEY=VALUE \
  --debug
```

### Run a scenario via skill function

```python
sandy__play(scenario="scenario-name", variables={})
```

### Create a new scenario

```bash
cat > ~/.hermes/sandy/scenarios/my-task.json << 'EOF'
{
  "version": "2.1",
  "metadata": {"name": "my-task"},
  "variables": {"VAR": ""},
  "steps": [
    {
      "step": 1,
      "tool": "claude__bash",
      "id": "step1",
      "params": {"command": "echo {{VAR}}"}
    }
  ]
}
EOF
```

### Scenario format

```json
{
  "version": "2.1",
  "metadata": {"name": "Task Name", "description": "What this does"},
  "variables": {
    "KEY": "default_value"
  },
  "steps": [
    {
      "step": 1,
      "tool": "claude__bash",
      "id": "step1",
      "params": {"command": "echo hello"},
      "description": "Optional description",
      "output": {"result": "$"},
      "on_error": "skip|stop|retry",
      "retry": {"count": 3, "delay": 500, "condition": "timeout"}
    }
  ]
}
```

### Tool types

| Prefix | Example | Purpose |
|--------|---------|---------|
| `claude__` | `claude__bash`, `claude__read`, `claude__write`, `claude__edit`, `claude__glob`, `claude__grep`, `claude__web_fetch` | Native tools (no server needed) |
| `sandy__` | `sandy__wait`, `sandy__log`, `sandy__append_file` | Internal Sandy operations |
| `mcp__` | `mcp__server__tool_name` | MCP server tool calls |

### Sandy internal tools

- `sandy__wait`: `{"seconds": 5}` — pause execution
- `sandy__log`: `{"message": "status update"}` — debug output
- `sandy__append_file`: `{"path": "/tmp/out.jsonl", "format": "jsonl", "data": {...}}`

### append_file format options

- `jsonl`: one JSON object per line
- `json`: JSON array (appends to existing array)
- `csv`: CSV rows with header auto-creation

### Output extraction (JSONPath)

```json
{
  "step": 1,
  "tool": "claude__bash",
  "id": "git_status",
  "params": {"command": "git status --porcelain"},
  "output": {"changed": "$.stdout"}
}
```

Then reference `{{git_status.changed}}` in later steps.

## Common Patterns

### Shell variable in command

```json
{
  "step": 1,
  "tool": "claude__bash",
  "id": "step1",
  "params": {"command": "ls -la /home/thomas/Desktop/{{PROJECT_DIR}}"}
}
```

### Conditional step execution

```json
{
  "step": 2,
  "tool": "claude__bash",
  "params": {"command": "echo done"},
  "condition": "{{step1.exit_code}} == 0"
}
```

### Error handling with retry

```json
{
  "step": 1,
  "tool": "claude__bash",
  "params": {"command": "curl -s https://api.example.com/data"},
  "on_error": "retry",
  "retry": {"count": 3, "delay": 1000, "condition": "connection"}
}
```

## Setup (Required Before First Use)

> **One-time setup is automated.** The system already has Sandy installed at `~/.hermes/skill-assets/sandy/` with all 8 scenarios deployed. You only need to run the setup commands if setting up a new machine.

```bash
# Create config directory and minimal config
mkdir -p ~/.sandy ~/.hermes/sandy/scenarios
echo '{"servers": {}}' > ~/.sandy/config.json
ln -sf ~/.sandy/config.json ~/.hermes/sandy/config.json
```

> **Critical:** Sandy will NOT run without a config file. See `references/scenario-library.md` for the full list of deployed scenarios and wrapper scripts.

> **Critical:** Sandy will NOT run without a config file. It searches these paths in order and fails if none exist:
> `$SANDY_CONFIG` → `.sandy/config.json` (project) → Claude Desktop config → `~/.cursor/mcp.json` → `~/.sandy/config.json`
> If `~/.sandy/config.json` is missing, it raises `ConfigNotFoundError`.

## Pitfalls

### `script` field bypasses agent and skill entirely
When a cron job has `script: X.sh`, Hermes runs that script with `no_agent: true` — the `prompt` and `skill` fields are **completely ignored**. This is by design. The old `daily-ai-digest` cron job had `script: daily-ai-digest.sh` which called `play.py`; `play.py` exited 0 silently before any LLM call, producing 0-byte output files for days. The fix: omit `script` to use the agent+skill path, or if using `script`, ensure it outputs the actual content you want delivered.

### Sandy `play.py` stdout is NOT the script's stdout
`play.py` prints its own progress banner to stdout (timing, step names, PASSED/FAILED). This is what the cron system captures as the `.md` output file. **The individual step stdout is NOT captured** by default — it goes to the terminal. If you need a script's output to become the cron delivery content:
- Option A (simplest): make your script output the desired content as its own stdout directly (no Sandy needed for single-script jobs)
- Option B: use `sandy__append_file` to write content to a file, then have the wrapper script `cat` that file after Sandy exits
- Option C: use `output: {"field": "$.stdout"}` to capture a step's stdout, but note the cron system only captures the outer `play.py` output, not individual step outputs

### execute_code sandbox is unusable for Sandy
The Hermes `execute_code` sandbox lacks external packages (`mcp`, `httpx`, `jsonpath-ng`, `markdownify`, `nbformat`). **All Sandy operations must use `terminal`** — write files, run imports, and execute scenarios via `terminal` heredocs or `python3 << 'PYEOF'` scripts. `execute_code` only works for pure-stdlib Python.

### Wrapper scripts MUST use hermes-agent venv Python explicitly
The hermes-agent project uses a venv at `~/Desktop/hermes-agent/.venv/bin/python3` with packages installed via `uv pip install --python ~/Desktop/hermes-agent/.venv/bin/python3 <package>`. The system `python3` resolves to a different Python (often the uv-managed 3.11 or system 3.13) and lacks these packages — causing `ModuleNotFoundError` failures at import time before Sandy even starts.

**All `*_sandy.sh` wrapper scripts must use the explicit venv Python:**
```bash
PYTHON="/home/thomas/Desktop/hermes-agent/.venv/bin/python3"
$PYTHON /home/thomas/.hermes/skill-assets/sandy/scripts/play.py ...
```
Never `python3`, `$(which python3)`, `/usr/bin/python3`, or the bare `play.py` shebang — they resolve to the wrong interpreter.

### Wrapper scripts must be SILENT on success
`play.py` always prints a verbose banner to stdout on success (timing, step names, `Result: PASSED`). This banner IS the cron job's output — if the wrapper echoes it, the cron system delivers it as a notification even on healthy runs.

**Correct pattern (silent on success):**
```bash
PYTHON="/home/thomas/Desktop/hermes-agent/.venv/bin/python3"
output=$($PYTHON /home/thomas/.hermes/skill-assets/sandy/scripts/play.py ... 2>&1)
exit_code=$?
[ $exit_code -eq 0 ] && exit 0
# Failure path — echo to stderr so cron delivers the notification
echo "$output" >&2
exit $exit_code
```

**Wrong pattern (sends spurious notifications):**
```bash
# ❌ This echoes the Sandy banner on success → cron delivers it
[ -n "$output" ] && echo "$output"
exit $exit_code
```

**For watchdog jobs**: success = silent (no output = no notification). Failure = echo to stderr (stderr = cron delivery = notification sent). The 5-whys auto-fix loop runs before propagation, so transient dep failures heal automatically.

### Import chain: `import mcp` must NOT be at top level
`clients/base.py` imports `mcp` at the top level. When `player.py` imports from `scenario.py` → `config.py` → `clients`, the top-level `import mcp` fails if `mcp` isn't in the Python path. Always import `mcp` inside functions that use it, or inside the `try/except` block that handles optional dependencies.

### Config file path symlink required
`play.py` resolves `~/.sandy/config.json` (the standard Sandy path), but Hermes stores its config at `~/.hermes/sandy/config.json`. Create a symlink so both paths resolve:
```bash
ln -sf ~/.sandy/config.json ~/.hermes/sandy/config.json
```

### When to use Sandy vs direct script vs agent-based cron
- **Sandy**: multi-step deterministic workflows where you need replay, conditional branching, or MCP tool orchestration. Overkill for single Python scripts.
- **Direct script**: single-step Python scripts where stdout = delivery content. Just set `script: my_script.sh` with `no_agent: true`. The script's stdout becomes the cron output file directly.
- **Agent-based** (`skill: X`, no `script`): LLM-driven research or synthesis tasks. Slower but handles ambiguity and produces natural language output.

## Decision Tree for Cron Jobs

```
Is the task a single deterministic script?
  YES → Use `script: my_script.sh` with `no_agent: true`. Script stdout = cron output.
  NO  → Is it a multi-step deterministic workflow?
    YES → Use Sandy scenario + `script: my_scenario_sandy.sh`
    NO  → Use agent-based: `skill: my-skill` (no `script`)
```

## Verification

```bash
cd ~/.hermes/skill-assets/sandy/scripts
python3 -c "
import sys; sys.path.insert(0, '.')
from scenario import load_scenario; from player import play_scenario
from config import Config
import asyncio, json
config = Config(servers={}, source='test')
scenario = load_scenario('/home/thomas/.hermes/sandy/scenarios/example.json')
result = asyncio.run(play_scenario(scenario, config))
print('PASSED' if result.success else 'FAILED')
"
```

## MCP Server Configuration

Sandy auto-detects MCP config from:
1. `$SANDY_CONFIG` env variable
2. `.sandy/config.json` (project local)
3. Claude Desktop config (`~/.config/Claude/claude_desktop_config.json`)
4. Cursor MCP config (`~/.cursor/mcp.json`)
5. `~/.sandy/config.json` (global)

Format:
```json
{
  "servers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@some/mcp-server"],
      "env": {"API_KEY": "{{MY_API_KEY}}"}
    }
  }
}
```