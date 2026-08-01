# RTK Token Compression — Integration Reference

**Learned: 2025-05-08. Updated: 2026-06-05 — added `transform_terminal_output` plugin path; corrected bash-alias myth.**

*Absorbed from the former `tool-output-compression` skill (archived 2026-07-25). The housekeeping skill now owns RTK integration; this file is the full integration reference.*

## What
RTK (Rust Token Killer) compresses CLI tool output before it reaches the LLM context. Saves 40-97% on tokens for commands like `git diff`, `ls -la`, `grep`, pytest output, and git log.

## Three integration paths — pick the right one

There are three ways to wire RTK into Hermes. They are NOT equivalent.

### Path 1: Bash aliases (legacy — does NOT cover the `terminal` tool)

The `~/.bash_aliases` → `~/.hermes/.hermes_env` chain fires when a human runs commands in a shell. It does NOT fire when Hermes's `terminal` tool calls `subprocess.run` — that bypasses bash aliases entirely. If you see `rtk-compress` listed in `hermes plugins list` as "not enabled" or as an empty stub directory, the bash-alias path is not active for the agent loop.

**Verify before claiming it works:** check `~/.hermes/plugins/rtk-compress/__init__.py` exists and is non-empty. An empty stub means aliases-only — agent loop is unfiltered.

### Path 2: `transform_terminal_output` plugin (CORRECT for the agent loop)

This hook fires inside `tools/terminal_tool.py` *after* command execution and *before* the output enters context. It can replace the output string. A plugin at `~/.hermes/plugins/rtk-compress/` does the actual compression.

**This is the integration path the agent loop needs.** Built and tested 2026-06-05 — see `references/rtk-compress-plugin.md` for full source and the safety-net checklist.

Quick verify:
```bash
ls ~/.hermes/plugins/rtk-compress/__init__.py  # should exist, ~150 lines
hermes plugins list | grep rtk-compress        # should show "enabled"
```

### Path 3: `rtk init` (for Claude Code / Cursor / other assistant CLIs)

`rtk init` installs hooks for specific assistant platforms — see the "Two Separate Hook Systems" section below.

## Install RTK
```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
```

## Integration for Hermes-type agents (legacy bash-alias path)

Use this only for human-driven shells — it does NOT cover the agent loop. For that, build the Path 2 plugin.

```bash
cat > ~/.bash_aliases << 'EOF'
alias git="rtk git"
alias ls="rtk ls"
alias cat="rtk read"
alias grep="rtk grep"
alias diff="rtk diff"
alias docker="rtk docker"
alias pytest="rtk test -- pytest"
alias npm="rtk npm"
alias cargo="rtk cargo"
EOF

cat > ~/.hermes/.hermes_env << 'EOF'
if [ -f "$HOME/.bash_aliases" ]; then
    source "$HOME/.bash_aliases" 2>/dev/null || true
fi
EOF
```

## Verify RTK is active (any path)
```bash
rtk gain   # shows token savings stats
```

## Two Separate Hook Systems — Know Which You're Installing

`rtk init` installs hooks for **specific assistant platforms**. Running it without a target installs for Claude Code only.

| Command | Installs hook for |
|---------|-------------------|
| `rtk init` | Claude Code (`~/.claude/settings.json`) |
| `rtk init -g --agent claude` | Claude Code |
| `rtk init -g --agent cursor` | Cursor Agent |
| `rtk init -g --agent windsurf` | Windsurf IDE |
| `rtk init -g --agent cline` | Cline / Roo Code |

**For Hermes, do NOT use `rtk init`** — it targets Claude Code, not Hermes. Hermes's native integration is the `transform_terminal_output` plugin (Path 2 above).

**Always confirm the target system before installing RTK hooks.** If asked to "install the hook" without specifying which system, ask first.

### Confirm target before installing RTK hooks

When Thomas says "install the hook" or "rtk install" without specifying a system, **ask first** — `rtk init` defaults to Claude Code only. The two systems are separate:

| System | RTK integration | How to activate |
|--------|-----------------|----------------|
| **Hermes agent loop** | `transform_terminal_output` plugin | Build `~/.hermes/plugins/rtk-compress/` (Path 2) |
| **Human shell** | Bash alias wrappers | `~/.bash_aliases` + `~/.hermes/.hermes_env` (Path 1) |
| **Claude Code** | `~/.claude/settings.json` hook | `rtk init -g --auto-patch` |

**Wrong:** Running `rtk init -g` assuming it covers Hermes — it only targets Claude Code.
**Right:** When Thomas says "install the hook" without specifying, confirm: "Hermes, human shell, or Claude Code?" Each needs a different path.

## Hook contract — critical gotcha

- `post_tool_call` → **observational only**, return values are IGNORED
- `transform_tool_result` → can replace tool output (general)
- `transform_terminal_output` → can replace terminal tool output specifically — this is the right hook for RTK

If you write a hook handler for `post_tool_call` and try to modify output via the return value, it silently does nothing. Use `transform_terminal_output` for the `terminal` tool specifically.

## When to use
- Heavy terminal usage in the agent loop (git, ls, grep, pytest, mypy, ruff)
- Token cost optimization — measured 89.8% savings on 279 commands in one session
- Agents with limited context windows
