---
name: csl-policy
description: CSL-Core deterministic policy enforcement for hermes-agent. Z3-verified rules block credential leaks, enforce git safety, validate cron/skill creation. Integrates via pre_tool_call hook.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [safety, credentials, git, policy, z3, csl-core, enforcement]
    related_skills: [github-repo-management, github-pr-workflow]
---

# CSL-Core Policy Enforcement

Deterministic safety layer for hermes-agent operations. Policies are `.csl` files verified by Z3
before activation, enforced at runtime via the `pre_tool_call` hook.

## Quick Start

```bash
# Verify all policies (Z3 check)
hermes policy verify

# List loaded policies and rules
hermes policy list

# Hot-reload after editing a .csl file
hermes policy reload

# Test a scenario against policies
hermes policy test terminal '{"command": "git add .wrangler/"}'
```

## Policies

### safety.csl (Priority 1)
Blocks credential leaks via build artifacts and enforces pre-push staging checks.

**Blocked paths:**
- `.wrangler/` — Cloudflare Workers build (contains .map with embedded secrets)
- `.next/`, `dist/`, `out/` — build output
- `*.map` — source maps embed original source
- `*.pem`, `*.key`, `secrets.json`, `credentials.json` — secret files
- `.env`, `.env.local`, `.env.*.local` — env files with real keys

**Rules:**
- `git add` / `git commit` → blocked if any blocked path is staged
- `git push` → blocked if staging area hasn't been checked (no `git status` + `git diff --cached`)

### agent-behavior.csl
Validates agent operations at creation time.

**Rules:**
- `cronjob create` → blocked if no `prompt` field
- `cronjob create` → blocked if `repeat` is set on first call (defer to update)
- `delegate_task` → blocked if no explicit scope in context
- `skill_manage create` → blocked if SKILL.md frontmatter missing `name` or `description`

### workflow.csl
Enforces workflow conventions.

**Rules:**
- `cronjob create` → delivery defaults to `"origin"` if not specified
- `skill_manage create` → validates SKILL.md frontmatter before completing
- Plan mode → `.hermes/plans/` file must exist before execution proceeds

## Policy Paths

- **Shipped policies:** `skills/csl-policy/policies/*.csl`
- **User overrides:** `~/.hermes/policies/*.csl` (loaded after shipped, overrides same-name policies)

## Enforcement Modes

- **ADVISORY** (default during rollout) — warn on violation, let through. Logs to `agent.log`.
- **ENFORCING** — block on violation. Switch via `hermes policy mode <policy> ENFORCING`.

## Files

```
skills/csl-policy/
├── SKILL.md                      # This file
├── policies/
│   ├── safety.csl               # Build artifact block + pre-push staging check
│   ├── agent-behavior.csl      # Cron, delegation, skill frontmatter rules
│   └── workflow.csl             # Plan mode + delivery conventions
└── scripts/
    ├── load_guard.py            # PolicyEngine: compile, track staging state, check_tool_call()
    └── verify_policies.py       # Standalone: chimera_core.cli verify on all .csl files

plugins/csl_enforce/             # Repo root (NOT hermes_cli/plugins/)
├── __init__.py                  # on_pre_tool_call hook + hermes policy CLI
└── plugin.yaml                  # kind: backend, auto-loads on startup
```

## Dependencies

- `csl-core >= 0.4.0`
- `z3-solver >= 4.12` (installed with csl-core)

## Integration Point

The `csl_enforce` plugin (`plugins/csl_enforce/`, `kind: backend`) registers a `pre_tool_call` callback.
Before every tool call, the guard evaluates the action against loaded .csl policies. Block/warn/allow
is determined by the policy's `ENFORCEMENT_MODE` setting and the rule's constraint satisfaction.

**Plugin path matters:** `PluginManager.get_bundled_plugins_dir()` resolves to the **repo root** `plugins/`,
not `hermes_cli/plugins/`. Placing a plugin in `hermes_cli/plugins/` silently fails discovery.

