# HTML-Effectiveness Pattern (LLM-generated spec / report / doc artifacts)

## What this is

A reference for any pipeline that has an LLM generate a structured HTML
artifact — design specs, build plans, status reports, incident reports,
research briefings, etc. — and ship it through a Telegram (or any
chat-platform) approval flow. The thariqs/html-effectiveness catalog
(20 example HTMLs) is the canonical pattern library. The
implementation-plan example (`16-implementation-plan.html`) is the
closest template for *spec-style* output (architecture / backend /
frontend).

Source: https://thariqs.github.io/html-effectiveness/ — fetch the 20
linked `.html` files into `/tmp/` and `grep -E '<h[1-3]'` each one to
read the section shape.

## The class-level lesson

**When the user gives you a single reference URL (a "catalog page,"
"examples page," "this is the style I want"), fetch the linked examples
and read their structure before designing.** Don't just read the
overview. The overview is marketing; the examples are the pattern.

For thariqs specifically: the page is sluggish, so parallelize with
background `&` curls (one per example), wait ~12s, then classify by
`grep -E '<h[1-3]'`. Each example is ~10–28 KB. Total payload ~350 KB.
Fits comfortably in working memory after one summarization pass.

## The "implementation-plan" template (anchor for any spec-style output)

This is the template that maps 1:1 onto "design doc, build plan,
architecture spec." Study `16-implementation-plan.html` for the shape:

```
Title strip:  "<Doc type> · <Project / Surface>"
Prompt:       The original ask, preserved verbatim
Effort:       Single line of metadata ("~2 weeks", "$0.25/build", etc.)
01 Section 1 — the first decision the reader must make
02 Section 2 — the next decision, etc.
...
Risks & mitigations
Open questions
```

**Sections are decisions, not headings.** Numbering implies a reading
order; the user skims from 01 downward and the most load-bearing
information (data flow, key code, mockups) is in the middle.

## What the HTML *is* and *isn't*

**IS:**
- Real, semantic HTML + CSS (no JS, no build step)
- Inline diagrams drawn as ASCII (data flow) or HTML/CSS (mockups)
- Inline code blocks with real syntax (no syntax highlighter — just `<pre><code>`)
- Inline mockups that look like product screenshots (built from `<div>`s, not images)
- Inline tables for component matrices, schema, decision logs

**ISN'T:**
- A container for AI-generated *images*. Almost never needs images.
- A page that requires JavaScript. The user might be reading in an email
  preview, on a phone, in a printout.
- A page that requires external assets. One file, all inline, opens
  anywhere.

**This collapses the image-gen, mermaid-render, syntax-highlight, and
chart subsystems.** One LLM call → one HTML file. That's it.

## The 3-spec structure (architecture / backend / frontend)

For multi-faceted builds, **generate all three specs in a single LLM
call** with three clearly delimited sections. Sequential is overkill
at this size and the consistency gain between the three sections
matters more than latency.

```
specs/<build_id>/
├── architecture.html    # System context, components, data flow, deployment, trust boundaries
├── backend.html         # Schema, API contract, milestones, data flow, key code, risks
├── frontend.html        # Surfaces, components, mockups, state, a11y, key code, risks
└── manifest.json        # { id, idea, status, costs, created_at, file_hashes }
```

No subdirectories, no `images/`, no `notes.md`. The HTML files are the
documentation. `manifest.json` is the bookkeeping (matches the
`skills/registry.json` pattern in the Omni-Memory hub).

## Per-spec content (sections that ship in every spec)

| Section | Always present | Why |
|---|---|---|
| Title strip | yes | `<Doc type> · <Build name>` — gives the doc identity at a glance |
| Prompt | yes | Preserves the original ask; lets the reader audit scope |
| Effort / size | yes | One line, easy to skip if not relevant |
| Milestones (week-by-week) | backend, frontend | "Ship in N slices, each behind the flag" — see `#16` |
| Data flow | all | ASCII diagram with solid/dashed legend (sync vs. async) |
| Schema / API contract | backend, architecture | Real SQL, real type signatures — not pseudo-code |
| Mockups | frontend | Built from `<div>`s; not pixel-final, but shows nesting/placement |
| Component matrix | architecture, frontend | Table: name / responsibility / interface / owns |
| State model | frontend | What lives where, optimistic vs server-of-truth |
| Key code | all | The snippets most likely to be done wrong (per `#16`) |
| Risks & mitigations | all | Table or list, explicit |
| Open questions | all | Flagged for the user; drives the next conversation |

