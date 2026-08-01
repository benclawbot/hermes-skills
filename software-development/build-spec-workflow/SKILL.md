---
name: build-spec-workflow
description: "End-to-end build workflow that pairs with an external specification — produce the spec set (architecture/backend/frontend/optional ux-journey HTML docs) and then implement it into a real codebase. Replaces the two formerly separate skills (spec-driven-build + codebase-porting) — they were two halves of the same flow ('turn this idea into a buildable spec' then 'implement that spec into code'), and the location-confirmation pitfall + path-collision pre-check are shared concerns. Use when the user says 'spec this out', 'write the architecture/frontend/backend docs for X', 'implement this spec', 'build this specification', 'port X to Y', 'rewrite X for Windows', 'generalize this to any new build', 'put it in its own folder', 'follow this build contract', or any other workflow where there is (or should be) a written buildable spec before implementation begins."
version: 1.0.0
author: Hermes Agent (consolidated from spec-driven-build + codebase-porting)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [specs, llm-workflow, planning, build, documentation, self-contained-html, porting, implementation, integration]
    related_skills: [plan-and-execute-workflow, one-question-at-a-time, test-what-you-built, oss-pattern-mining]
---

# Build-Spec Workflow

The end-to-end flow when a build needs (a) a written spec and (b) someone to
implement that spec into code. Two halves:

```
generate spec (spec-driven-build)
   │
   │  outputs: architecture.html + backend.html + frontend.html
   │           + optional ux-journey.html + manifest.json
   │
   ▼
implement into codebase (codebase-porting)
   │
   │  inputs: the spec files
   │  outputs: code in target repo, with deviations documented,
   │           acceptance checklist verified
   │
   ▼
verify + ship
```

When to use:
- User has a build idea and wants the LLM to produce the spec doc set
- User says "implement this spec" / "follow this build contract" / "port X to Y"
- Multi-screen UI is involved → adds the 4th spec (ux-journey)
- Greenfield or existing-repo target

When NOT to use:
- Plan-then-execute on a multi-step refactor → `plan-and-execute-workflow`
- Pure pattern extraction from existing OSS → `oss-pattern-mining`
- Ad-hoc small change → just do it

---

## SUBSECTION A: spec-driven-build (formerly standalone)

> Generate the *spec* (architecture.html + backend.html + frontend.html + optional ux-journey.html) that an implementer will consume, not a markdown plan that an LLM agent will execute. The spec IS the deliverable.

### Core Principle: Scope the Workflow to the Right Repo

The most common mistake: scaffolding the spec workflow inside the agent's home repo just because the bot plumbing lives there. The spec workflow is **not coupled** to the agent's infrastructure — it should live in its own folder, its own git repo.

**Pre-flight check before writing any file:**

```bash
# Where will the SPECS land?
#   Greenfield:  ~/<build-name>/specs/  (fresh git repo at ~/<build-name>/)
#   Existing:    <target-repo>/specs/<build-name>/
#
# Where will the WORKFLOW live?
#   Default:     ~/build-spec/  (its own git repo)
#   Never:       inside the agent's home repo
#   Never:       inside the target build repo (pollutes the build)
```

### Mandatory confirmation checkpoint

The user has corrected this mistake: *"Stop. You're building it inside Omni Memory where I explicitly mentioned it was a separate requirement I wanted to generalize to any new build. It should be in its own folder."*

**HIGH-INTENT phrases that mandate asking before writing the first file:**

| Phrase | Meaning | Action |
|---|---|---|
| "I want this generalized" | Workflow is meant to be reusable | Scaffold NEW sibling repo |
| "It should be in its own folder" | Sibling location | Ask: which folder? |
| "This is a separate requirement" | Distinct from current project | Don't piggyback |
| "Make it a public repo on [account]" | Public artifact | Sibling repo on named account |
| "Add it to [other project]" | Reuse a different existing repo | That's the target |

**Rule:** if framing contains ANY of the above, do not default. Ask one question — *where should this live?* — and wait.

### The Five Phases

**Phase 1 — Intake.** One-line idea. Source can be `/build <idea>` in Telegram, CLI, or chat.

**Phase 2 — Clarify loop.** LLM gets the user's one-liner + design principles, returns either `"READY"` or a single question. One question per turn. Multi-screen detection: infer if the idea clearly implies multiple screens.

**Phase 3 — Write specs (one LLM call, four files out).**

```json
{
  "architecture": "<full self-contained HTML>",
  "backend":      "<full self-contained HTML>",
  "frontend":     "<full self-contained HTML>",
  "ux_journey":   "<full self-contained HTML or null>",
  "open_questions": ["...", "..."],
  "manifest": { "version": 1, "state": "reviewing" }
}
```

