# iAgent-windows Repo: Findings from Code Review (2026-05-20)

## Repo Location
`github.com/benclawbot/iAgent-windows` — 52-crate Rust workspace, forked from `jcode`.

## Directory Structure (key paths)

```
iAgent-windows/
├── crates/
│   ├── skill/           # skill registry, loader, tool
│   ├── app-integrations/  # outlook, powerpoint, vscode stubs only
│   ├── overlay-ui/      # Rust/tokio overlay daemon
│   ├── jcode-core/      # session, messages, protocol
│   ├── jcode-agent/     # turn execution, streaming, tools
│   ├── jcode-memory-types/ # graph schema
│   ├── jcode-memory/    # MemoryManager, embedding, retrieval
│   ├── jcode-provider-*/  # OpenAI, Claude, OpenRouter, Gemini
│   ├── jcode-mcp/       # MCP client + manager + pool
│   └── jcode-desktop/   # desktop integration traits
├── src/
│   ├── agent/           # turn_execution.rs, prompting.rs
│   ├── gateway/         # WebSocket gateway (TCP/7643)
│   ├── tui/             # ratatui-based overlays
│   └── bin/
│       └── overlay_ui.rs  # overlay daemon binary
└── scripts/
    └── install.ps1      # comprehensive Windows installer
```

## Skill System (crates/skill/)

### Core Files
- `crates/skill/src/skill.rs` — `SkillRegistry`, `load_for_working_dir()`, `parse_frontmatter()`, 458 lines
- `crates/skill/src/tool/skill.rs` — `skill_manage` tool: `load`, `list`, `reload`, `reload_all`, `read`
- `src/agent/turn_execution.rs:600-608` — `/skillname` parsing → `active_skill`
- `src/agent/prompting.rs:80-91` — skill prompt injection into system prompt

### Discovery
```rust
// First-run import from Claude Code / Codex CLI
Self::import_from_external();
// Loads from:
~/.jcode/skills/       // global jcode skills
./.jcode/skills/       // project-local
./.claude/skills/      // Claude Code compat
```

### Metadata Format (YAML frontmatter)
```rust
struct SkillFrontmatter {
    name: String,
    description: String,
    #[serde(rename = "allowed-tools")]
    allowed_tools: Option<String>,  // parsed but NOT enforced
}
```
```yaml
---
name: skill-name
description: "..."
allowed-tools: "tool1,tool2"
---
```

### Invocation Path
`/skillname` → `SkillRegistry::parse_invocation()` → sets `active_skill` → skill prompt injected into system prompt on next turn. **No tool-calling bridge** — skills become context, not tools.

## app-integrations Crate

**Path:** `crates/app-integrations/src/`

| File | Status | Detail |
|------|--------|--------|
| `lib.rs` | Exports 3 modules | `outlook`, `powerpoint`, `vscode` |
| `outlook.rs` | Stub | `connect()` → `Ok(Self)`, `get_active_email_draft()` → empty `EmailDraft`, `apply_email_suggestion()` no-op |
| `powerpoint.rs` | Stub | Regex heuristics only (word count, line length), no actual Office interop |
| `vscode.rs` | LSP builder | No VS Code extension runtime |

**Not wired:** `Cargo.toml` depends on it, but `src/` has no `use app_integrations`. Dead code.

**Missing:** Word, Excel, browser (Chrome/Edge), form-fill modules.

## Dock UI

**iAgent-windows overlay-ui** (`crates/overlay-ui/`): Pure Rust, tokio async. `OverlayClient` uses `tokio::sync::mpsc::UnboundedSender<OverlayEvent>`. Send-only channel, headless daemon, no actual rendering widget.

**Actual dock** comes from **separate Python package** `iagent-py` — downloaded from `github.com/benclawbot/iagent` at install time. Not in this repo.

**TUI overlays** (`src/tui/`): ratatui (Rust), not Qt/PySide.

## PowerShell Install Script

`scripts/install.ps1` — fully implemented:
- Downloads `iagent-py` from `github.com/benclawbot/iagent` → `%LOCALAPPDATA%\iAgent\app`
- Hotkey: Alt+; via P/Invoke `RegisterHotKey` + VBS launcher + Startup shortcut
- Dock launcher: `launch-iagent-dock.ps1` + `launch-iagent-dock.vbs`
- All PowerShell scripts are functional, not stubs

## Key Gaps (vs Architecture Spec)

| Spec | Reality |
|------|---------|
| Word COM automation | Missing |
| Excel COM automation | Missing |
| PowerPoint real interop | Stub only |
| Browser (Chrome/Edge) automation | Missing |
| Form-fill stub | Missing |
| `allowed-tools` enforcement | Parsed but ignored |
| app-integrations wired to agent | Not wired |
| PySide dock in this repo | Separate Python package |
| Per-skill scripts → callable tools | Neither codebase does this |