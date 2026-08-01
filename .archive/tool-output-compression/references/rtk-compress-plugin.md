# RTK-Compress Plugin — Full Reference

Built and tested 2026-06-05. Lives at `~/.hermes/plugins/rtk-compress/`. Compresses `terminal` tool output via `rtk pipe -f <filter>` before it enters the LLM context.

## Why this approach

The `terminal` tool in Hermes calls `subprocess.run`, which bypasses shell aliases entirely. The legacy `~/.bash_aliases` → `~/.hermes/.hermes_env` path works for human shells but does nothing for the agent loop. The right integration point is the `transform_terminal_output` hook in `tools/terminal_tool.py` (line ~2318), which fires *after* command execution and *before* the output reaches the model.

`post_tool_call` is **observational only** — return values are ignored. Use `transform_terminal_output` (or `transform_tool_result`) for output replacement.

## File layout

```
~/.hermes/plugins/rtk-compress/
├── plugin.yaml        # name, version, hooks
└── __init__.py        # register(ctx) entry point
```

## plugin.yaml

```yaml
name: rtk-compress
version: 1.0.0
description: "Compress noisy terminal tool output via RTK pipe filters..."
author: thomas
kind: hook
hooks:
  - transform_terminal_output
```

## __init__.py (the working version)

```python
"""RTK Compress — terminal output compression hook for Hermes."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# Map: command-prefix pattern → RTK pipe filter name
_FILTER_MAP: list[tuple[re.Pattern[str], str]] = [
    # Grep family
    (re.compile(r"^(grep|egrep|fgrep)\b"), "grep"),
    (re.compile(r"^rg\b"), "rg"),
    # Find family
    (re.compile(r"^find\b"), "find"),
    (re.compile(r"^fd\b"), "fd"),
    # Git
    (re.compile(r"^git\s+log\b"), "git-log"),
    (re.compile(r"^git\s+diff\b"), "git-diff"),
    (re.compile(r"^git\s+status\b"), "git-status"),
    # Linters / formatters
    (re.compile(r"^ruff\s+check\b"), "ruff-check"),
    (re.compile(r"^ruff\s+format\b"), "ruff-format"),
    (re.compile(r"^mypy\b"), "mypy"),
    (re.compile(r"^prettier\b"), "prettier"),
    # Test runners
    (re.compile(r"^(pytest|python\s+-m\s+pytest)\b"), "pytest"),
    (re.compile(r"^cargo\s+test\b"), "cargo-test"),
    (re.compile(r"^go\s+test\b"), "go-test"),
    (re.compile(r"^go\s+build\b"), "go-build"),
    (re.compile(r"^tsc\b"), "tsc"),
    (re.compile(r"^vitest\b"), "vitest"),
]

_MIN_OUTPUT_BYTES = 500
_RTK_TIMEOUT_S = 10


def _resolve_filter(command: str) -> Optional[str]:
    """Return the RTK pipe filter for `command`, or None if no match."""
    cmd = command.strip()
    # Strip leading env-var assignments (KEY=VAL cmd args → cmd args)
    while re.match(r"^[A-Z_][A-Z0-9_]*=", cmd):
        cmd = re.sub(r"^[A-Z_][A-Z0-9_]*=\S*\s*", "", cmd, count=1)
    for pattern, filter_name in _FILTER_MAP:
        if pattern.search(cmd):
            return filter_name
    return None


def _rtk_available() -> bool:
    return shutil.which("rtk") is not None


def _compress(output: str, filter_name: str) -> Optional[str]:
    """Pipe `output` through `rtk pipe -f <filter_name>`.

    Returns compressed output, or None on any failure (caller keeps
    the original). Failures logged at debug — never raised.
    """
    try:
        proc = subprocess.run(
            ["rtk", "pipe", "-f", filter_name],
            input=output,
            capture_output=True,
            text=True,
            timeout=_RTK_TIMEOUT_S,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug("rtk pipe failed for filter=%s: %s", filter_name, e)
        return None

    if proc.returncode != 0:
        logger.debug(
            "rtk pipe non-zero exit (%d) for filter=%s: %s",
            proc.returncode, filter_name, proc.stderr[:200],
        )
        return None

    # If RTK produced nothing (filtered everything out), keep original —
    # "no output" is a signal the agent might need.
    if not proc.stdout.strip():
        return None

    return proc.stdout


def on_transform_terminal_output(
    *,
    command: str,
    output: str,
    returncode: int,
    **kwargs,
) -> Optional[str]:
    """transform_terminal_output hook handler.

    Returns a compressed string to replace `output`, or None to leave
    unchanged. Per the hook contract, the first non-None string wins.
    """
    if returncode != 0:
        return None  # preserve error tracebacks
    if len(output.encode("utf-8")) < _MIN_OUTPUT_BYTES:
        return None  # too small to benefit
    if not _rtk_available():
        return None
    filter_name = _resolve_filter(command)
    if filter_name is None:
        return None
    compressed = _compress(output, filter_name)
    if compressed is None:
        return None
    if len(compressed) >= len(output):
        return None  # compression made it bigger
    return compressed


def register(ctx) -> None:
    """Plugin entry point — called by the plugin loader at startup."""
    ctx.register_hook("transform_terminal_output", on_transform_terminal_output)
```