Each HTML is **self-contained**: inline `<style>`, no external fonts, no CDN scripts, no relative links to other files. **No images. No mermaid. No GPT image gen.** ASCII diagrams and inline HTML/CSS mockups. This is what makes the file actually portable.

**Phase 4 — Open-questions loop.** Each `open_questions` entry is a real decision. Bot sends question 1. User answers. LLM rewrites *only affected sections* of *only affected specs*. Repeat until empty or "ship it."

**Phase 5 — Feedback loop + final review.**

User can:
- Click `[Approve & build]` → handoff to SUBSECTION B
- Reply with feedback → enters a 3rd loop

**Feedback loop:** user provides notes. LLM returns diffs in plain text section-replacement format:

```
FILE: frontend.html
SECTION: Mockups
OLD: <div class="empty-state">No tasks yet</div>
NEW: <div class="empty-state">Nothing on your plate — start your first task</div>
```

Diffs applied by string replacement against stable section markers. **Hard cap: 3 feedback rounds.** After round 3, bot says: *"Three rounds in. Keep going, or commit and start building with what we have?"*

**Final review order in Telegram:** ux-journey → frontend → architecture → backend.

### Storage + Handoff

**Greenfield:**
```
~/<build-name>/
├── .git/
├── specs/
│   ├── architecture.html
│   ├── backend.html
│   ├── frontend.html
│   ├── ux-journey.html
│   └── manifest.json
├── README.md
└── .gitignore
```

**Existing-repo target:** Specs go in `<target-repo>/specs/<build-name>/`. After build/test/review pass, the spec gets **appended to the target repo's main specs index**.

### Principles File (the Voice)

`principles.md` is **repo-committed**, versioned, injected into every LLM call. It's the *only* file the user edits to evolve quality. Templates evolve slower. Drafted from the html-effectiveness patterns — see `references/spec-driven-build--html-effectiveness-patterns.md`.

**Drafting rules:**
- Each principle is a position, not a category
- Bad/good examples for every abstract principle
- Show-don't-describe: ASCII layouts, inline CSS mockups, code snippets
- Self-contained HTML (no external resources)
- The next person is the reader — 20 minutes on a phone

### Manifest Schema
`specs/manifest.json` is the audit log for the spec's whole life. See `references/spec-driven-build--manifest-schema.md`.

### Design system

The exact CSS the LLM must inline in every spec is in `references/spec-driven-build--design-system.md`. Palette (ivory/slate/clay/oat/olive), typography (serif display + sans body + mono labels), and the full class inventory (`.page-head`, `.sec-head`/`.num`, `.summary`/`.cell`, `.code`/`.kw`/`.str`, `.risks`/`.sev`, `.open-q`/`.q`, `.persona`, `.screen`, `.journey-step`, `.milestone`, etc.). The LLM is forbidden from inventing new class names. This is the load-bearing constraint that keeps every spec visually identical to the html-effectiveness reference set.

### Pitfalls (from spec-driven-build)

- **Scope drift: putting the workflow in the wrong repo** — always scaffold in a sibling repo
- **One big markdown plan instead of self-contained HTML specs** — deliverables are HTML files
- **Adding image generation, mermaid, or syntax highlighters** — keeps file portable
- **Asking 6+ clarifying questions** — write specs with what you have and flag the rest as open
- **Batching open questions into one Telegram message** — one question per message. Always.
- **Modifying the bot's source to add the `/build` command** — call the bot's existing API
- **LLM produces specs that "look similar" but don't match the reference** — design system contract is enforced, not suggested

---

## SUBSECTION B: codebase-porting (formerly standalone)

> Implement external specifications (build-ready specs, porting plans, or integration plans) into an existing real codebase, or port a codebase from one platform/framework to another.

### Location-Confirmation Checkpoint (FIRST thing, before reading code)

Same principle as SUBSECTION A. **When the user asks you to build / port / generalize something, the first question is "where does this live?"**

| Phrase | What it means | Where it should NOT go |
|---|---|---|
| "I want this generalized" | Workflow reusable across many builds | Inside any single project repo |
| "It should be in its own folder" | Sibling location | Inside the existing repo |
| "This is a separate requirement" | Distinct from current project | Piggybacked |
| "Make it a public repo on [account]" | User wants to share | Buried in private repo |
| "Generalize this to any new build" | Decoupling | Anywhere coupled |
| "Add it to [other project]" | Reuse a different repo | The current project |

