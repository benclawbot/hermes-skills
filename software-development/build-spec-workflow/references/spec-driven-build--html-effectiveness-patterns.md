# HTML-Effectiveness Patterns

Distilled from `https://thariqs.github.io/html-effectiveness/` — a
catalog of 20 self-contained HTML deliverables that LLMs produce better
than any other medium. The patterns below are the load-bearing ones for
spec generation; the page is the canonical reference.

## The 20 examples, grouped by what they teach

| # | Title | Pattern we steal |
|---|---|---|
| 01 | Three ways to implement debounced search | Multiple-approach comparison, inline code, decision matrix |
| 02 | Four visual directions for the empty state | Inline CSS mockups, no images |
| 04 | How authentication flows through the codebase | Surface-level code walkthrough, real file paths |
| 05 | Acme design system | Design tokens as CSS variables, swatches in HTML |
| 06 | Card variant matrix | Component variants as a single page |
| 07 | Task completed micro-interaction | Interaction as code, not video |
| 08 | Sidebar drag-to-reorder | Interaction as code, real DOM |
| 10 | Background jobs — header illustrations | One-off SVG header, but we skip images per principle 8 |
| 12 | Incident report | Failure-first, timeline, mitigation |
| 13 | Deploy pipeline — annotated flowchart | ASCII flowchart with annotations |
| **16** | **Implementation plan for comment threads** | **The archetype for backend.html. Closest to what we produce.** |
| 15 | Consistent hashing — interactive explainer | Concept explainer with interactive DOM |
| 18 | Cycle 14 triage | Triage board as inline CSS |
| 19 | flags.production.json | Config as a view, not a file |

The implementation-plan template (#16) is the **archetype for
backend.html and architecture.html**. It demonstrates the section
structure we use: prompt → effort → surfaces → milestones → data flow
→ mockups → key code → risks → open questions.

## Universal patterns (all 20 examples share these)

### 1. Title strip at the top

Every file starts with `<Title> · <Surface>`. The two parts are
visually distinct (the title in display-weight, the surface in
muted-text below it). For our specs:

- `Architecture · <build-name>`
- `Backend · <build-name>`
- `Frontend · <build-name>`
- `UX journey · <build-name>`

### 2. The prompt, preserved verbatim

The original ask is rendered as a quote near the top. The reader
verifies the doc answers what was asked, not what the LLM thought was
asked. In our templates: `<p class="prompt">"<original user prompt, verbatim>"</p>`.

### 3. Numbered sections, not headings-only

Each section is a *decision*, not a category. The implementation-plan
template has `01 Milestones`, `02 Data flow`, `03 Mockups`, `04 Key
code`, `05 Risks & mitigations`, `06 Open questions`. Each one
commits to a position. The reader never asks "what is this section
about" — the number is enough.

### 4. Inline HTML/CSS mockups

Visual artifacts are real HTML, not images, not "see Figma." Empty
states, populated states, error states, success states — all inline
CSS. The reader skims the spec on a phone and *sees the screen*.

### 5. Inline code, real paths

Code blocks reference real files: `packages/db/migrations/0042_...`.
The reader can grep their repo for the path and find the actual code.
No "approximately this signature."

### 6. Data flow as ASCII with a legend

The implementation-plan template draws the data flow as a sequence of
boxes and arrows in the page itself, with a legend below:

```
Solid = request/response path. Dashed clay = realtime fan-out.
The composer never waits on the dashed path.
```

We use the same convention: **solid = request/response, dashed =
async/fan-out, dotted = fire-and-forget.**

### 7. Risks & mitigations as a table

Not "things to consider." A concrete failure mode per row:

| What can fail | Detection | Mitigation |
|---|---|---|
| Postgres unreachable during write | API returns 5xx, latency p99 > 2s | Client retries with exponential backoff, capped at 5 min |

### 8. Open questions as a section, not a TODO

The implementation-plan template ends with `06 Open questions` as a
real section. The reader knows what's undecided. We follow the same
pattern — open questions are an explicit section, filled in by the
second LLM loop.

## What we explicitly do NOT steal

- **SVG illustrations** (example #10). We skip per principle 8. If the
  user wants visuals, they're post-approval polish, not part of v1.
- **Interactive JavaScript** (example #15, the consistent-hashing
  explainer). Our specs are static. The reader is skimming, not
  interacting.
- **External CDN imports** (no examples do this anyway, but worth
  noting). The file is self-contained. If you find yourself reaching
  for `<script src="https://...">`, stop.

## The implementation-plan template, distilled

The single most important example. Sections, in order:

1. **Title + prompt** — what was asked
2. **Effort** — single line: `~2 weeks`
3. **Surfaces touched, New tables, Feature flag** — three short
   metadata lines
4. **Milestones** — numbered slices, each behind a flag, each
   independently reviewable
5. **Data flow** — ASCII diagram with legend
6. **Mockups** — inline HTML/CSS, one per major state
7. **Key code** — the 2-3 snippets most likely to be done wrong
8. **Risks & mitigations** — table
9. **Open questions** — section, not a TODO

This is the skeleton our backend.html uses directly. Architecture
rearranges slightly (system context first, no milestones), and frontend
adds `<section id="a11y">` and `<section id="state-model">`.

## Voice

Direct, technical, no marketing. The reader is an engineer assigned the
ticket. The implementation-plan template's voice is the reference — read
example #16 out loud, that's the bar.

## Why this format works for LLM-generated specs

Three properties the format has that other formats don't:

1. **Self-contained.** One file, opens in any browser, no broken
   references. The user can email it, archive it, commit it.
2. **Renderable in chat previews.** Telegram's link preview will
   render the title; the user can scan filenames at a glance.
3. **Skimmable on a phone.** The 20 examples are explicitly designed
   for "the reviewer reads on their phone." Spec docs are the same
   shape — engineer assigned the ticket, 20 minutes, phone in hand.

This is the format. Don't reinvent it.
