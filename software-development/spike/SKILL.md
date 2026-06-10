---
name: spike
description: "Throwaway experiments to validate an idea before build."
version: 1.0.0
author: Hermes Agent (adapted from gsd-build/get-shit-done)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spike, prototype, experiment, feasibility, throwaway, exploration, research, planning, mvp, proof-of-concept]
    related_skills: [sketch, writing-plans, subagent-driven-development, plan]
---

# Spike

Use this skill when the user wants to **feel out an idea** before committing to a real build — validating feasibility, comparing approaches, or surfacing unknowns that no amount of research will answer. Spikes are disposable by design. Throw them away once they've paid their debt.

Load this when the user says things like "let me try this", "I want to see if X works", "spike this out", "before I commit to Y", "quick prototype of Z", "is this even possible?", or "compare A vs B".

## When NOT to use this

- The answer is knowable from docs or reading code — just do research, don't build
- The work is production path — use `writing-plans` / `plan` instead
- The idea is already validated — jump straight to implementation

## If the user has the full GSD system installed

If `gsd-spike` shows up as a sibling skill (installed via `npx get-shit-done-cc --hermes`), prefer **`gsd-spike`** when the user wants the full GSD workflow: persistent `.planning/spikes/` state, MANIFEST tracking across sessions, Given/When/Then verdict format, and commit patterns that integrate with the rest of GSD. This skill is the lightweight standalone version for users who don't have (or don't want) the full system.

## Core method

Regardless of scale, every spike follows this loop:

```
decompose  →  research  →  build  →  verdict
   ↑__________________________________________↓
                  iterate on findings
```

### 1. Decompose

Break the user's idea into **2-5 independent feasibility questions**. Each question is one spike. Present them as a table with Given/When/Then framing:

| # | Spike | Validates (Given/When/Then) | Risk |
|---|-------|----------------------------|------|
| 001 | websocket-streaming | Given a WS connection, when LLM streams tokens, then client receives chunks < 100ms | High |
| 002a | pdf-parse-pdfjs | Given a multi-page PDF, when parsed with pdfjs, then structured text is extractable | Medium |
| 002b | pdf-parse-camelot | Given a multi-page PDF, when parsed with camelot, then structured text is extractable | Medium |

**Spike types:**
- **standard** — one approach answering one question
- **comparison** — same question, different approaches (shared number, letter suffix `a`/`b`/`c`)

**Good spike questions:** specific feasibility with observable output.
**Bad spike questions:** too broad, no observable output, or just "read the docs about X".

**Order by risk.** The spike most likely to kill the idea runs first. No point prototyping the easy parts if the hard part doesn't work.

**Skip decomposition** only if the user already knows exactly what they want to spike and says so. Then take their idea as a single spike.

### 2. Align (for multi-spike ideas)

Present the spike table. Ask: "Build all in this order, or adjust?" Let the user drop, reorder, or re-frame before you write any code.

### 3. Research (per spike, before building)

Spikes are not research-free — you research enough to pick the right approach, then you build. Per spike:

1. **Brief it.** 2-3 sentences: what this spike is, why it matters, key risk.
2. **Surface competing approaches** if there's real choice:

   | Approach | Tool/Library | Pros | Cons | Status |
   |----------|-------------|------|------|--------|
   | ... | ... | ... | ... | maintained / abandoned / beta |

3. **Pick one.** State why. If 2+ are credible, build quick variants within the spike.
4. **Skip research** for pure logic with no external dependencies.

Use Hermes tools for the research step:

- `web_search("python websocket streaming libraries 2025")` — find candidates
- `web_extract(urls=["https://websockets.readthedocs.io/..."])` — read the actual docs (returns markdown)
- `terminal("pip show websockets | grep Version")` — check what's installed in the project's venv

For libraries without docs pages, clone and read their `README.md` / `examples/` via `read_file`. Context7 MCP (if the user has it configured) is also a good source — `mcp_*_resolve-library-id` then `mcp_*_query-docs`.

### 4. Build

One directory per spike. Keep it standalone.