**Rule:** if framing contains any of the above, ask one question — *where should this live?* — and wait.

### Design-Only Refactor Confirmation (the "use this design" trap)

A variant that looks like the location-confirmation case but is its own failure mode: the user uploads a mockup or screenshot and says "use this exact design" without naming a target repo. Three sub-questions before writing any file:

1. **Which repo is the target?** If the conversation was in project A and the user said "use this design" without naming a project, *ask*.
2. **Logic or only visuals?** "Use this design" is ambiguous. State the assumption in one sentence ("I'll keep all the handlers/state/AI calls untouched and only swap the visual layer — tell me if you want logic changes too") and wait for the green light.
3. **Which components get the new skin?** Default to applying the visual rules (palette, radius, shadow, typography) to the whole UI, not just the screen the user showed. Then call that out so the user can scope it down.

**Real incident (2026-06-25, MeetingMind design → wrong project):** The user uploaded a Stripe-style "MeetingMind" mockup. The active project was MindDrop. Applied the design to `MeetingStudio.tsx` in MindDrop. User replied "stop!!!!! revert all the changes as they are not being applied to the right project. it needs to be applied to the video meeting minutes manager, not minddrop."

### Core Principle: Investigate Deeply Before Writing Anything

When the user says "Don't make shortcuts or summarize, go deep in the investigation", read every source file, understand the full subsystem map, build a complete picture BEFORE writing any spec or making architectural decisions.

1. Read ALL source files completely — not just "key" files
2. Map every subsystem: state machines, animation math, API calls, design tokens, analytics events, permission system, IPC protocol
3. Write the spec AFTER the investigation, not during
4. Lock major decisions (language, framework, service choices) at the top of the spec before writing anything else

### Path-Collision Pre-Check (CRITICAL — do this BEFORE any mkdir or write_file)

**When a spec specifies literal package paths, the path may already exist as a tracked FILE in the repo.** A naive `mkdir <spec_path>` silently destroys the file.

```bash
# 1. Does ANY directory match the spec name? (case-insensitive)
find ~ -maxdepth 5 -type d -iname "<spec-folder-name>" 2>/dev/null

# 2. For each candidate, is the git remote consistent with the spec's repo?
cd <candidate> && git remote -v && git log --oneline -3
# If the remote doesn't match the spec, REFUSE TO WRITE. Ask the user which one is correct.

# 3. Does the path exist as a file?
stat <spec_path> 2>&1 | head -3

# 4. Is it tracked in git?
git ls-files <spec_path>

# 5. Are there same-name siblings?
ls -la $(dirname <spec_path>) | grep -E "^-" | awk '{print $9}' | grep -E "^<name>$"
```

**Decision tree:**
- Multiple candidates by name (case-insensitive) → **case-mismatch trap**. Verify via git remote.
- `stat` shows a file at parent path AND `git ls-files` confirms tracked → **path collides**. Either pick non-colliding location (most common), ask, or `git checkout HEAD -- <file>`.
- `stat` shows a directory → safe to `mkdir` inside
- Path doesn't exist → safe to `mkdir -p`

**Real incident (2026-06-24, MindDrop auth bypass):** Spec referenced `benclawbot/MindDrop2-Opencode`. Local `find -iname` found `MindDrop2-Opencode/` AND `minddrop2-opencode/` (lowercase, git remote was `obsidian-vault-backup`). A naive `cd` to the lowercase match would have clobbered a vault backup. Both behaviors (case-sensitive search OR case-insensitive without verification) are wrong. Correct: case-insensitive discovery + git-remote verification on every candidate.

**Why `mkdir -p` doesn't fail:** it treats the leaf as a new directory and creates the path tree. If a file already exists at the leaf, behavior depends on the shell — `bash` will refuse (good) but the failure happens after the file may have been replaced by the empty directory in some flows. Always run the pre-check.

### Project-Rename Touchpoint Sweep

A rename is a rename of a *system*, not a directory. The folder is one touchpoint out of a dozen. Missing any of them produces a broken state that looks healthy for days — a cron job with a stale `workdir`, a test that hardcodes the old path, a memory entry that references the old location, a skill doc that points at a non-existent path.

**Phase 1 — GitHub + filesystem:**
```bash
gh repo rename "<old>" --destination "<new>" -R <owner>/<old> --yes
cd ~ && mv <old-dir> <new-dir>
cd <new-dir> && git remote set-url origin https://github.com/<owner>/<new>.git
```

