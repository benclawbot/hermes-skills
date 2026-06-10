---
name: ambient-agent-architecture
description: >
  Architecture patterns for persistent, ambient AI agents — systems that run continuously,
  maintain memory across sessions, execute proactive background work, and expose tools via
  MCP and WebSocket gateways. Loaded when discussing or building ambient/run-always agent
  systems, memory graph architectures, cross-platform agent engines, or tool integration
  layers. - `references/iagent-windows-patterns.md` — iAgent-windows README conventions, image sourcing patterns, active build objectives, and git hygiene for standalone repostriggers:
  - ambient agent
  - persistent memory agent
  - background agent scheduler
  - WebSocket gateway for agents
  - memory graph architecture
  - MCP client pool
  - skill system for agents
---

# Ambient Agent Architecture

## Core Architecture

An ambient agent is a persistent background AI system that:
1. Runs continuously, not in message-response bursts
2. Maintains memory across sessions via a knowledge graph
3. Schedules and executes proactive background work
4. Exposes tools via MCP and WebSocket gateways
5. Supports desktop dock UI (system tray / dock icon)

## Key Components

### 1. Engine Core (language-agnostic)
The core is a language-agnostic agent runtime — in iAgent's case, a Rust monorepo with these key crates:
- `jcode-core` — session management, message handling, protocol
- `jcode-agent` — turn execution, tool calling, streaming
- `jcode-memory` — embedding, graph storage, retrieval
- `jcode-provider-*` — OpenAI, Claude, MiniMax, OpenRouter provider abstractions
- `jcode-mcp` — MCP client pool and protocol implementation

### 2. Memory Graph
Entity/edge model (not flat embeddings). Schema:
- `ClusterEntry` — concept cluster with confidence
- `Edge` + `EdgeKind` — typed relationships between entities
- `GraphMetadata` — version, last compaction timestamp