## Design principles as prompt injection

Keep a single `principles.md` (or per-doc-type file) that gets injected
into the LLM call. The principles inform *section content* — they're
the criteria for the Risks and Decisions sections, not a style guide
for image generation.

Three principle sets, one per doc type:

- **architecture**: trust boundaries explicit, observability-first,
  deployable to one box, no shared mutable state, explicit contracts
- **backend**: idempotent ops, schema-validated inputs, timeouts on
  every external call, errors carry remediation hints
- **frontend**: design tokens not hardcoded values, keyboard
  navigable, optimistic UI, screen-reader tested

**Inject, don't hardcode.** Repo-committed `principles.md` is
versioned and reviewable. The LLM cites the principle in each design
decision: *"We chose X because principle Y"* — makes the spec
auditable.

## Image gen (optional, post-approval only)

Keep image generation as a *secondary polish* path, not a build-blocker:

- User approves the 3 HTML specs in Telegram
- Bot writes them to `specs/<id>/`
- A separate command (`/build/render <id>`) takes each spec's
  "Open questions" or "Hero diagram" placeholders and asks GPT to draw
  1–3 images, swapping them in as `<img>` tags
- Costs ~$0.10/build, opt-in, **never blocks the spec from being usable**

**Why opt-in:** the implementation-plan template has zero images and
reads fine. Most specs don't need them. Don't add cost and latency
for the common case.

## Telegram integration (the user-facing surface)

The existing `telegram-bot-implementation` skill covers the full
inline-keyboard / callback / strip-keyboard plumbing. The build-pipeline
extension is just:

1. A new `build_proposals` table in the same `proposals.db`
2. A new `build:approve:<id>` / `build:modify:<id>` / `build:dismiss:<id>`
   callback namespace (same `bot.on("callback_query", ...)` handler)
3. The 3 HTML files sent as **document attachments** (Telegram shows
   the `<title>` text as the doc name; user opens in browser)
4. The inline Approve / Modify / Dismiss buttons — same as skill
   approval, same `stripKeyboard` flow

**Reuse everything.** The bot, the registry, the polling loop, the
MarkdownV2 escaping fixes, the `assertKeyboardValid`, the chat-id
resolution hierarchy — none of it changes. This is the lesson of the
Omni-Memory hub: every new artifact type is one new DB table + one new
callback namespace. The plumbing is already there.

## Worked session reference

The Omni-Memory build-pipeline design session (2026-06-15) produced:
- 3-spec structure (architecture / backend / frontend)
- `principles.md` injection
- Image gen as opt-in post-approval layer
- Telegram document-attachment send with inline-keyboard approval

The implementation-plan template (`16-implementation-plan.html`) was
the anchor that pivoted the design from "container for AI images" to
"self-contained single-file HTML with inline diagrams." The pivot
collapsed a ~6-component pipeline (image gen, mermaid render, syntax
highlighter, chart gen, mockup render, file composer) down to a
single LLM call → single HTML file out.

## Verification recipe

After the pipeline is built:

1. Seed one real `build_proposal` row in the DB
2. Start the bot with the real token + chat id
3. Confirm `[bot] Sent proposal: <title> (msg_id=N)` in the log
4. Open the 3 HTML files (sent as documents) in a browser — verify
   the inline diagrams render, the code blocks have real syntax, the
   mockups look like product screenshots
5. Click ✅ in Telegram — confirm DB row → `approved`, files written
   to `specs/<id>/`, `manifest.json` present
6. Click 🖼️ Render images (opt-in) — confirm images appear inline in
   the spec files
7. `node --check hub/build/pipeline.mjs` — confirm syntax
8. `rg "Proposals_PATH|PROPOSALS_PATH" hub/` — confirm consistent naming
   (one form, no camelCase mix)

If any step fails, the failure is in *that* step, not in the bot
plumbing. The bot has been verified end-to-end in prior sessions
(see `references/omni-memory-hub-2026-06-15.md`).
