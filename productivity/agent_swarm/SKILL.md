---
name: agent-swarm
description: "Use when coordinating multiple agents without a central orchestrator. Pattern: many small specialized agents (cron jobs, delegate_task children, or in-session skill invocations) write structured entries to a shared scratchpad file; one aggregator agent reads and synthesizes. Replaces single-orchestrator setups across cron, delegation, and in-session flows."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [swarm, coordination, stigmergy, multi-agent, cron, delegation]
    related_skills: [autonomous-ai-agents]
---

# Agent-Swarm Coordination (Stigmergic)

## Overview

Xenobots coordinate without an orchestrator — they leave chemical traces in
the world and other xenobots respond. This skill encodes the same pattern
for Hermes agents: many small specialists (each with one narrow
responsibility) write structured entries to a shared JSON scratchpad file,
and one aggregator reads the file and synthesizes a result. No agent has
the whole picture. Each piece is bounded; the intelligence lives in the
aggregation pattern.

Works across three execution modes:

1. **Cron** — specialists are cron jobs (cheap, scheduled, no_agent=True)
2. **`delegate_task` sweeps** — specialists are parallel children (bounded, in-session)
3. **In-session multi-skill** — specialists are skill invocations within one session

## When to Use

- You have a multi-step workflow (morning brief, research sweep, nightly
  digest) where sub-tasks are independent.
- Failures in one sub-task shouldn't block the others.
- You want each sub-task to be cheap, bounded, and inspectable.
- You'd otherwise write one big prompt that tries to do everything.

## When NOT to Use

- Sub-tasks genuinely need each other's intermediate results (use a single
  agent with `delegate_task` batch instead).
- The whole workflow fits in one prompt easily.

## Pattern

```
  ┌─────────────────┐
  │ specialist 1    │──┐
  └─────────────────┘  │
  ┌─────────────────┐  │    ┌──────────────────┐
  │ specialist 2    │──┼───▶│ scratchpad.json  │
  └─────────────────┘  │    └────────┬─────────┘
  ┌─────────────────┐  │             │
  │ specialist 3    │──┘             ▼
  └─────────────────┘         ┌──────────────────┐
                              │ aggregator agent │
                              │ (reads + digests)│
                              └──────────────────┘
```

## Quick Start

```bash
# 1. Initialize the scratchpad (do this once per swarm)
python skills/productivity/agent_swarm/scripts/swarm_init.py morning-brief \
    --agents health-check inbox-triage git-dirty

# 2. Each specialist writes to it (cron prompt, subagent prompt, or skill):
python skills/productivity/agent_swarm/scripts/swarm_write.py morning-brief \
    health-check --payload-json '{"status": "ok", "rss_mb": 412}'

# 3. The aggregator reads and synthesizes:
python skills/productivity/agent_swarm/scripts/swarm_read.py morning-brief
```

## Wiring Examples

### Cron mode (specialists are cron jobs)

```yaml
# .hermes/cron/morning-brief-specialists.yaml
- name: morning-brief-health
  schedule: "0 7 * * *"
  script: skills/productivity/agent_swarm/scripts/swarm_write.py
  no_agent: true
  # cron would pass: <swarm_name> <agent_name> --payload-json '...'

# .hermes/cron/morning-brief-aggregator.yaml
- name: morning-brief-aggregate
  schedule: "15 7 * * *"
  no_agent: false
  prompt: |
    Read ~/.hermes/swarms/morning-brief.json and synthesize a 5-bullet
    morning brief. If any entry is missing or older than 90 minutes, note it.
```

### delegate_task sweep mode (specialists are parallel children)

```python
# In a parent agent's prompt:
for name, payload in [
    ("health", {"rss_mb": 412}),
    ("inbox",  {"unread": 7}),
    ("git",    {"dirty": 3}),
]:
    delegate_task(
        goal=f"Write your entry for the {name} swarm",
        context=f"swarm=morning-brief agent={name} payload={payload}",
        toolsets=["terminal"],
    )
# Then:
final = delegate_task(
    goal="Synthesize morning brief from swarm",
    context="Read ~/.hermes/swarms/morning-brief.json and write 5 bullets",
)
```

## Pitfalls

- **Time skew (cron mode)** — specialists should run with staggered
  `schedule` so all entries are present when the aggregator runs. Pick the
  aggregator's offset generously (e.g. 15 minutes after the earliest
  specialist).
- **Stale entries** — the aggregator should check `entries[k].ts` and warn
  if anything is older than expected.
- **Concurrent writes** — `write_entry` uses atomic temp-file-rename so
  concurrent specialists don't corrupt the scratchpad. Don't bypass it
  with raw `Path.write_text`.
- **Schema drift** — specialists evolve their payload shape over time. Add
  a `schema_version` field per entry if you find this happening.
- **One writer per agent** — each specialist writes to its OWN key in
  `entries`. Don't have multiple specialists write to the same key.