## Safety nets (all required)

1. **`returncode != 0` → pass through** — never compress failed commands
2. **Output < 500 bytes → pass through** — RTK overhead > savings
3. **Unmapped commands → pass through** — `cat`, `ls`, `python`, `rm`, `ssh` etc. are NOT in `_FILTER_MAP`
4. **RTK errors / timeouts → pass through** — `subprocess.TimeoutExpired`, `FileNotFoundError`, non-zero exit
5. **Empty RTK output → pass through** — preserve "no output" as a signal
6. **Compressed larger than original → pass through** — rare but possible
7. **10-second timeout cap** — never block the agent loop

## RTK CLI facts you'll need

### `rtk pipe -f <filter>` — stdin mode

Available filters (as of RTK 0.39.0):
`cargo-test`, `pytest`, `go-test`, `go-build`, `tsc`, `vitest`, `grep`, `rg`, `find`, `fd`, `git-log`, `git-diff`, `git-status`, `mypy`, `ruff-check`, `ruff-format`, `prettier`

Not in this list: `log`, `ls`, `read`, `cat`. Use the grep/git filters for these, or don't compress.

### `rtk rewrite <cmd>` — detect rewriter

Exit codes:
- `0` — command is rewritable (e.g. `ls -la /tmp` → `rtk ls -la /tmp`)
- `3` — not rewritable (e.g. `python script.py` → empty)
- `1` — error

For this plugin, `rewrite` is not used (we don't re-execute). Listed for reference.

## Verification

```bash
# Plugin enabled
hermes plugins list | grep rtk-compress    # should show "enabled"

# Plugin loaded (gateway must be restarted)
systemctl --user restart hermes-gateway

# Safety net smoke test
python3 -c "
import sys; sys.path.insert(0, '$HOME/.hermes/plugins/rtk-compress')
from __init__ import _resolve_filter
assert _resolve_filter('ls -la') is None          # not in map
assert _resolve_filter('git log --oneline') == 'git-log'
assert _resolve_filter('python -m pytest') == 'pytest'
assert _resolve_filter('FOO=bar grep -rn x') == 'grep'  # env stripped
print('all checks pass')
"

# Real compression test
seq 1 1000 | rtk pipe -f grep   # arbitrary filter on stdin works
```

## Measured performance

From the 2026-06-05 session (RTK 0.39.0, 279 commands tracked):
- **89.8% global savings** (2.6M tokens saved)
- **97.2% on git log** (typical multi-commit output)
- **93.6% on dense git history**
- 60-80% on `rtk grep`, `rtk find`, `rtk ls`

## Gotchas learned the hard way

1. **The `hermes-agent` SKILL.md is wrong** about the hook contract. It lists `post_tool_call` and `transform_tool_result` as the compression hooks but misses `transform_terminal_output` — which is the right one for the `terminal` tool. Patched.
2. **The `hermes-agent` SKILL.md is wrong** about bash aliases covering the agent loop. They don't. `subprocess.run` bypasses aliases. The skill is now corrected.
3. **Hub-installed `taste` skill blocks skill updates** — uses the protection mechanism. Don't try to patch it.
4. **Plugin must be enabled explicitly** — `kind: hook` plugins are not auto-loaded. Run `hermes plugins enable rtk-compress` after creating the files.
5. **Gateway restart required** for plugin changes to take effect — same as toolset changes.
6. **CSL security blocks updates from community sources** — `hermes skills update` for hub-installed skills can be blocked by the dangerous verdict. Not a bug.