```
spikes/
├── 001-websocket-streaming/
│   ├── README.md
│   └── main.py
├── 002a-pdf-parse-pdfjs/
│   ├── README.md
│   └── parse.js
└── 002b-pdf-parse-camelot/
    ├── README.md
    └── parse.py
```

**Bias toward something the user can interact with.** Spikes fail when the only output is a log line that says "it works." The user wants to *feel* the spike working. Default choices, in order of preference:

1. A runnable CLI that takes input and prints observable output
2. A minimal HTML page that demonstrates the behavior
3. A small web server with one endpoint
4. A unit test that exercises the question with recognizable assertions

**Depth over speed.** Never declare "it works" after one happy-path run. Test edge cases. Follow surprising findings. The verdict is only trustworthy when the investigation was honest.

**Avoid** unless the spike specifically requires it: complex package management, build tools/bundlers, Docker, env files, config systems. Hardcode everything — it's a spike.

### Thomas's investigation standard (applies to all spikes)

When the user says "don't make shortcuts or summarize, go deep in the investigation" (or any variant — "investigate this deeply", "read everything", "document everything"), treat it as a standing instruction for any codebase investigation task. This means:

- **Read every file** in the target codebase — no early termination after "enough" files read. Complete coverage is non-negotiable.
- **Batch read** related files in parallel (7-8 at a time) to understand a subsystem as a whole before moving on.
- **Map every subsystem** before declaring the investigation complete. Surface what wasn't documented.
- Don't summarize findings mid-investigation — just keep reading. The verdict comes after full coverage.
- Report the **complete file inventory** (file count, total lines, distribution across subsystems) even if tedious.
- Preserve **specific values, exact math, exact API signatures** — not just "it does X."
- Use `execute_code` to run line-count analysis across the entire codebase to get the complete picture before reading individual files.
- Write a **full spec** from the complete read — every color hex, every animation timing, every state transition, every API mapping.
- **Check for existing forks** before building a from-scratch rewrite — an existing production-quality port may already exist and outperform a bespoke implementation (e.g. clicky-win for Clicky macOS → Windows). Factor this into the spike verdict.

This overrides the default "get the gist and move on" heuristic. Thomas's bar for "done" is exhaustive, not approximate.

**Building one spike** — a typical tool sequence:

```
terminal("mkdir -p spikes/001-websocket-streaming")
write_file("spikes/001-websocket-streaming/README.md", "# 001: websocket-streaming\n\n...")
write_file("spikes/001-websocket-streaming/main.py", "...")
terminal("cd spikes/001-websocket-streaming && python3 main.py")
# Observe output, iterate.
```

**Parallel comparison spikes (002a / 002b) — delegate.** When two approaches can run in parallel and both need real engineering (not 10-line prototypes), fan out with `delegate_task`:

```
delegate_task(tasks=[
    {"goal": "Build 002a-pdf-parse-pdfjs: ...", "toolsets": ["terminal", "file", "web"]},
    {"goal": "Build 002b-pdf-parse-camelot: ...", "toolsets": ["terminal", "file", "web"]},
])
```

Each subagent returns its own verdict; you write the head-to-head.

### 5. Verdict

Each spike's `README.md` closes with:

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

### What worked
- ...

### What didn't
- ...

### Surprises
- ...

### Recommendation for the real build
- ...
```

**VALIDATED** = the core question was answered yes, with evidence.
**PARTIAL** = it works under constraints X, Y, Z — document them.
**INVALIDATED** = doesn't work, for this reason. This is a successful spike.

## Comparison spikes

When two approaches answer the same question (002a / 002b), build them **back to back**, then do a head-to-head comparison at the end:

```markdown
## Head-to-head: pdfjs vs camelot

| Dimension | pdfjs (002a) | camelot (002b) |
|-----------|--------------|----------------|
| Extraction quality | 9/10 structured | 7/10 table-only |
| Setup complexity | npm install, 1 line | pip + ghostscript |
| Perf on 100-page PDF | 3s | 18s |
| Handles rotated text | no | yes |

