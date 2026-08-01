---
name: spec-driven-build
description: "Run an LLM-driven iterative spec-generation loop for a new build — clarify one question at a time, write self-contained HTML specs (architecture, backend, frontend, optional ux-journey), iterate through open-questions and feedback rounds, commit to a target repo or greenfield git repo, then hand off to the build agent. The deliverable is the specs themselves, not a markdown plan. Use when the user says 'spec this out', 'generate a build spec', 'write the architecture/frontend/backend docs for X', 'turn this idea into a buildable spec', 'generalize this to any new build', or any workflow where the LLM is producing *the spec* that an implementer will consume, not a plan that an LLM agent will execute. Distinct from `writing-plans` (markdown tasks for an LLM implementer) and `codebase-porting` (implementing an existing spec into a real codebase)."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [specs, llm-workflow, planning, build, documentation, self-contained-html]
    related_skills: [writing-plans, codebase-porting, one-question-at-a-time, test-what-you-built]
---

# Spec-Driven Build Workflow

Generate the *spec* (architecture.html + backend.html + frontend.html + optional
ux-journey.html) that an implementer will consume, not a markdown plan that an
LLM agent will execute. The spec IS the deliverable.

## When to Use

- User has a build idea and wants the LLM to produce the spec doc set
- User says "spec this out", "write the architecture/frontend/backend docs"
- User says "generalize this build process to any new project"
- Multi-screen UI is involved → adds the 4th spec (ux-journey)
- Greenfield or existing-repo target

**Do NOT use when:**
- The user wants an implementation plan that an LLM agent will execute → `writing-plans`
- The user has a finished spec and wants it built → `codebase-porting`
- The user wants a single design doc, not a 4-spec set → use a lighter template

## Core Principle: Scope the Workflow to the Right Repo

The most common mistake: scaffolding the spec workflow inside the agent's
home repo (Omni-Memory, hermes-agent) just because the bot plumbing lives
there. The spec workflow is **not coupled** to the agent's infrastructure —
it should live in its own folder, its own git repo. Only the Telegram bot
plumbing (if used) is shared, and only via the platform's existing bot API.

**Pre-flight check before writing any file:**

```bash
# 1. Where will the SPECS land?
#    Greenfield:  ~/<build-name>/specs/  (a fresh git repo at ~/<build-name>/)
#    Existing:    <target-repo>/specs/<build-name>/  (the project the build touches)
#
# 2. Where will the WORKFLOW live?
#    Default:     ~/build-spec/  (its own git repo, sibling to other repos)
#    Never:       inside the agent's home repo
#    Never:       inside the target build repo (pollutes the build)
#
# 3. Where will the BOT live (if Telegram UX is used)?
#    Reuse the platform's existing bot (e.g. ~/.hermes/hermes-agent/)
#    via its API, not by extending its source tree.
```

**If the user says "generalize this to any new build," that is a signal the
workflow does NOT belong in any single-project repo.** Scaffold a new
sibling repo. If unsure, ask before writing the first file.

### Mandatory confirmation checkpoint (added 2026-06-15)

The user has corrected this specific mistake in anger: *"Stop. You're
building it inside Omni Memory where I explicitly mentioned it was a
separate requirement I wanted to generalize to any new build. It should
be in its own folder."* That correction is **load-bearing**. Future
sessions must not repeat the failure.

**HIGH-INTENT phrases that mandate asking before writing the first file:**

| Phrase | Meaning | Action |
|---|---|---|
| "I want this generalized" | The workflow is meant to be reusable across many builds | Scaffold a NEW sibling repo, not the agent's home repo |
| "It should be in its own folder" | A sibling location, not inside the existing one | Ask: which folder? Confirm before mkdir |
| "This is a separate requirement" | Distinct from whatever project is being discussed | Don't piggyback on the current project — ask where |
| "Make it a public repo on [account]" | The user wants to share this as a public artifact | Sibling repo on the named account. Don't bury it |
| "Add it to [other project]" | Reuse a different existing repo | That's the target, not the current project |

**The rule:** if the user's framing contains *any* of the above phrases,
do not default. Ask one question — *where should this live?* — and wait
for an answer. The cost of one question is seconds. The cost of scaffolding
in the wrong repo and being told to start over is minutes (and trust).

**Specifically: don't reuse the agent's home repo (Omni-Memory,
hermes-agent, the spec-driven-build skill itself) just because that's
where similar plumbing already lives.** "Similar plumbing exists" is
not "this belongs there." Plumbing is reached by reference, not by
duplication.

## The Five Phases

### 1. Intake

One-line idea. Source can be `/build <idea>` in Telegram, a CLI, or pasted
in chat. The idea is the seed, nothing more.

### 2. Clarify loop

The LLM gets the user's one-liner + the design principles and returns
either:
- `"READY"` — has enough to start
- A single question

One question per turn. Never batch. The loop runs until READY. The user's
original `one-question-at-a-time` preference applies here.

