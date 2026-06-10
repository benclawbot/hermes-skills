# GenericAgent Setup Reference

## Installation (May 2026 session)

Installed from: `https://github.com/lsdefine/GenericAgent`
Location: `/home/thomas/Desktop/GenericAgent/`

## `mykey.py` configuration

Created at `/home/thomas/Desktop/GenericAgent/mykey.py` with MiniMax M2.7:

```python
import os

native_claude_config_minimax = {
    'name': 'minimax-m27',
    'apikey': os.environ.get('MINIMAX_API_KEY', ''),
    'apibase': 'https://api.minimaxi.com/anthropic',
    'model': 'MiniMax-M2.7',
    'max_retries': 3,
}

mixin_config = {
    'llm_nos': ['minimax-m27'],
    'max_retries': 10,
    'base_delay': 0.5,
}
```

Key points:
- Uses `NativeClaudeSession` config (`native_claude_config_minimax`) — aligns with model training format
- Field names are `apikey` and `apibase` (not `api_key`/`api_base`) per GenericAgent's naming convention
- Reads `MINIMAX_API_KEY` from environment (not hardcoded)
- Same API base as Hermes Agent MiniMax config
- TUI entry point: `frontends/tuiapp.py`

## Shell invocation

The `generic` command is provided by `~/bin/generic` (executable, in `$PATH`):

```bash
#!/bin/bash
# Source .bashrc to load MINIMAX_API_KEY from ~/.hermes/.env
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
cd /home/thomas/Desktop/GenericAgent && python frontends/tuiapp.py
```

Why source `.bashrc`? The `MINIMAX_API_KEY` lives in `~/.hermes/.env` and is loaded by `.bashrc`'s existing logic. Without this, new login shells never see the key and GenericAgent reports "invalid api key".

**Verification:**
```bash
bash -l -c 'source ~/.bashrc; echo "Key length: ${#MINIMAX_API_KEY}"'
# Must show 125 (non-empty key loaded)
```

## Troubleshooting: "invalid api key" error

1. Check the key exists in `.hermes/.env`:
   ```bash
   grep MINIMAX_API_KEY ~/.hermes/.env
   ```
2. Confirm `.bashrc` loads it:
   ```bash
   source ~/.bashrc && echo $MINIMAX_API_KEY
   ```
3. Verify the `generic` script sources `.bashrc` (see above)
4. If the TTY hangs: Textual TUI needs a real TTY — use `tmux` or a proper terminal emulator

## GenericAgent vs Hermes Agent

| | GenericAgent | Hermes Agent |
|---|---|---|
| Type | Terminal TUI | Background daemon |
| Model | MiniMax M2.7 | MiniMax M2.5 |
| Best for | Interactive coding | Automation, cron, PM tasks |
| Access | `generic` command | `hermes` command |

## TUI Controls

- `↑↓` — navigate history
- `Ctrl+N` — new session
- `Ctrl+S` — stop running task
- `Ctrl+Q` — quit
- `/help` — agent commands inside the chat input
- `^p` — command palette
- `^← / ^→` — previous/next session