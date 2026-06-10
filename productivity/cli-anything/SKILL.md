---
name: cli-anything
description: "Discover, install, and run CLI harnesses from the CLI-Anything ecosystem (HKUDS/CLI-Anything and CLI-Anything-WEB). Use when Thomas wants to work with CLI tools generated for specific websites or applications."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [cli, automation, web, agents, tool-generation]
    trigger: [cli-anything, CLI harness, generate CLI for website, cli-hub, cli-web]
---

# CLI-Anything

A unified interface for the CLI-Anything ecosystem — two related but distinct tools for generating and running agent-native command-line interfaces.

## The Two Projects

| Project | Purpose | Repo |
|---------|---------|------|
| **CLI-Anything** (HKUDS) | Discover and run ready-made CLI harnesses for desktop/server apps | [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything) |
| **CLI-Anything-WEB** | Generate agent-native CLIs for websites by observing live browser traffic | [ItamarZand88/CLI-Anything-WEB](https://github.com/ItamarZand88/CLI-Anything-WEB) |

## Skills Map

| Task | Skill |
|------|-------|
| Discover/install CLI harnesses via cli-hub | `cli-anything-hub` (absorbed below) |
| Generate new CLI for a website | `cli-anything-web` (absorbed below) |
| Both | *(this skill — overview and decision guide)* |

## When to Use Each

### Use cli-hub (CLI-Anything) when:
- Thomas wants a CLI for an app that already has a generated harness
- Examples: Obsidian, Linear, Airtable, Notion
- Pattern: `cli-hub search → cli-hub install → cli-anything-<name> --json`

### Use cli-anything-web when:
- Thomas wants to interact with a website that doesn't have a ready-made harness
- Thomas wants to generate a new CLI for a site
- Pattern: Claude Code plugin observes browser → generates harness → cli-web-\<site\> --json

---

## CLI-Anything-Hub

*Full content absorbed from `cli-anything-hub` skill.*

### Overview

Use `cli-hub` to discover and install ready-made `cli-anything-*` harnesses from HKUDS/CLI-Anything.

### Core commands

```bash
cli-hub list
cli-hub list --json
cli-hub search "<keyword>" --json
cli-hub info <name>
cli-hub install <name>
cli-hub update <name>
cli-hub uninstall <name>
cli-hub launch <name> -- --help
```

### Typical workflow

1. Search: `cli-hub search "<keyword>" --json`
2. Inspect: `cli-hub info <name>`
3. Install: `cli-hub install <name>`
4. Use: `cli-anything-<name> --help`

### Example: Obsidian

```bash
cli-hub info obsidian
cli-hub install obsidian
cli-anything-obsidian --help
cli-anything-obsidian --json server status
cli-anything-obsidian --json search simple "meeting notes"
```

### Notes

- `cli-hub` is only the package manager; each app installs a separate `cli-anything-<name>` executable
- Check `cli-hub info <name>` before installing — many harnesses require the target app to be installed locally
- Prefer `--json` for agent use

---

## CLI-Anything-WEB

*Full content absorbed from `cli-anything-web` skill.*

### Overview

Use the CLI-Anything-WEB project to generate or use agent-native CLIs for websites.

### Decision guide

- Prefer an existing generated `cli-web-*` tool from the repo if the site is already covered
- Otherwise use Claude Code with the plugin to generate a new CLI from live website traffic
- Best for quick CLI access to websites with agent-friendly `--json` output

### Repo paths

- Repo clone: `/tmp/cli-anything-web`
- Plugin dir: `/tmp/cli-anything-web/cli-anything-web-plugin`

### Basic workflow

1. Check whether the repo already contains a generated CLI for the target site
2. If yes, install from `<site>/agent-harness/` and use `cli-web-<site> ... --json`
3. If not, run Claude Code with the plugin loaded:

```bash
cd /tmp/cli-anything-web
claude --plugin-dir /tmp/cli-anything-web/cli-anything-web-plugin
```

Then inside Claude:

```bash
/cli-anything-web https://target-site.example.com
```

### Good starter examples

```bash
cd /tmp/cli-anything-web/gh-trending/agent-harness && python3 -m pip install -e .
cli-web-gh-trending repos list --language python --since weekly --json

cd /tmp/cli-anything-web/unsplash/agent-harness && python3 -m pip install -e .
cli-web-unsplash photos search "mountains" --json
```

### Notes

- Requires Claude Code, Node.js, Python 3, and Playwright CLI
- Some sites need browser login during capture
- `--mitmproxy` is available for harder captures
- Generated CLIs use undocumented web APIs and can break when websites change
