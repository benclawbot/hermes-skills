# RTK Integration — Hermes vs Claude Code

RTK (Rust Token Killer) compresses CLI tool output before it hits the LLM context. Two separate integration points, one goal.

## Two integration layers

### Hermes — bash alias layer (always active)
Hermes terminal commands go through `.hermes_env` → `~/.bash_aliases`, which wraps core commands:
```bash
alias git="rtk git"
alias ls="rtk grep"
alias cat="rtk read"
alias grep="rtk grep"
alias rg="rtk rg"
# ... etc
```
This is pre-existing and works transparently — `rtk gain` confirms it's active.

### Claude Code — settings.json hook (manual install)
Claude Code doesn't use bash aliases. It needs the explicit hook:
```bash
rtk init -g --auto-patch
```
This adds to `~/.claude/settings.json` under `hooks.PreToolUse`.

**Installation steps:**
1. Run `rtk init -g` — interactive, prompts for settings.json patch
2. Or `rtk init -g --auto-patch` — non-interactive
3. Manually add to settings.json if needed:
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "rtk hook claude" }]
    }]
  }
}
```

## Verification
```bash
rtk gain              # overall savings (Hermes layer)
rtk status            # hook status for Claude Code
```

## Filter customization
User-global filters: `~/.config/rtk/filters.toml`