**Phase 2 — inside the repo (`git grep` finds these):**
- README, docs, docstrings
- Hardcoded absolute paths in tests, scripts, source

**Phase 3 — outside the repo (cron + memory + skills):**
- Cron jobs with workdir/prompt pointing at the old dir
- Cron shell scripts (the .sh wrappers that no_agent jobs exec)
- Agent memory entries
- Hub-installed + agent-created skills (live-path pointers in SKILL.md / references/)

**Phase 4 — cleanup:** Run the test suite; trigger each updated cron; verify the live path pointers resolve; check for orphan scripts.

### Build-Ready Spec Implementation Workflow

When the user hands you a build-ready spec and says "implement that":

1. **Read the spec once end-to-end.** Note every literal path, every file, every schema field.
2. **Map spec paths to reality.** For each `path/to/file.py` in the spec, run the path-collision pre-check. Build a "spec-vs-reality" delta before touching anything.
3. **Identify integration points.** Where does the new code hook into the existing repo? Read 1-2 representative files at each integration point.
4. **Follow the spec's build order.** Build-ready specs have a numbered build order. Follow it.
5. **Document deviations in the package itself.** When a spec says `hermes/task_contract/` and you place it at `hermes_cli/task_contract/`, the deviation is part of the deliverable. Add a one-paragraph note in `__init__.py` and the developer guide.
6. **Acceptance-driven validation.** Build-ready specs end with an acceptance checklist. Run every item.
7. **Run the existing test suite, not just the new one.** A new package that breaks unrelated tests has not actually shipped.

### Platform API Mapping (porting case)

For each macOS API, find the direct Windows equivalent:

| macOS | Windows |
|---|---|
| AXUIElement (window positioning) | Win32 SetWindowPos |
| ScreenCaptureKit | mss + PIL |
| CGEvent tap (global hotkey) | SetWindowsHookEx |
| NSStatusItem (menu bar) | NotifyIcon / System Tray |
| AVFoundation audio | NAudio / Windows Audio API |
| Apple Speech framework | Piper TTS + Windows Speech API |

### Direct Patching Over Delegation for Multi-File Changes

For complex porting tasks involving many files:
- DO NOT delegate to a subagent for the entire port. Subagents timeout on long-running tasks.
- DO make targeted patches file-by-file yourself when changes are well-understood.
- Delegation is appropriate for: research synthesis, parallel exploration of unknown systems. Not for: applying known patterns across a codebase.

### Extending an Existing Implementation (spec is v2, not v1)

When the user already shipped v1 and now hands you a v2 spec that **adds** modules, the move is **extension-in-place**:

1. **Inventory what's already there.** Run a gap analysis.
2. **Map the new spec's modules onto the existing tree.**
3. **Extend the schema additively.** New Pydantic models, new Optional fields. Never change existing field types or defaults.
4. **Extend the config additively.** New sections with their own `enabled: bool` field.
5. **Wire new modules in `integration.py`.** Wrap each new call in `try/except`.
6. **Run the existing test suite after every new module.** Don't batch.
7. **End with: existing tests + new tests + end-to-end smoke + disabled-mode smoke.**

### Disabled-by-Default Optimization Packs

When a spec lists "optimization packs" or "optional modules" with some disabled by default:
- Each pack gets a section with its own `enabled: bool` field
- Pack-specific default is encoded in the Pydantic model: `enabled: bool = False` for disabled, `enabled: bool = True` for enabled
- Integration layer checks `config.x.enabled` before each call, wraps in `try/except`
- Tests for disabled-by-default packs assert the disabled path returns default unchanged

### README-Driven Install Implementation

When the README is the spec:
- Phase 0: Confirm README is fetchable and canonical
- Phase 1: Audit README against actual tree. Produce gap table.
- Phase 2: Verify with REAL synthetic data, not just "the script exits 0"
- Phase 3: Ship the install path the user actually asked for
- Phase 4: Update README in the same commit
- Phase 5: Commit + push. Verify push landed.

### Asking design questions mid-implementation

When you need user input during a long implementation, reach for `clarify`. **Schema constraint:** `List[str]`, not `List[dict]`. Gateway does `str(c).strip()` on each choice, so dicts render as literal `{'value': '...'}`.

**Match question shape to expected response:**

| If short answer (yes/no, "2", "build the gated version") | If longer answer / discussion | If constrain to N options |
|---|---|---|
| Omit `choices` entirely → open-ended clarify | Omit `choices` entirely → open-ended clarify | Provide `choices=[A, B, C, D]` AND mention button-tap gotcha |

### Tool-budget pivot (don't stop at the iteration wall)