**Hook callback contract:** `on_pre_tool_call(tool_name, args)` must return `None` (allow) or a dict
`{"action": "block", "message": "reason"}`. The gateway's `get_pre_tool_call_block_message()` processes these.

**Hot reload:** call `hermes policy reload` to clear `chimera_core.runtime._guard_cache` and recompile.

## Pitfalls

### Z3 constraint engine — one constraint per WHEN clause
CSL compiles each constraint to a Z3 assertion. When a WHEN clause has chained `AND` conditions and
multiple `THEN` clauses, Z3 reports "sort mismatch". **Fix:** split into separate `STATE_CONSTRAINT`
blocks, one per assertion. E.g.:

```csl
// WRONG — sort mismatch on combined THEN clauses
STATE_CONSTRAINT skill_create_requires_frontmatter {
  WHEN tool == "skill_manage" AND action == "create"
  THEN has_name == "TRUE" AND has_description == "TRUE"
}

// RIGHT — separate constraints
STATE_CONSTRAINT skill_create_requires_name {
  WHEN tool == "skill_manage" AND action == "create"
  THEN has_name == "TRUE"
}
STATE_CONSTRAINT skill_create_requires_description {
  WHEN tool == "skill_manage" AND action == "create"
  THEN has_description == "TRUE"
}
```

### ENUM values cannot collide across policies
If `safety.csl` uses `CLEAN` and `agent-behavior.csl` also uses `CLEAN` as value labels,
Z3 produces "logic verification failed: sort mismatch" on the second-loaded policy.
**Fix:** namespace ENUM values with policy-specific prefixes (e.g., `STATE_CLEAN`, `AB_HAS_NAME`).

### Package name is `chimera_core`, not `cslcore`
`pip install csl-core` installs package `chimera_core`. Import with:
```python
from chimera_core import load_guard  # NOT from csl_core import ...
```
Also: `ChimeraGuard.verify()` returns an object with `.allowed` (bool) and `.violations` (list) — not a dict.

### State machine in load_guard.py
The `_staging_state` and `_staging_checked` flags are **stored on the PolicyEngine instance**, not
in the CSL context. They persist across tool calls in a session. To reset between independent
invocations, re-instantiate `PolicyEngine()` or call `engine._staging_checked = "FALSE"` before
the test sequence.

### The install-time gate does NOT cover already-installed skills
`tirith` runs at `hermes skills install` time. A `scan_verdict: "dangerous"` blocks the install.
But if the skill was installed *before* the verdict was assigned, or installed via a different
code path, the lock.json entry stays `installed: true` indefinitely. Verified live:
`~/.hermes/skills/.hub/audit.log` shows `taste-skill` was `BLOCKED ... dangerous 6_findings` twice
(May 28, Jun 5) but `~/.hermes/skills/.hub/lock.json` still showed `installed: true` for 9+ days.
The gate's enforcement is *prospective* (it stops new installs), not *retrospective* (it doesn't
re-quarantine skills whose verdicts changed). A periodic cron / hermes-housekeeping sweep of
`lock.json` for `scan_verdict == "dangerous" AND trust_level == "community"` is the missing
defensive layer. Future direction: add a CSL rule in `agent-behavior.csl` that fires
`hermes curator archive` on any hub install whose `scan_verdict` became `dangerous` after
install. Until that rule exists, the audit/cleanup is human-driven via the
`hermes-housekeeping` skill.

### CSL syntax rules
- `MUST NOT BE IN {value1, value2}` — the `NOT ... IN` form is invalid
- String constants must be valid Z3 identifiers — no hyphens, no dots → use underscores
- `CONFIG { ENFORCEMENT_MODE = ADVISORY }` — only `BLOCK`, `WARN`, `LOG` are valid values
- Variables must have explicit types: `var name: TYPE`
- Constants block is not valid CSL — inline domain values directly
- `_context_has_goal_or_context` — use this when checking scope presence, not a custom function
