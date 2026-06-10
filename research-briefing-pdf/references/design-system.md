# Design system: soft-modern data journal

The research-briefing skill ships with one default design — the
**soft-modern data journal** — and the `templates/briefing.html`
template renders in that aesthetic. This reference doc documents
the token set, the type pairing, and the swap pattern for
alternative skins.

## The default look (and why)

**Visual reference:** Stripe Press / FT Weekend tear-sheets /
Pitchbook research. Cream paper, near-black warm ink, ONE
terracotta accent, serif display + mono numerics, hairline rules
as section dividers, large display numerals, drop caps on ledes,
asymmetric grid, generous whitespace.

**Why this over navy + gold (the SpaceX briefing look) or pure
white + blue (the Bloomberg terminal look):**
- The cream paper reads as a *publication*, not a screen —
  the document is meant to be read end-to-end on a tablet or
  printed, not skimmed on a trading floor.
- The single terracotta accent forces editorial discipline —
  every red mark is meaningful (drop cap, italic emphasis word,
  key delta number, risk pill). Charts can't drift into
  Christmas-tree mode.
- Serif + mono pairing gives the page two registers: serif for
  voice (titles, body, pull quotes), mono for data (labels,
  numerics, sources, eyebrows). The eye knows where to look.
- Hairline rules replace boxes and callouts. A 0.5pt rule is
  enough structure to anchor a card without enclosing it.

## The 6 tokens that matter

```css
:root {
  --paper:     #f6f1e8;   /* page background — warm cream */
  --ink:       #1c1a17;   /* primary text — near-black, warm */
  --ink-soft:  #4a4640;   /* secondary text */
  --ink-faint: #8a857c;   /* labels, metadata, rules */
  --rule:      #2a2723;   /* hairline rule colour */
  --accent:    #b8412a;   /* ONE accent — terracotta */
  --gold:      #c89b3c;   /* chart series */
  --olive:     #6b7a3a;   /* chart series */
  --plum:      #6e4663;   /* chart series */
  --slate:     #3a5566;   /* chart series */
}
```

**Re-skin in 2 lines:** change `--paper` and `--accent` to the
newspaper/skin you want, and update the matplotlib `SRC_*colors`
set in `src/make_charts.py` to match. The chart palette must
stay in harmony with the page background — chart panels
default to the page paper color (`#f6f1e8`) and use the same
`--ink` and `--accent` for the primary and emphasis series.

## Three reference skins (proven or proposed)

| Direction        | Paper    | Accent   | Vibe                          |
|------------------|----------|----------|-------------------------------|
| **Soft-modern** (default) | `#f6f1e8` cream | `#b8412a` terracotta | Stripe Press / FT Weekend |
| **Editorial navy**        | `#fbfaf6` warm white | `#0d1b2a` ink blue | Bloomberg / Reuters research note |
| **Mono stark**            | `#ffffff` pure white | `#cc0000` red | McKinsey / consulting deck |

The 2nd (navy + gold) is what the SpaceX briefing used before
soft-modern was promoted. It's a solid alternative when the
client wants a more "financial institution" feel. The 3rd
(white + red) is the McKinsey / consulting-deck look — works
for advisory work where the data is the only thing that should
draw attention.

To switch: edit the `:root` block at the top of
`templates/briefing.html`, change `--paper` and `--accent`, and
update the chart palette. The full token list (including
--gold/--olive/--plum/--slate) is also in
`src/make_charts.py` as `SRC_COLORS` — change those too.

## Tear-sheet demo (the 2-page alternative design)

A frequent follow-up to a delivered briefing is: *"can I see a
different design for the same data?"* The fastest answer is a
**2-page tear-sheet demo** — a cover + one data-dense page, in
a different aesthetic, rendered to PDF. The first version of
this template served both as the default and as the tear-sheet
demo. They were separated on 2026-06-10.

For a tear-sheet demo specifically:
- Keep it to 2 pages (cover + 1 data page)
- No external chart PNGs — pure CSS, no matplotlib
- The donut chart uses CSS `conic-gradient` (no SVG, no canvas)
- The bar "chart" is a flexbox of `<div>` bars
- Renders in ~1s with headless Chrome

The old `templates/design-alternative-softmodern.html` file is
now consolidated into `templates/briefing.html` (which is the
full 12-page version). If you need a tear-sheet demo again,
copy the cover and the first tear-sheet page out of the full
template — the structure is identical, just shorter.

## Type pairing

- **Display + body:** Iowan Old Style (Apple) / Source Serif
  Pro (Google) / Georgia (universal fallback). All three work.
- **Numerics + labels + eyebrows:** JetBrains Mono / SF Mono /
  Menlo. The mono `font-variant-numeric: tabular-nums` gives
  the data column alignment that makes any number column
  readable.
- **Avoid:** Inter / Roboto / Open Sans for the body. They
  look like screens, not publications. If a sans is needed for
  a single page section, use a different weight of the same
  family (e.g. Source Sans for sidebar metadata).

## Pitfalls specific to the soft-modern aesthetic

- **Donut center text overlapping the ring.** A subtitle line
  often extends past the inner hole. Cleanest fix: drop the
  subtitle, keep a single short word in the center. Verified
  2026-06-09: vision hallucinated the overlap 3× in a row even
  after fixing; pixel-row inspection at the donut's center y
  confirmed the cream band was 100px wide and the text was
  19px. Vision is wrong; trust the pixels.

- **Source lines wrapping inside `.card-head`.** Add
  `white-space: nowrap; flex-shrink: 0;` to `.card .src` and
  shorten the source string.

- **Drop-cap line spacing.** The CSS `::first-letter { float:
  left }` drop cap needs `line-height: 0.82` and a small
  `padding-right: 2.5mm`. A `line-height: 0.85` (the default
  for a 38pt cap) leaves a visible gap on the first wrapped
  line.

- **Source-attribution alignment in pullquotes.** The opening
  curly quote at 22pt looks misaligned unless you add
  `text-indent: -5mm; padding-left: 5mm` to the blockquote.

- **Cream background vs white-default assumption.** Chart PNGs
  embedded in the HTML MUST match `--paper`. The
  `make_charts.py` helper sets `fig.patch.set_facecolor` and
  `ax.set_facecolor` to `#f6f1e8` — don't remove these, or the
  chart panels will render as white rectangles on the cream
  page.

## File map

| File                                          | Purpose                                |
|-----------------------------------------------|----------------------------------------|
| `templates/briefing.html`                     | Default 12-page template (this skill)  |
| `references/design-system.md`                 | This file                              |
| `references/anthropic-ipo-briefing-2026-06-10.md` | Worked example with the template  |
| `references/spacex-ipo-briefing-2026-06-08.md`| Predecessor design (navy + gold)       |
| `src/make_charts.py`                          | Chart generator (uses the same tokens) |
| `scripts/audit_layout.py`                     | Post-render layout audit               |