A long extension task can hit the per-session tool-call ceiling. The wrong move is "iteration limit reached, here's a partial summary." The right moves:

1. Use `execute_code` to loop locally — one `execute_code` call can drive 50 tool calls inside one session
2. Use `delegate_task` to parallelize independent workstreams
3. Document what's left, only as a last resort

### Always-On Default Packs (regression-locked defaults)

When the user says "enable those 3" and the right interpretation is "make it non-negotiable," the move is **lock the default, don't override the toggle**. Three places get updated:
1. The default config YAML (with comment block listing always-on vs opt-in)
2. A regression test that asserts each always-on pack's `enabled` field is `True`
3. The user guide splits the pack table into "Always-on (cannot be disabled)" and "Opt-in (can be turned off)"

**What NOT to do:** silently override `enabled: false` in user config at runtime. That's hostile — fights the user. The "always-on" guarantee is the *default*, not a runtime override.

---

## Pitfalls (shared between both halves)

These appear in both spec-generation and spec-implementation; treat them as class-level for the whole build-spec workflow:

- **Approximating instead of mapping**: "close enough" in the spec becomes wrong code
- **Starting from spec without investigating**: Writing spec before reading all source files means missing subsystem details
- **Forgetting the permission system**: macOS has accessibility + screen recording permissions. Windows has equivalent but different names/flows
- **Spec path ≠ reality path** — the single most expensive mistake in spec-implementation work
- **`mkdir -p` lies about file collisions** — run the pre-check
- **`git status` lies when `core.fileMode` is unset** — set `git config core.fileMode false` before any perms audit
- **The "two script versions + README only documents one" trap** — carry dead scripts, or update
- **Install scripts that block on no-TTY** — gate `read` calls behind an INTERACTIVE check; put `--max-time 5` on every network call
- **Local `git clone` made before `gh auth login` has no git creds wired** — `gh auth setup-git` fixes it
- **`nohup` + `&` + `> /tmp/x.log` inside foreground `terminal()` is rejected** — Hermes tracks background processes via `background=true`
- **LSP errors inside `/* ... */` blocks ≠ `tsc` errors** — verify with `git stash` → re-run typecheck → compare counts
- **A half-installed `node_modules` produces phantom typecheck errors** — `rm -rf node_modules package-lock.json && npm install`
- **The "two-step plan + README" trap** — the README is often the de facto spec; treat it as such

---

## Companion references (in `references/`)

From spec-driven-build:
- `spec-driven-build--html-effectiveness-patterns.md` — distilled patterns from thariqs/html-effectiveness
- `spec-driven-build--design-system.md` — exact CSS the LLM must inline in every spec
- `spec-driven-build--manifest-schema.md` — full manifest.json schema, every state transition
- `spec-driven-build--prompt-injection-for-spec-gen.md` — how to structure principles.md + per-type template injection

From codebase-porting:
- `codebase-porting--clicky-macos-to-windows.md` — full Clicky port: 25-file inventory, subsystem math, locked decisions
- `codebase-porting--spec-implementation-playbook.md` — investigation order, spec-vs-reality delta construction, deviation logging
- `codebase-porting--extending-existing-implementation.md` — v1 → v2 extension workflow, additive schema changes, regression-net testing
- `codebase-porting--readme-driven-install.md` — README-as-spec workflow, audit table, real-data verification
- `codebase-porting--vendor-swap-in-spa.md` — switching from X to Y for AI provider / auth / storage in deployed frontend
- `codebase-porting--design-only-rewrite.md` — when user shows a mockup and says "use this design" against an existing app

## Companion templates (in `templates/`)

From spec-driven-build:
- `spec-architecture.md` — starter for the architecture spec
- `spec-backend.md` — starter for the backend spec
- `spec-frontend.md` — starter for the frontend spec
- `spec-principles.md` — starter for principles.md (the voice)
- `spec-ux-journey.md` — starter for the optional ux-journey spec

From codebase-porting:
- `install-script.sh` — install script template with noninteractive + max-time patterns

## Companion scripts (in `scripts/`)

From codebase-porting:
- `verify-pipeline.py` — synthetic-data-driven pipeline verification (matches the README-driven-install pattern)

## Related skills

- `plan-and-execute-workflow` — for multi-step implementation work, this is the execution side; build-spec-workflow is the spec+implement side
- `one-question-at-a-time` — for spec-handoff discovery flow (open questions in plans/specs)
- `test-what-you-built` — for verifying the build actually works after implementation
- `oss-pattern-mining` — for extracting patterns from existing OSS repos before starting a new build