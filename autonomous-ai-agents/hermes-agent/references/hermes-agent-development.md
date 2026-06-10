# Hermes Agent Monorepo Development

Quick reference for working inside the `hermes-agent` codebase (the framework that runs this agent). Mostly an index — load this only when you're modifying `hermes-agent` itself, not when you're using it.

## Performance & Test Harness

The two most useful files in this area:

- **`references/performance-tuning.md`** — three config tweaks that make the gateway faster (`auto_source_bashrc: false`, `file_read_max_chars: 30000`, `tool_output max_bytes: 30000`)
- **`references/test-harness-improvements.md`** — ranked list of pytest/xdist/testmon/pyright optimizations applied to the hermes-agent test suite, with measured impact and implementation details

## Repo Layout Quick-Reference

```
hermes-agent/
├── run_agent.py          # AIAgent — core conversation loop
├── model_tools.py        # Tool discovery and dispatch
├── toolsets.py           # Toolset definitions
├── cli.py                # Interactive CLI (HermesCLI)
├── hermes_state.py       # SQLite session store
├── agent/                # Prompt builder, compression, memory, routing, skill dispatch
├── hermes_cli/           # CLI subcommands, config, setup, commands
│   ├── commands.py       # Slash command registry (CommandDef)
│   ├── config.py         # DEFAULT_CONFIG, env var definitions
│   └── main.py           # CLI entry point and argparse
├── tools/                # One file per tool, auto-registered via registry.register()
├── gateway/              # Messaging gateway (Telegram, Discord, Slack, …)
├── cron/                 # Job scheduler
├── tests/                # ~3000 pytest tests
└── website/              # Docusaurus docs site
```

Config: `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys).

## Container Architecture (Docker)

For the s6-overlay supervision tree inside the Docker image — service registration, profile gateway lifecycle, Architecture B main-program pattern:

- **`references/s6-container-supervision.md`** — full architectural deep-dive: cont-init.d boot scripts, /run/service slots, gateway-coder/<profile>/ run scripts, reconciler log format, common pitfalls (s6 command-not-found, root-owned profiles, container exit 143)

## Cross-Cutting Patterns

| Pattern | File / Doc |
|---------|-----------|
| gh CLI caching for monitoring scripts | `references/github-script-optimization.md` (in `github-pr-workflow` skill) |
| Parallel `ThreadPoolExecutor` for multi-repo gh scripts | same file as above |
| Pre-commit code review pipeline | `requesting-code-review` skill (auto-fix, 2-stage review) |
| Gateway troubleshooting | `references/gateway-debugging.md` (in main `hermes-agent` skill) |

## Testing

```bash
python -m pytest tests/ -o 'addopts=' -q   # Full suite (clears baked-in addopts)
python -m pytest tests/tools/ -q            # Specific area
```

- Tests auto-redirect `HERMES_HOME` to temp dirs — never touch real `~/.hermes/`
- Run full suite before pushing any change
- `-o 'addopts='` clears any baked-in pytest flags from pyproject.toml

## Layout Pitfalls

Repo-specific gotchas that cost real time when missed. Verify against the actual filesystem before writing any new package.

### `hermes` is a launcher SCRIPT, not a Python package

The file at the repo root (`./hermes`, `#!/usr/bin/env python3`, ~10 lines) is the CLI launcher — it imports from `hermes_cli.main`. There is **no** `hermes/` Python package in this repo. If a spec, plan, or LLM suggests creating `hermes/<name>/`, that's wrong for this repo.

**The trap:** `mkdir hermes/<name>/` *silently clobbers* the launcher (replaces a file with a directory of the same name — no error, no warning). The next `./hermes` invocation fails with `Is a directory`.

**Recovery if you hit it:**
```bash
git checkout HEAD -- hermes && chmod +x hermes
```

**Correct location for new Python packages:**
- Subsystems / feature modules → `hermes_cli/<name>/` (imported as `hermes_cli.<name>.*`).
- Agent internals → `agent/<name>/` (imported as `agent.<name>.*`).
- Tools → `tools/<name>.py` (auto-registered via `registry.register()`).
- Skills → `skills/<name>/SKILL.md` (lazy-loaded).

Document the deviation in any PR description that contradicts the spec — the spec writer probably assumed a different repo layout.

### CLI subcommand dispatcher pattern

When wiring a new top-level subcommand in `hermes_cli/main.py`, follow the `fallback_cmd.py` convention, not the standalone-argparse style:

```python
# Right: dispatcher accepts a Namespace and routes on an attr.
def cmd_myfeature(args) -> int:
    sub = getattr(args, "myfeature_command", None)
    if sub == "init":   return _init(args)
    if sub == "status": return _status(args)
    ...

my_parser.set_defaults(func=cmd_myfeature)
```

The parent argparse parser already populated `args.myfeature_command` (set by the subparser's `dest=`). Don't re-parse argv in the leaf — that fails with `TypeError: 'Namespace' object is not iterable`.

## When NOT to Load This

If you're a *user* of Hermes, not a contributor — you want the main `hermes-agent` skill, not this development reference.