The memory agent runs as a separate LLM-powered process (MiniMax M2.7 in Thomas's setup) alongside the main agent. It handles:
- Embedding search + relevance verification
- Memory surfacing to main agent per turn
- Background maintenance (cluster refinement, confidence adjustment, gap detection)
- Final extraction at session end

### 3. Ambient Scheduler
Persistent background scheduler with:
- `ScheduledItem` — task with priority, target (Ambient/Session/Spawn), working dir context
- `ScheduleTarget` — delivery modes:
  - `Ambient` — wake ambient agent with queued task
  - `Session` — deliver reminder into specific interactive session
  - `Spawn` — spawn new session derived from originating session
- `AmbientStatus` — Idle / Running / Scheduled / Paused / Disabled

### 4. WebSocket Gateway
TCP/7643 WebSocket gateway for remote clients (iOS, web):
- Auth via Bearer token (64-char hex) or query param `?token=`
- Device pairing via 6-digit codes (5-min expiry)
- Virtual Unix socket pair bridging WebSocket ↔ newline-delimited JSON
- Ping/pong keepalive (20-sec interval)
- HTTP endpoints: `GET /health`, `POST /pair`, `GET /status`
- Device registry persisted to `~/.jcode/devices.json`

**What it needs to be complete:**
- TLS termination (or documented clear that it's behind a tunnel)
- `handle_client` bridge verification — virtual socket pair must actually route to server loop
- Session resurrection on reconnect (replay last N messages)
- APNs push for iOS notifications

### 5. MCP Integration
MCP client pool with:
- Shared servers (reused across sessions) vs owned servers (per-session, for stateful like Playwright)
- Protocol: JSON-RPC over stdio
- Config: `~/.config/jcode/mcp.json` with server definitions

## Application Integration Stack

For deep OS integration (Windows), COM automation via `windows-rs` is the right call:
- Word/Excel/PowerPoint via Office COM objects
- Browser automation via CDP (Chromium DevTools Protocol)

For cross-platform, Microsoft Graph API handles Office 365 cloud docs.

### Skill Framework (iAgent-windows, as built)

**Discovery:** `~/.jcode/skills/`, `./.jcode/skills/`, `./.claude/skills/`

**Frontmatter fields** (all comma-separated strings):
```yaml
scripts: deploy.sh, rollback.sh    # declared scripts
platforms: windows, linux           # OS restriction (empty = all)
allowed-tools: bash, read, write  # restricts agent toolset when skill active
```

**Platform filtering:** `Skill::is_available_for_current_platform()` uses `std::env::consts::OS`, checked at load time in `load_from_dir()`.

**Invocation:** `/skillname` → sets `active_skill` → prompts injected into system prompt on next turn. No tool-calling bridge — skills become context.

**`allowed-tools` enforcement:** `fn sync_allowed_tools_from_active_skill(&mut self)` in `src/agent.rs:251` reads `skill.allowed_tools` and sets `self.allowed_tools = Some(HashSet)`. Called from `turn_execution.rs:606` and `tui/app/input.rs:2002`.

**Per-skill scripts:** `SkillScriptTool` (`src/tool/skill_script.rs`) reads `scripts/` directory and executes via `BashTool`. Takes `skill`, `script`, `args` params.

**Skill frontmatter parse:** `SkillFrontmatter` in `src/skill.rs` deserializes `scripts:`, `platforms:`, `allowed-tools:` from YAML.

### Application Integrations Stack (iAgent-windows, as built)

**`crates/app-integrations/`** — Modules: `browser`, `form_fill`, `officecli`. Wired into `AppTool` (`src/tool/app.rs`) and registered in `Registry::new()` at `src/tool/mod.rs:257`.

**Browser CDP** (`browser.rs`): Chrome/Edge over HTTP/WebSocket (port 9222). `BrowserType` enum (Chrome/Edge). `CdpBrowser` struct with async methods: `list_tabs`, `attach_to_tab`, `new_tab`, `navigate`, `get_interactables`, `fill_form`, `click`, `evaluate`, `screenshot`, `get_content`. CDP structs: `CdpTab`, `CdpInteractable`, `CdpFormField`, `CdpRect`. Browser discovery via `discover_browsers()` — probes default Chrome/Edge install paths. `remote_debugging_flags()` returns launch flags per browser type.

**Form fill** (`form_fill.rs`): High-level async wrappers over CDP with smart selector matching. `FormFillRequest` with URL + field list; `fill_form()` extracts interactable elements and populates them. `fill_single_field()` for single-field operations.

**OfficeCLI** (`officecli.rs`): Subprocess wrapper for [iOfficeAI/OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) (4.7k stars, self-contained C# binary, no Office installation required). Works on Windows, macOS, Linux.

- **Word (.docx):** `create`, `view`, `stats`, `validate`, `text`, `get`, `query`, `set`, `add`, `add_after`, `replace`, `format_text`, `remove`, `open`, `close`, `export_html`, `batch`, `docx_insert_paragraph`, `docx_bold`
- **Excel (.xlsx):** `get`, `set`, `stats`, `open`, `close`, `xlsx_set_cell`, `xlsx_set_formula`, `xlsx_get_range`
- **PowerPoint (.pptx):** `add`, `get`, `set`, `pptx_add_slide`, `pptx_add_textbox`, `pptx_set_shape`, `pptx_get_shapes`

Returns structured JSON output. `is_installed()` and `version()` for availability checks. `batch()` runs multi-step workflows from a single JSON command string. `AppTool::officecli_ready()` helper exposes availability to the tool layer.

**Install:** `scripts/install.ps1` includes `Install-OfficeCLI` (downloads latest release via GitHub API) and `Test-OfficeCLIInstalled`. Manual: `irm https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 | iex` (Windows), `curl -fsSL .../install.sh | bash` (macOS/Linux). Verify: `officecli --version`.

### Skill Framework (Hermes)

- Discovery: `~/.hermes/skills/` + `skills.external_dirs` from config
- Platform filtering (`linux`, `macos`, `windows`)
- Two invocation paths: slash command (injects as user msg) and `skill_view` tool (returns JSON)
- Template vars and inline shell expansion (`!`cmd``)
- Security: path traversal guards, prompt injection scanning, env var capture
- Per-skill scripts: `tools/skill_script_tool.py` — `list_scripts` and `exec` actions, registered in tool registry, 300s timeout, respects working_dir
- Skill script injection: `_inject_skill_scripts()` in `skill_commands.py` reads `scripts:` frontmatter and lists disk scripts in activation messages
- `get_skill_scripts()` in `skill_utils.py` — returns `List[Tuple[str, Path]]` from skill's `scripts/` directory

## Memory Agent Model Priority

Thomas's memory agent uses **MiniMax-M2.7**, not Haiku or Codex-Spark. Routing:
- Sidecar abstraction for cheap/fast calls (Haiku, codex-spark)
- Full provider path for memory agent (MiniMax M2.7)
- Config: `config().agents.memory_model`

## Reference: iAgent-windows Architecture

52-crate Rust monorepo workspace. Key binaries:
- `iagent` — main CLI entrypoint
- `iagent-ambient` — standalone ambient runner
- `iagent-overlay-ui` — overlay UI daemon (Rust/tokio, no rendering widget)

Install layout (Windows):
- `%LOCALAPPDATA%\iAgent\bin` — backend CLI
- `%LOCALAPPDATA%\iAgent\app` — desktop dock frontend (separate Python package, downloaded at install time from `github.com/benclawbot/iagent`)

Dock: separate `iagent-py` Python package (PySide), not in the iAgent-windows repo. Launched via PowerShell/VBS chain.

Overlay-ui: pure Rust, `tokio::sync::mpsc::UnboundedSender<OverlayEvent>`, headless by default. No actual dock rendering in this binary.

TUI overlays: ratatui (Rust), not Qt/PySide.

## iAgent-windows Update (2026-05-21)

**Office stubs → OfficeCLI:** `word.rs`, `excel.rs`, `powerpoint.rs` were `unimplemented!()` COM stubs. Replaced with `officecli.rs` — subprocess wrapper for [iOfficeAI/OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) (4.7k⭐, C# binary, no Office required). `app-integrations` now exports: `browser`, `form_fill`, `officecli`. Deleted: `outlook.rs`, `vscode.rs`.

**Install script updated:** `scripts/install.ps1` now includes `Install-OfficeCLI` function (downloads latest `officecli-win-x64.exe` from GitHub releases) and `Test-OfficeCLIInstalled` helper. OfficeCLI status shown at end of install.

**AppTool wired:** `src/tool/app.rs` fully rewritten with `oc_*` OfficeCLI actions + browser/form_fill CDP actions. `AppTool::officecli_ready()` helper added. Registered in `Registry::new()` at `src/tool/mod.rs:257`.

**WebSocket gateway state:** `GET /status` HTTP endpoint exists (returns version, backend name). `/ws` WebSocket fully implemented with token auth, keep-alive pings (20s), newline-delimited JSON bridge to `handle_client()`. No completion endpoint needed — `transport/` platform split (Unix: 19 lines native `Stream::pair()`, Windows: 421 lines named pipes with crypto auth) is correct and not a stub.

**README visual preferences:** Thomas prefers visual content (infographic, screenshots) over technical diagrams in README/docs. Architecture SVG called "ugly" — removed from README. README updated to show infographic + desktop screenshot at top, with a detailed "Desktop Integrations" section covering CDP browser automation, web form fill, and full OfficeCLI capabilities for Word/Excel/PowerPoint. No emoji in title. README is a primary product-facing document — keep it clean and visually oriented.