**Multi-screen detection:** if the LLM is unsure whether the build has
multiple screens/tabs, ask once. If the idea clearly implies multiple
screens (mentions "tabs", "pages", "wizard", "dashboard + detail view",
"settings", "onboarding", "wizard flow", etc.), infer it and include the
4th spec. Don't ask when confident.

### 3. Write specs (one LLM call, four files out)

Single LLM call produces a JSON envelope:

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

Each HTML is **self-contained**: inline `<style>`, no external fonts, no
CDN scripts, no relative links to other files. Opens in any browser from
any path. The user may email it to someone and have it render the same way.

**No images. No mermaid. No GPT image gen.** ASCII diagrams and inline
HTML/CSS mockups. This is what makes the file actually portable.

### 4. Open-questions loop

The LLM's `open_questions` array drives this. Each question is a real
decision the LLM couldn't make from the clarifications alone.

Bot sends question 1. User answers. LLM rewrites *only the affected
sections* of *only the affected specs*. Repeat until empty or "ship it."

### 5. Feedback loop + final review

The user can:
- Click `[Approve & build]` → handoff
- Reply with feedback → enters a 3rd loop

**Feedback loop:** user provides notes (text or quoted HTML excerpts).
LLM returns diffs in plain text section-replacement format:

```
FILE: frontend.html
SECTION: Mockups
OLD: <div class="empty-state">No tasks yet</div>
NEW: <div class="empty-state">Nothing on your plate — start your first task</div>
```

Diffs applied by string replacement against stable section markers. If a
patch can't be applied (section moved, marker not found), the bot reports
which patch failed and asks for clarification. **Hard cap: 3 feedback
rounds.** After round 3, bot says: *"Three rounds in. Keep going, or
commit and start building with what we have?"*

**Final review order in Telegram:** ux-journey → frontend → architecture →
backend. Filenames in the chat sorted by this priority. Reading
top-to-bottom = reading in the order a stakeholder would.

## Storage + Handoff

### Greenfield

```
~/<build-name>/
├── .git/                       # initialized on first spec
├── specs/
│   ├── architecture.html
│   ├── backend.html
│   ├── frontend.html
│   ├── ux-journey.html         # if multi-screen
│   └── manifest.json
├── README.md                   # generated, points at specs/
└── .gitignore
```

`handoff` does `git init` if `.git` doesn't exist, commits with
`specs: <build-name> initial (arch, backend, frontend, ux-journey)`, then
spawns the build agent in that directory so the build's code lands in the
same repo as its specs.

### Existing-repo target

The build touches code in an existing repo. Specs go in
`<target-repo>/specs/<build-name>/`. After the build, test, and human
review all pass, the spec gets **appended to the target repo's main
specs index** (e.g. `specs/index.html`) — it becomes part of the project's
permanent history. Reading that file top-to-bottom = the project's
architecture history.

Detection: CLI flag `--target-repo <path>`. Without it, treat as
greenfield and use `~/<build-name>/`.

## Principles File (the Voice)

`principles.md` is **repo-committed**, versioned, injected into every LLM
call. It's the *only* file the user edits to evolve quality. Templates
evolve slower. Drafted from the `html-effectiveness` patterns — see
`references/html-effectiveness-patterns.md`.

**Drafting rules:**
- Each principle is a position, not a category
- Bad/good examples for every abstract principle
- Show-don't-describe: ASCII layouts, inline CSS mockups, code snippets
- Self-contained HTML (no external resources)
- The next person is the reader — 20 minutes on a phone

See `templates/principles.md` for a starter.

## Manifest Schema

`specs/manifest.json` is the audit log for the spec's whole life:

```json
{
  "build_name": "real-time-collab-whiteboard",
  "state": "reviewing",
  "specs": {
    "architecture": { "version": 3, "last_updated_question": "comments-format" },
    "backend":      { "version": 2 },
    "frontend":     { "version": 4 },
    "ux_journey":   { "version": 1 }
  },
  "feedback_rounds": 2,
  "open_questions_remaining": [],
  "history": [
    { "ts": "...", "event": "specs_written" },
    { "ts": "...", "event": "open_question_answered", "q": "..." },
    { "ts": "...", "event": "feedback_round", "files_changed": ["frontend.html"] },
    { "ts": "...", "event": "approved_for_build", "specs_final": ["..."] }
  ]
}
```

Append-only history. After build/test/review pass, the final entry
records the approved state. The "append to project history" feature reads
from this.

## Telegram UX (if used)

A clean example flow (concise — `one-question-at-a-time` style):

```
You:  /build a real-time collab whiteboard
Bot:  Quick question — who is the primary user in v1?
You:  design teams, 2-5 people per board
Bot:  Got it. One more — does this need to integrate with an existing tool or is it greenfield?
You:  greenfield
Bot:  Got it. Last one — must the data persist across sessions?
You:  persist
Bot:  ✅ Got it. Writing specs...
Bot:  📐 4 specs ready. I have 4 open questions before I hand them over. Q1 of 4: ...
You:  ...
Bot:  ✅ Specs updated. Final review:
      📄 <id>-ux-journey.html
      📄 <id>-frontend.html
      📄 <id>-architecture.html
      📄 <id>-backend.html
      [✅ Approve & build]
```