**Winner:** pdfjs for our use case. Camelot if we need table-first extraction later.
```

## Frontier mode (picking what to spike next)

If spikes already exist and the user says "what should I spike next?", walk the existing directories and look for:

- **Integration risks** — two validated spikes that touch the same resource but were tested independently
- **Data handoffs** — spike A's output was assumed compatible with spike B's input; never proven
- **Gaps in the vision** — capabilities assumed but unproven
- **Alternative approaches** — different angles for PARTIAL or INVALIDATED spikes

Propose 2-4 candidates as Given/When/Then. Let the user pick.

## Output

- Create `spikes/` (or `.planning/spikes/` if the user is using GSD conventions) in the repo root
- One dir per spike: `NNN-descriptive-name/`
- `README.md` per spike captures question, approach, results, verdict
- Keep the code throwaway — a spike that takes 2 days to "clean up for production" was a bad spike

## Template reference

For Three.js interactive graph spikes: `references/threejs-graph-spike-template.md` — covers Python data extraction, force-directed layout, individual Mesh rendering, embedded JSON gotchas, and verification checklist.

For deep codebase investigation (e.g. Clicky reverse-engineering): `references/clicky-investigation.md` — complete file inventory, exact technical values (VAD, bezier arc math, state machine states), [POINT] coordinate format and regex, design tokens, locked Windows port decisions. Loaded when user says "go deep", "document everything", or "1:1 rewrite" — preserves investigation output so future sessions don't re-read every file.

### Pitfall: Check for Existing Ports Before Rewriting from Scratch

Before building a cross-platform rewrite of any significant application, check for existing production-quality ports first. A from-scratch rewrite of a 7,637-line macOS app produced a 3,555-line WPF port with critical gaps — while a pre-existing clicky-win (PySide6, 3,810 lines) was significantly more complete and production-ready.

**The pattern:**
1. User wants "1:1 rewrite of X for platform Y"
2. Agent starts from scratch without checking if a port already exists
3. Result: inferior to existing port in completeness, structure, and polish

**When this applies:** Any time the user says "rewrite for Windows", "port to X", "make work on Y", or asks to replicate another platform's app. The spike investigation step should always include a brief check for existing ports on the target platform before committing to from-scratch implementation.

**Why this matters:** Existing ports benefit from months of real-user bug reports, production hardening, and iteration. A fresh rewrite starts at zero. For example, a PySide6 clicky-win already had full CompanionManager, proper hotkey detection, streaming transcription, SSE parsing, waveform visualization, fly-to animation, multi-monitor support, and a test suite — none of which were complete in the WPF rewrite after 20 minutes of subagent time.

## Pitfalls (Three.js graph spikes)

**Canvas sizing — clientWidth/clientHeight are 0 if only CSS sets size**
THREE.js reads canvas pixel dimensions at renderer init. If size is set purely via CSS (`width: 100%; height: 100vh`), the renderer creates a 0×0 WebGL context. Fix: set explicit `canvas.width` and `canvas.height` pixel values before `new THREE.WebGLRenderer({ canvas })`.

**MeshLambertMaterial vs MeshStandardMaterial for colored nodes**
`MeshStandardMaterial` requires full PBR lighting to display colors correctly. Use `MeshLambertMaterial` (pure diffuse) for graph nodes under ambient + directional light — colors show immediately without tuning.

**InstancedMesh + instanceColor silently fails in r160**
Setting `instanceColor` on an InstancedMesh often renders no visible color even when the buffer format is correct, because the default material doesn't have vertex colors enabled. For N < 2000: use individual `THREE.Mesh` objects (one per node). For N > 5000: use InstancedMesh with uniform color + size variation.

**frustumCulled = false**
Three.js culls objects outside the camera frustum by default. Sphere nodes at graph edges can disappear unexpectedly during orbit. Set `mesh.frustumCulled = false` on all node meshes.

**Headless Chromium WebGL**
On Linux, headless Chromium uses SwiftShader (software WebGL). Features like `InstancedMesh.instanceColor` may render differently than in real Chrome. Test with `--enable-unsafe-swiftshader` and verify output in headed mode.

## Attribution

Adapted from the GSD (Get Shit Done) project's `/gsd-spike` workflow — MIT © 2025 Lex Christopherson ([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). The full GSD system offers persistent spike state, MANIFEST tracking, and integration with a broader spec-driven development pipeline; install with `npx get-shit-done-cc --hermes --global`.
