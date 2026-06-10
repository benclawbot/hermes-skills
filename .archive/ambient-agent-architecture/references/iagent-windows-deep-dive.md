# iAgent-windows Deep Dive

Reference implementation: https://github.com/benclawbot/iAgent-windows

## Architecture Overview

52-crate Rust monorepo workspace. Forked from `jcode` (original) → `iagent` (product name).

### Crate Structure

**Core engine crates:**
- `jcode-core` — session, messages, protocol
- `jcode-agent` — turn execution, streaming, tools
- `jcode-memory-types` — graph schema (ClusterEntry, Edge, EdgeKind, GraphMetadata)
- `jcode-memory` — MemoryManager, embedding, retrieval
- `jcode-provider-core` — provider trait definition
- `jcode-provider-openai`, `jcode-provider-claude`, `jcode-provider-openrouter`, `jcode-provider-gemini` — provider implementations
- `jcode-mcp` — client + manager + pool + protocol

**Feature crates:**
- `jcode-desktop` — desktop integration traits
- `jcode-terminal-launch` — PTY/spawn logic
- `jcode-tui-*` — ratatui-based terminal UI components
- `jcode-compaction-core` — conversation compaction
- `jcode-swarm-core` — multi-agent coordination
- `jcode-plan` — planning subsystem
- `jcode-session-types` — session data structures

**Binaries:**
- `iagent` — main CLI
- `iagent-ambient` — standalone ambient runner
- `iagent-overlay-ui` — overlay UI process
- `iagent-harness` — test harness
- `iagent-test-api` — API tester

### Key Source Files (src/)

**Agent:** `agent.rs` — Agent struct with provider, registry, session, tool handling. 1800+ lines.

**Memory:**
- `memory_agent.rs` — Dedicated Haiku-powered agent for memory management. Transforms session transcript → memories. Surface mechanism: `PENDING_MEMORY` injection per turn.
- `memory_graph.rs` — Compatibility re-export to `jcode-memory-types`
- `memory.rs` — MemoryManager with list/get/store/forget/tag/link operations

**Ambient:**
- `ambient.rs` — Types: AmbientState, AmbientStatus, ScheduledItem, ScheduleTarget, CycleStatus, AmbientCycleResult
- `ambient_scheduler.rs` — Persistent scheduler with queue
- `ambient_runner.rs` — Runs ambient cycles

**Gateway:**
- `gateway.rs` — WebSocket gateway on TCP/7643. HTTP endpoints: GET /health, POST /pair. Bridge: virtual Unix socket pair.
- `gateway/auth.rs` — Bearer token + query param auth. 64-char hex token validation.
- `gateway/registry.rs` — DeviceRegistry: pair_device(), validate_token(), generate_pairing_code()

**Providers:**
- `provider_catalog.rs` — OpenAiCompatibleProfile registry. Includes MiniMax profile with `MiniMax-M2.7`, `MiniMax-M2.7-highspeed`, `MiniMax-M2.5`, etc. Env vars: `MINIMAX_API_KEY`

**Sidecar:**
- `sidecar.rs` — Lightweight fast model client. Currently routes to OpenAI (codex-spark) or Claude (haiku). NOT MiniMax. Uses OpenAI Responses API or Claude Messages API.

## Memory Agent → MiniMax M2.7

**Current state:** Sidecar uses Haiku or codex-spark. Memory agent calls sidecar.

**Required change:** Route memory agent to MiniMax M2.7 via full provider path.

In `sidecar.rs`, add `SidecarBackend::MiniMax` variant and detect `MINIMAX_API_KEY`:
```rust
// MiniMax OpenAI-compatible endpoint
const MINIMAX_API_BASE: &str = "https://api.minimax.chat/v1";
```

In `memory_agent.rs`, the memory agent should use `config().agents.memory_model` (e.g. "MiniMax-M2.7") and call the provider directly, not through sidecar (since M2.7 is not a "cheap/fast" model).

## Provider Catalog — MiniMax Models

```rust
"minimax" => {
    push("MiniMax-M2.7");
    push("MiniMax-M2.7-highspeed");
    push("MiniMax-M2.5");
    push("MiniMax-M2.5-highspeed");
    push("MiniMax-M2.1");
    push("MiniMax-M2.1-highspeed");
    push("MiniMax-M2");
}
```

Env var: `MINIMAX_API_KEY`. API base: `https://api.minimax.chat/v1` (OpenAI-compatible).

## MCP Configuration

Config at `~/.config/jcode/mcp.json`:
```json
{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp-server"],
      "shared": false
    }
  }
}
```

`shared: true` → pool reuse. `shared: false` → per-session spawn (stateful).

## Transport Layer

`src/transport/mod.rs` — Unix/Windows platform split:
```rust
#[cfg(unix)]
mod unix;
#[cfg(windows)]
mod windows;
```

Platform-specific stream pair creation for gateway bridging.