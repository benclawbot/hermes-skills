# Design system

The exact visual design system every spec this system produces. Extracted
from `https://thariqs.github.io/html-effectiveness/` (the canonical
reference) and committed to `spec-style.css` in the HTML-specs repo.

**Every spec uses this CSS verbatim, inlined in a `<style>` block at the
top.** No additions, no removals, no overrides. The LLM is forbidden
from inventing new class names.

## Palette

| Token | Hex | Role |
|---|---|---|
| `--ivory` | `#FAF9F5` | Page background. Soft cream. |
| `--slate` | `#141413` | Primary text. Near-black. |
| `--clay` | `#D97757` | Accent. CTAs, focus rings, severity HIGH, step circles, open-question left-border. |
| `--oat` | `#E3DACC` | Chips. Section numbers, route chips, milestone tags, severity MED. |
| `--olive` | `#788C5D` | Success. "Done" dots, code-string highlighting. |
| `--gray-150` | `#F0EEE6` | Subtle bg. Prompt box, summary cells, screen headers. |
| `--gray-300` | `#D1CFC5` | Borders. 1.5px on every panel and table. |
| `--gray-500` | `#87867F` | Secondary text. Eyebrows, captions, mono labels, comments. |
| `--gray-700` | `#3D3D3A` | Body text default. |
| `--white` | `#FFFFFF` | Panel backgrounds. Mock bodies, code blocks, table cells. |

Three severity colors in `.risks`:
- HIGH: `#F3D9CC` bg, `#8A3B1E` text
- MED: `--oat` bg, `--slate` text
- LOW: `#E4E9DC` bg, `#4B5C39` text

## Typography

| Token | Font | Used for |
|---|---|---|
| `--serif` | `ui-serif, Georgia, 'Times New Roman', serif` | h1, h2, h3 (display weight 500, letter-spacing -0.01em) |
| `--sans` | `system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif` | Body, paragraphs, list items |
| `--mono` | `ui-monospace, 'SF Mono', Menlo, Monaco, monospace` | Eyebrows, labels, code, file paths, severity pills, open-question owners, ASCII diagrams |

## Document skeleton (every spec starts this way)

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{TYPE} · {BUILD-NAME}</title>
<style>
/* spec-style.css inlined verbatim */
</style>
</head>
<body>
<div class="page">

  <header class="page-head">
    <div class="eyebrow">{TYPE} · {BUILD-NAME}</div>
    <h1>{one-sentence summary}</h1>
    <div class="prompt-box">
      <span class="label">PROMPT</span>
      {verbatim original ask}
    </div>
  </header>

  <div class="summary">
    <div class="cell"><div class="k">{K1}</div><div class="v">{V1}</div></div>
    <div class="cell"><div class="k">{K2}</div><div class="v">{V2}</div></div>
    <div class="cell"><div class="k">{K3}</div><div class="v">{V3}</div></div>
    <div class="cell"><div class="k">{K4}</div><div class="v">{V4 [accent]}</div></div>
  </div>

  <section>
    <div class="sec-head"><span class="num">01</span><h2>{Section name}</h2></div>
    <p class="sec-intro">{one-sentence intro}</p>
    ...content...
  </section>

  ...

  <section>
    <div class="sec-head"><span class="num">NN</span><h2>Open questions</h2></div>
    <div class="open-q">
      <div class="q">
        <div class="qt">{the question}</div>
        <div class="qd">{why we need an answer}</div>
        <div class="owner">OWNER · {role}</div>
      </div>
    </div>
  </section>

</div>
</body>
</html>
```

## Component classes (use these, don't invent new ones)

### Header & summary
- `.page` — outer 1120px max-width container
- `.page-head` — header block, max-width 820px
- `.eyebrow` — 12px mono uppercase, gray-500, letter-spacing 0.08em
- `.prompt-box` — gray-150 bg, 1.5px gray-300 border, 12px radius
- `.prompt-box .label` — mono uppercase, used for the "PROMPT" tag
- `.summary` — 4-column grid (collapses to 2 on mobile <900px)
- `.summary .cell` — white card, 12px radius
- `.summary .k` — mono uppercase label
- `.summary .v` — large value (use `class="v accent"` for the lead value, in clay)

### Section chrome
- `.sec-head` — flex row with the numbered chip + h2
- `.sec-head .num` — oat-bg mono chip "01", "02", ...
- `.sec-intro` — one-sentence intro paragraph under the h2

### Code blocks
- `.code-block` — wrapper
- `.code-block .file-label` — mono file path label above the code
- `.code` — dark slate background, 12px radius, padding 18px 20px
- `.code pre` — 12.5px mono, color `#E8E6DE`
- `.code .kw` (clay) — keywords (CREATE, SELECT, function, const, ...)
- `.code .str` (olive) — strings
- `.code .cm` (gray-500) — comments
- `.code .fn` (tan `#C9B98A`) — function names