The bot is a separate concern (reuses the platform's existing bot — Hermes
in this case — via its API, not by extending its source). The spec
workflow does NOT modify the bot's source code.

## Pitfalls

### Scope drift: putting the workflow in the wrong repo

**Symptom:** the workflow ends up inside `~/Omni-Memory/hub/build/` or
`~/.hermes/hermes-agent/skills/` because the bot plumbing is there. **Fix:**
always scaffold in a sibling repo (`~/build-spec/`, `~/specs/`, or similar).
The bot is reached via API, not by editing its source.

### One big markdown plan instead of self-contained HTML specs

**Symptom:** the LLM produces a single mega-markdown doc with embedded
code blocks. **Fix:** the deliverables are HTML files. Each spec is its
own file, self-contained, renderable in any browser. Markdown plans are
for LLM implementers (`writing-plans`); HTML specs are for human readers.

### Adding image generation, mermaid, or syntax highlighters

**Symptom:** the LLM prompt says "include a mermaid diagram" or the
template includes `<script src="https://cdn.mermaid.in/mermaid.js">`. **Fix:**
the file must be self-contained — no CDN scripts, no external resources.
ASCII diagrams and inline CSS only. This is what makes the file portable.

### Asking 6+ clarifying questions

**Symptom:** the LLM keeps asking instead of writing. **Fix:** "95%
certainty" = every section in every template can be filled without `??`
or `[TBD]`. Anything the LLM can't fill becomes an open question in step
4, not a spec gap. If the LLM asks 8+ in a row, soft-warn: *"This is
taking a while — want me to write specs with what I have and flag the
rest as open questions?"*

### Batching open questions into one Telegram message

**Symptom:** "I have 4 open questions: Q1, Q2, Q3, Q4 — please answer all
four." User answers 1 and ignores 3. **Fix:** one question per message.
Always.

### Modifying the bot's source to add the `/build` command

**Symptom:** patching `~/.hermes/hermes-agent/.../telegram.py` to register
`/build`. **Fix:** call the bot's existing API. The bot is a platform, not
a build target.

### LLM produces specs that "look similar" but don't match the reference

**Symptom:** the LLM invents its own palette, its own typography, or
replaces the named classes (`page-head`, `sec-head`, `summary`/`.cell`)
with generic `<header>` / `<section>` / `<div>` tags. Result: every
spec looks different from every other spec, and none of them match the
`html-effectiveness` reference set. **Fix:** the LLM prompt must embed
the entire `spec-style.css` block verbatim AND forbid inventing new
class names. Point the LLM at `references/design-system.md` (the full
class inventory) and `examples/sample-spec.html` (a worked reference).
This is enforced, not suggested — the prompt says "use ONLY the class
names defined in the CSS" and "every spec MUST follow the design system
EXACTLY."

The user was clear: *"Nope that HTML files produced by this system should
have a similar design to the ones from the initial repo I shared with
you."* "Similar" is not "the same." The design system is a contract.

### Embedding images, mermaid, or external resources "to make it look like the reference"

**Symptom:** the LLM adds `<img src="...">`, `<script src="https://cdn.mermaid...">`,
or `<link rel="stylesheet" href="...">`. **Fix:** the reference set
(self-contained HTML files) deliberately has *no* images, no scripts, no
external CSS. The design system produces the visual quality through
typography, palette, and layout — not through media. Adding a `<script>`
breaks portability and contradicts principle 8. The reference set is
the model: it has no JS, and neither should the specs.

## Reference Materials

- `references/html-effectiveness-patterns.md` — Distilled patterns from the
  thariqs.github.io/html-effectiveness examples. Section structure, voice,
  show-don't-describe rules, the implementation-plan template as the
  archetype for backend/architecture specs.
- `references/design-system.md` — **The exact CSS the LLM must inline in
  every spec.** Palette (ivory/slate/clay/oat/olive), typography (serif
  display + sans body + mono labels), and the full class inventory
  (`.page-head`, `.sec-head`/`.num`, `.summary`/`.cell`, `.code`/`.kw`/`.str`,
  `.risks`/`.sev`, `.open-q`/`.q`, `.persona`, `.screen`, `.journey-step`,
  `.milestone`, etc.). The LLM is forbidden from inventing new class names.
  This is the load-bearing constraint that keeps every spec visually
  identical to the `html-effectiveness` reference set.
- `references/prompt-injection-for-spec-gen.md` — How to structure
  `principles.md` + per-type template injection so the LLM produces
  consistent voice across all four specs. Anti-patterns (instructions in
  prose vs. section templates, leakage between specs).
- `references/manifest-schema.md` — The full `manifest.json` schema with
  every state transition and field semantics. Includes the history
  event types and what each commits to.
