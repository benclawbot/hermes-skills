# iAgent-windows Build & Dev Notes

## Cargo Workflow

### Always prefer targeted builds over full workspace
Full `cargo build` on the 52-crate workspace times out (>600s). Use targeted checks:

```bash
# Single crate (instant)
cargo check -p app-integrations

# Main lib only (fast)
cargo check -p iagent --lib
```

### Pre-existing E0670 lint errors (ignore)
`cargo check` reports `E0670: 'async fn' is not permitted in Rust 2015` — these are false positives from `edition = "2024"` in `Cargo.toml`. Filter them when checking output:

```bash
cargo check -p iagent --lib 2>&1 | grep -v "E0670"
```

### Running tests
`cargo test -p app-integrations --lib` compiles `tokio` from scratch (~20 min cold). Run in background:

```bash
cargo test -p app-integrations --lib 2>&1 | tail -5 &
# Check with process list or wait for notification
```

## Git Push Workflow

On this machine, HTTPS repos don't have credential helper configured — `git push` always fails with "could not read Username". Use token injection:

```bash
# Standard push (fails)
git push

# With token (works)
git push "https://$(gh auth token)@github.com/benclawbot/iAgent-windows.git"

# After pull-rebase (when remote has commits ahead)
git pull --rebase "https://$(gh auth token)@github.com/benclawbot/iAgent-windows.git"
git push "https://$(gh auth token)@github.com/benclawbot/iAgent-windows.git"
```

## File Organization

- `crates/app-integrations/` — Browser CDP, OfficeCLI, form fill. This is the integration layer.
- `src/tool/app.rs` — `AppTool`, the unified tool registered in `Registry::new()`
- `src/tool/mod.rs` — `Registry::new()` — where all tools are registered (line ~257 for AppTool)
- `src/gateway.rs` — WebSocket gateway, HTTP endpoints (`/health`, `/status`, `/pair`)
- `scripts/install.ps1` — Windows installer; also installs OfficeCLI
- `docs/assets/` — README images (infographic, screenshots)