### Diagrams
- `.diagram` — white panel, 1.5px gray-300 border, 12px radius, 28px padding
- `.diagram pre` — mono 12.5px, preserves box-drawing characters
- `.caption` — small gray-500 italic-style paragraph below the diagram

### Mockups
- `.mocks` — 2-column grid (collapses to 1 on mobile <900px)
- `.mock` — white panel with 1.5px border
- `.mock .mock-label` — gray-150 header bar, mono uppercase
- `.mock .mock-body` — padded 22px content area
- `.card-mock` — for inline card mockups (gray-300 border, ivory bg, 10px radius)
- `.comment` / `.avatar` / `.bubble` / `.composer` — for chat/thread mockups

### Risks table
- `.risks` — table with 1.5px border, 12px radius
- `.risks .row` — grid row (3 columns: 1.6fr / 90px / 1.6fr)
- `.risks .cell` — base cell
- `.risks .cell.head` — gray-150 bg, uppercase, slate text
- `.sev` — severity pill (mono, 6px radius)
- `.sev.high` / `.sev.med` / `.sev.low` — colors per palette

### Open questions
- `.open-q` — vertical flex container, 14px gap
- `.q` — white card, 1.5px gray-300 border, 4px clay left-border, 10px radius
- `.q .qt` — bold slate question
- `.q .qd` — gray-500 description
- `.q .owner` — mono gray-500 small text "OWNER · {role}"

### Personas (ux-journey)
- `.persona` — white card with 12px radius
- `.persona .name` — serif 19px slate
- `.persona .role` — 13px gray-500
- `.persona .quote` — italic, 3px clay left-border, 12px padding-left

### Screens (ux-journey)
- `.screen` — white panel with 1.5px border
- `.screen-head` — gray-150 header with route chip + screen name
- `.screen-head .route` — oat mono chip like "/dashboard"
- `.screen-head .name` — serif 19px slate
- `.screen .states` — grid of state mini-cards
- `.screen .state` — ivory bg, 8px radius
- `.screen .state .k` — mono uppercase label

### Journey steps (ux-journey)
- `.journey` — vertical flex, with connecting lines between steps
- `.journey-step` — 2-col grid: clay circle + body
- `.journey-step .step-num` — clay circle with white number
- `.journey-step::after` — gray vertical line connecting to next step (auto via CSS)

### Milestones (architecture)
- `.milestones` — vertical flex
- `.milestone` — 3-col grid: when / dot+line / body
- `.milestone .when` — mono right-aligned
- `.milestone .dot` — 14px circle, 3px clay border, white fill
- `.milestone .dot.done` — olive fill
- `.milestone .line` — 2px gray-300 vertical line
- `.milestone .tag` — gray-150 chip, mono 11.5px

### Generic
- `p` — 14px body, gray-700
- `code` — inline code chip (gray-150 bg, 1px gray-300 border, 4px radius)
- `pre` — mono, preserves whitespace
- `table` / `th` / `td` — default 13.5px, gray-150 header bg
- `strong` — slate (not bold by default; color carries emphasis)
- `ul, ol` — 14px items, 6px vertical gap

## Layout conventions

- **Page padding:** 56px top, 32px sides, 120px bottom (the body)
- **Page max-width:** 1120px
- **Header max-width:** 820px (so eyebrow + h1 don't span the full table)
- **Section gap:** 64px between sections
- **Cell gap inside summary:** 16px
- **Mockup grid gap:** 28px
- **Risks table row gap:** 1.5px (the border serves as separator)
- **Code block padding:** 18px 20px

## Voice and content rules

- Direct, active voice. No "the user is able to."
- No marketing. No "delightful," "seamless," "intuitive."
- Every sentence commits to a position. No "could be," "might want to consider."
- Lists are for artifacts (schema, endpoints, mockups), not adjectives.
- SQL is real SQL with constraints, indexes, default values, ON DELETE behavior.
- API responses are real JSON. Error tables are exhaustive.
- ASCII diagrams use box-drawing characters: `┌ ─ ┐ │ └ ┘ ┬ ┴ ├ ┤ ┼ ▼ ▶ ◀`

## Forbidden patterns

- ❌ `<script>`, `<link rel="stylesheet" href="...">`, `<img>`, `<svg>`
- ❌ Inline `style="..."` for color, font, spacing, layout
- ❌ Tailwind classes (the file is self-contained — no build step)
- ❌ New CSS classes not defined in this system
- ❌ Emoji
- ❌ Markdown-style headings inside the spec body (use `<section>` + `.sec-head`)
- ❌ `class="prompt"` (the class is `prompt-box`)

## Worked example

A complete reference file showing every pattern: `examples/sample-spec.html`
in the HTML-specs repo. Open it in a browser to see the design system in
action, or use it as a starting point for new specs.
