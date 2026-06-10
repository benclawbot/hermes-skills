# Debugging Hermes TUI Slash Commands

## Overview

Hermes slash commands span three layers — Python command registry, tui_gateway JSON-RPC bridge, and the Ink/TypeScript frontend. When a command misbehaves (missing from autocomplete, works in CLI but not TUI, config persists but UI doesn't update), the bug is almost always one layer being out of sync with another.

## Architecture

```
Python backend (hermes_cli/commands.py)     <- canonical COMMAND_REGISTRY
       │
       ▼
TUI gateway (tui_gateway/server.py)         <- slash.exec / command.dispatch
       │
       ▼
TUI frontend (ui-tui/src/app/slash/)        <- local handlers + fallthrough
```

Command definitions must be registered consistently across Python and TypeScript. The Python `COMMAND_REGISTRY` is the source of truth for: CLI dispatch, gateway help, Telegram BotCommand menu, Slack subcommand map, and autocomplete data shipped to Ink.

## Investigation Steps

1. **Check if the command exists in the TUI frontend:**
   ```bash
   search_files --pattern "/commandname" --file_glob "*.ts" --path ui-tui/
   ```

2. **Examine the TUI command definition:**
   ```bash
   read_file ui-tui/src/app/slash/commands/core.ts
   ```

3. **Check if the command exists in the Python backend:**
   ```bash
   search_files --pattern "commandname" --path hermes_cli/commands.py --context 3
   ```

4. **Examine the gateway implementation:**
   ```bash
   search_files --pattern "complete.slash|slash.exec" --path tui_gateway/
   ```

## Fix: Missing Command Autocomplete

Add a `CommandDef` entry to `COMMAND_REGISTRY` in `hermes_cli/commands.py`:
```python
CommandDef("commandname", "Description", "Session",
           cli_only=True, aliases=("alias",),
           args_hint="[arg1|arg2|arg3]",
           subcommands=("arg1", "arg2", "arg3")),
```

`cli_only=True` — only in the interactive CLI/TUI.
`gateway_only=True` — only in messaging platforms.
`gateway_config_gate="display.foo"` — config-gated availability in the gateway.

For gateway-available commands, add a handler in `gateway/run.py`:
```python
if canonical == "commandname":
    return await self._handle_commandname(event)
```

## Common Issues

1. **Command shows in TUI but not in autocomplete.** Missing from `COMMAND_REGISTRY` in `hermes_cli/commands.py`. Autocomplete data ships from Python.

2. **Command shows in autocomplete but doesn't work.** Check `tui_gateway/server.py` and the frontend handler in `ui-tui/src/app/createSlashHandler.ts`. Local TUI handlers take precedence over gateway dispatch.

3. **Command persists config but doesn't apply live.** For TUI-local commands, updating `config.set` is not enough. Also patch the relevant nanostore state immediately (`patchUiState(...)`).

4. **Gateway dispatch silently ignores the command.** Check `GATEWAY_KNOWN_COMMANDS` includes the canonical name.

## Debugging Tactics

- **Python side hangs:** use `python-debugpy` to break inside `_SlashWorker.exec` or the command handler. `remote-pdb set_trace()` at handler entry.
- **Ink side not reacting:** use `node-inspect-debugger` to break in `app.tsx`'s slash dispatch. `sb('dist/app.js', <line>)` after `npm run build`.

## "Windows Too Small" TUI Freeze

The TUI uses Rich for terminal rendering. Wide content exceeds the terminal column buffer → Rich silently clips or blocks.

Diagnosis:
```bash
stty -a < /dev/pts/N   # or: echo $COLUMNS
ps aux | grep hermes
```

Fix: resize terminal wider, or `kill <pid>` and restart. Prevent with `textwrap.wrap()`, `Constraint.FILL`, or `shrink` on wide content.

## Goal Loop Freeze

`/goal` session appears stuck — Ralph loop may be stuck in judge retries or TUI froze on wide output panel. Check `state_meta` via sqlite3 before killing:
```bash
sqlite3 ~/.hermes/sessions/<session>.db "SELECT * FROM state_meta LIMIT 5;"
```

## Pitfalls

- Don't forget to set the appropriate category in `CommandDef` ("Session", "Configuration", "Tools & Skills", "Info", "Exit")
- For commands with subcommands, ensure the `subcommands` tuple in `CommandDef` matches what's in the TUI code
- After adding live UI state, thread the new state through ALL render paths — live streaming and transcript/pending `MessageLine` rows
- Rebuild the TUI (`npm --prefix ui-tui run build`) before testing — tsx watch mode may lag

## Verification

1. Rebuild the TUI:
   ```bash
   cd /home/bb/hermes-agent && npm --prefix ui-tui run build
   ```
2. Run the TUI and test the command:
   ```bash
   hermes --tui
   ```
3. Type `/` and verify autocomplete.
4. Execute and confirm behavior, config persistence, and live UI state.
