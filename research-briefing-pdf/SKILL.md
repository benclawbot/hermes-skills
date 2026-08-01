---
name: research-briefing-pdf
description: "Produce a polished PDF research briefing from public sources (SEC filings, press releases, public web pages) — with charts, tables, risk heatmaps, and a clear call. Loads when Thomas says 'make me a full briefing', 'give me a PDF report on X', 'research Y and produce a document', or hands over a URL/PDF and asks for written analysis. The default design is the 'soft-modern data journal' aesthetic (cream paper, terracotta accent, serif display, mono numerics) — re-skinnable by swapping the :root CSS tokens. Uses single-flow pagination (one continuous HTML document, browser paginates, no audit layer required). Includes layout-density pitfalls, the snap-Chromium-writes lie, the file://+spaces pitfall, the relative-img-src pitfall, the pdftotext/pdfinfo/pdftoppm verification trio, the chromium grid-1fr collapse fix (use flexbox), and the vision-analyze layout-hallucination reality check."
version: 2.3.0
author: Hermes Agent (Thomas)
license: MIT
metadata:
  hermes:
    tags: [pdf, research, briefing, sec-edgar, charts, headless-chrome, matplotlib, design-system]
    category: productivity
---

# Research Briefing PDF

A workflow for turning public sources (SEC filings, PDFs, web pages,
press releases) into a polished, multi-page research PDF with
charts, tables, and a clear call. Output is institutional-quality
— cover page, exec summary, financial tables, risk analysis,
methodology, sources.

The default aesthetic is **soft-modern data journal** (cream paper,
terracotta accent, serif display, mono numerics) — the look of
Stripe Press / FT Weekend / Pitchbook tear-sheets. Re-skin by
swapping the `:root` CSS tokens; the chart palette and the
typography both follow the same token set.

## When to use this skill

- Thomas says "make me a full briefing on X" / "produce a PDF
  report" / "research Y and write me a document" / "give me a
  writeup I can read on the plane"
- Thomas hands over a URL or PDF and asks for written analysis
- The deliverable is a single PDF Thomas can read end-to-end,
  not a chat thread

Do NOT use this skill for:
- Short chat-style analysis (no PDF needed)
- Obsidian vault generation (use `deep-research-obsidian`)
- Single-page summary (just write it in chat)
- Real-time market commentary (use `fast-research-digest`)

## The single most important rule (2026-06-27)

**Don't build N page boxes. Build one continuous document and
let the browser paginate.** This is the lesson from the session
that produced `last30days-world-briefing-2026-06-27.pdf`: the
original 4-page design used `<section class="page">` with
`width:210mm; height:297mm; page-break-after:always` for each
section. Bottom-blank % on page 3 was flagged repeatedly by
verification scripts that had to be tuned because the test
itself was wrong. Thomas's response:

> "instead of trading the bottom of the page isn't empty, isn't
> it easier that the text is continuous with no page break
> from one section to the next? That's a lot of testing done
> just to produce a simple PDF"

The fix was structural: remove the `.page` height/page-break
boxes; add `page-break-inside: avoid` to charts and
`page-break-inside: avoid` to list items. The browser now
paginates correctly on the first pass and no audit is needed.
The `scripts/audit_layout.py` was retired because the bug
class it caught no longer exists.

If you find yourself reaching for an audit layer, a pixel
density checker, or a "verify every page" loop: stop. The
problem is probably in the HTML structure, not in the lack
of verification. See `references/single-flow-pagination.md`
for the working template and the chromium flags required.

## Design system (the soft-modern data journal)

Every briefing ships in this aesthetic by default. The full token
set is in the `:root` block at the top of `templates/briefing.html`.
The 6 tokens that matter:

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

**Type pairing:** Iowan Old Style / Source Serif Pro (display +
body) + JetBrains Mono (labels, numerics, eyebrows, sources).
Serif carries the voice; mono carries the data.

**Visual grammar:** hairline rules as section dividers; large
display numerals; drop caps on ledes; tabular-num figures;
asymmetric grid; generous whitespace; one accent color used
sparingly (drop cap, italic emphasis word, key delta numbers,
risk-severity pills).

**Re-skin in 1 line:** change `--paper` and `--accent` (e.g. to
`#0d1b2a` / `#e0a458` for a navy Bloomberg look). Everything
cascades. The chart palette also needs the matplotlib `SRC_*
colors` set to match the new tokens — see `src/make_charts.py`
for the exact hex values.

## The pipeline (worked, not theoretical)

```
   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐   ┌────────┐
   │  PULL   │ → │  EXTRACT │ → │  CHART   │ → │  HTML  │ → │  PDF   │
   └─────────┘   └──────────┘   └──────────┘   └────────┘   └────────┘
   SEC EDGAR,    BeautifulSoup,   matplotlib,    template      Chrome
   curl, wget,   pdftotext,       Agg backend,   with CSS      --print-to-pdf
   PDF download  regex patterns   tight figure   tokens        verify w/ pdfinfo
```

1. **Pull.** `curl -sL -A "Hermes Research research@hermes.local" <url>`
   with a real User-Agent. For PDFs: download then
   `pdftotext -layout file.pdf file.txt` to keep the text
   positioned. For HTML: download then strip with a tiny Python
   `HTMLParser` subclass.
2. **Extract.** Grep the cleaned text for the structured data you
   need. Don't ask an LLM to do this — it's faster and more
   verifiable with regex.
3. **Chart.** Matplotlib Agg backend. One chart per file,
   `savefig(..., bbox='tight', dpi=150)`. **Use the soft-modern
   palette in `src/make_charts.py`** (cream background `#f6f1e8`,
   ink `#1c1a17`, accent terracotta `#b8412a`, supporting
   gold/olive/plum/slate). Standard size 9×4.2 inches. Source
   line at `fig.text(0.01, 0.015, ...)` after
   `subplots_adjust(bottom=0.22)`.
4. **HTML.** Copy `templates/briefing.html` and edit the content
   blocks. The template is self-contained (CSS at the top, all
   design tokens in `:root`). Use absolute `file://` paths for
   chart `<img>` tags. The template handles the 12-page flow
   with `page-break-after: always` between major sections —
   don't add more.
5. **PDF.** Headless Chrome for Testing
   (`~/.cache/ms-playwright/chromium-<rev>/chrome-linux64/chrome`).
   See pitfalls — snap chromium lies about writes.

## Verification trio (run all three before delivery)

```bash
# 1. PDF exists, expected page count, expected size
pdfinfo output.pdf | grep -E "Pages|File size|Title"

# 2. All chart images actually embedded (not just referenced)
pdfimages -list output.pdf | head
# Expect: N large image entries (700-870px wide, ~15-50KB each)

# 3. Key facts present in the extracted text
pdftotext output.pdf - | grep -E "<key fact 1>|<key fact 2>|..."
```

Also render 2-3 preview pages with `pdftoppm -png -r 80 -f N -l N
output.pdf /tmp/preview` and use `vision_analyze` to check
readability. **Vision is reliable for relative comparisons but
UNRELIABLE for absolute blank-space percentages and for asserting
specific element overlaps** — for those, use `pdfimages -list`
to confirm chart embeds and `pdftotext -layout` to verify text
flow. The legacy `scripts/audit_layout.py` was removed
2026-06-27 because the bug class it caught no longer exists
with single-flow pagination (see "The single most important
rule" at the top of this file).

## Pitfalls (learned the hard way)

These are the bugs that have shipped (or nearly shipped) on past
briefings.

### Tool/runtime pitfalls

- **(2026-06-08) Snap chromium lies about writes.**
  `/snap/bin/chromium --print-to-pdf=foo.pdf` prints "N bytes
  written" but the file isn't on disk. The snap is sandboxed and
  stdout reflects the internal buffer. **Fix:** use Chrome for
  Testing from
  `~/.cache/ms-playwright/chromium-<rev>/chrome-linux64/chrome`.
  If you must use snap, the workaround is
  `cd <dir-with-no-spaces-or-hyphens> && snap-chromium --print-to-pdf=...`.

- **(2026-06-08) `file://` URLs with spaces in the path break
  headless Chrome.** `file:///tmp/spacex ipo/briefing.html`
  silently fails. **Fix:** use a path without spaces.

- **(2026-06-08) Relative `<img src>` paths don't resolve
  correctly when the HTML is at a different dir than the
  charts.** **Fix:** use absolute `file:///` paths. Always verify
  with `pdfimages -list | head` after rendering.

- **(2026-06-08) `matplotlib ax.bar()` with a single value
  returns a `BarContainer` of length 1, not a `Rectangle`.** For
  multi-value bars (lists), the container IS a list of
  Rectangles. The asymmetry bites on ownership / cap-stack
  charts.

- **(2026-06-27) Chromium `--print-to-pdf` silently breaks
  `display: grid` with `1fr` track in multi-page layouts.**
  Standalone HTML tests show grid `12mm 1fr` rendering full-width
  correctly. Same CSS nested inside `<section class="page">` with
  `@page { margin: 0 }` and `box-sizing: border-box` collapses the
  `1fr` body column to ~50px wide (text wraps word-by-word in a
  narrow left strip). Pixel-audit catches it — pdftotext does NOT,
  because it flattens narrow-column wrapped text into the same
  shape as wide text and reports full-width paragraphs. **Fix:**
  use `display: flex; flex: 0 0 <counter-width>; gap; .body { flex:
  1 1 0; min-width: 0 }` instead. Flexbox works correctly inside
  the `.page` context; grid does not. Verified 2026-06-27 on the
  30-day world briefing: vision reported "narrow column" on the
  grid version, pixel audit confirmed it (78–136px ink width),
  flexbox fix restored 78–831px (full body width).

- **(2026-06-08) Headless Chrome doesn't render
  `--no-pdf-header-footer` AND page-headers consistently.** The
  template uses neither; pages are styled entirely with
  `@page { size: A4; margin: 0 }` and manual padding on `.page`.

- **(2026-06-08) The vision model is the only check for typo
  and balance bugs.** Always render at least the cover and one
  interior page through `vision_analyze` before delivery. The
  text-extraction tools verify the right content is there; the
  vision model verifies the right content is *visible* and *not
  embarrassing*. **But for blank-space and overlap claims,
  vision is unreliable — see layout-density pitfalls below.**

### Layout-density pitfalls (HTML/CSS — verified 2026-06-09)

The first briefings shipped with these. They are now the
highest-priority class of bugs. After producing two briefings
in a row with the same defect, the most common shipping-quality
issues are *not* chart-data errors — they are layout density.
The previous `scripts/audit_layout.py` post-render check has
been retired; the fix is to use **single-flow pagination**
(no per-section `height: 297mm; overflow: hidden; page-break-after:always`
boxes) so the browser paginates correctly on the first pass.

- **`page-break-before: always` on every h2 forces orphan
  pages.** A 2-line section after a 1-line section gets its own
  page. **Fix:** only force page breaks before the *first* major
  section of a logical unit, and let CSS pagination flow the
  rest.

- **(2026-07-10) Orphan section header on dense sections.**
  `break-after: avoid` on h2 alone is NOT enough when section
  content density forces a page break inside the section.
  Chromium then sticks the h2 + first paragraph at the bottom of
  page N and pushes the rest of the section to page N+1 — a
  classic "title-only page-bottom" defect. Verified on the
  Cahier de Dictées briefing (9-page output, §07 GTM header
  at bottom of page 6 with content starting page 7).
  **Fix hierarchy:**
  1. Pair `break-after: avoid` on h2 with `break-before: avoid`
     on the h2's first child — keeps the heading glued to its
     lede paragraph regardless of how the rest of the page
     breaks.
  2. If section content + folio won't fit one page, add
     `section.spread { break-before: page }` so each major
     section starts on its own page. Accept the page-count
     increase.
  3. If neither fits, compact the section (shorter list, smaller
     margins, fewer items) until content + folio fit one page.
  Verify with: `pdftotext -layout briefing.pdf - | awk -v
  RS="\f" 'NR>1 {print "P"NR": "substr($0,1,80)}'` — every page
  should have section content, not just an end-strip or folio.

- **(2026-07-10) Heading+lede glue is bidirectional.**
  `h2 { break-after: avoid }` keeps the heading on the same
  page as the following paragraph — but only if the paragraph
  *immediately* follows. Adding `h* + p { break-before: avoid }`
  is the belt-and-suspenders pattern that prevents the
  reverse orphan (paragraph stranded above its heading on the
  next page). Cheap, no downside, recommended for every
  briefing.

- **Long tables / lists at end of a section leave the next page
  30–40% empty.** **Fix:** (1) reduce vertical padding on
  callouts and table rows from 5pt to 3pt; (2) move callout
  boxes to be inline rather than after the chart; (3) rebalance
  by adding the next section's intro paragraph as a teaser.

- **Orphaned headings.** A `h3` at the bottom of a page with
  content starting on the next page looks broken. **Fix:** keep
  h3 with at least 2 lines of content, or move the heading to
  the next page manually.

- **Section break + short content = page 2 of section is 90%
  empty.** **Fix:** put forced page breaks *before* the h2 of
  the section that genuinely starts a new topic, not before
  every h2.

- **`min-height: 95%` on the cover** + lots of vertical content
  pushes the disclaimer off the cover onto page 2 (often
  half-empty). **Fix:** tighten cover content; let the
  disclaimer sit at the natural bottom.

- **(2026-06-27) CSS `display: grid` with `::before { content: counter(...) }`
  on `<li>` causes per-word vertical wrap in chromium
  `--print-to-pdf`.** A list like
  `<li>` + empty leading `<div>` + body `<div>` with
  `grid-template-columns: 9mm 1fr` plus `counter-increment: c`
  on `<li>` and `::before { content: counter(c) }` rendered
  every word of every item on its own line — the body column
  collapsed to ~10mm wide. Cause: chromium's PDF print path
  computes grid track sizes before resolving pseudo-elements
  attached to the grid item, leaving the `1fr` track unconstrained
  and the leading empty cell (holding the counter pseudo-element)
  consuming the row's natural width. **Fix:** don't use
  `::before` for list counters in PDF-targeted HTML. Use explicit
  numbered markers — `<li><span class="n">01</span><div class="body">…`
  with `grid-template-columns: 12mm 1fr` and hard-coded numbers.
  Pixel-audit + pdftotext will both confirm the fix; vision will
  sometimes still hallucinate "narrow column" (see Vision-model
  unreliability section). Verified 2026-06-27 on the 30-day world
  briefing.

### Layout-density pitfalls (matplotlib charts — verified 2026-06-09)

- **Bar value labels at `v+offset` collide with annotations at
  the same y.** **Fix:** use `xytext` with both x and y offsets
  that put the annotation *above and to the left* of the bar
  label.

- **Scatter heatmap labels with `xytext=(8, 0)` overlap when
  points share a row or column.** **Fix:** abandon inline labels
  entirely. Use **numbered markers** in the chart + a side
  legend table mapping number → name.

- **Log-scale bars with values 1, 4, 6** — value labels stack at
  the bottom of the axis. **Fix:** use linear scale, label only
  the top 3 bars, and add a "see table" note.

- **Cap stack with mixed-size segments.** When stacking bars
  and 5 of 8 segments are < 5B while 3 are > 13B, trying to
  label all 8 in the bar area fails. **Fix:** label the large
  segments above the bar normally; print the small segments in
  a **single horizontal legend line** below the chart.

- **Stacked horizontal bar with mixed-size segments.** If you
  have segments of 32%, 48%, 12%, 8% — the 12% and 8% cannot fit
  in-bar text. **Fix:** label the two largest in-bar (centered
  white text), use leader lines for the small ones going DOWN
  with **staggered subtitle y-positions** and a **fixed x
  position** for all small labels so they stack vertically
  rather than collide horizontally.
  - **Second fix (verified 2026-06-10):** Even with leader lines,
    if two small labels are close in x (e.g. 12% segment center
    at x=68, 8% segment center at x=88) and the labels themselves
    are long ("Compute partners", "Employees & advisors"), they
    collide horizontally as "Compute partEmployees". The robust
    fix is a **side-callout table**: draw leader lines from each
    small segment down to a common y-row, then place text labels
    at **fixed, evenly-spaced x positions** (e.g. 58 and 78)
    regardless of segment center. Decouples label position from
    segment position.

- **Chromium `--print-to-pdf` does NOT respect CSS `max-width: 100%`
  on images for PDF output.** Charts wider than the page content
  width will overflow the right edge of the PDF, even if the
  HTML says `width:100%; max-width:100%;`. **Fix:** regenerate the
  chart PNG at a width that fits the page natively (~6.5" for A4
  with 18mm margins = 909px at 110dpi). Verify with
  `PIL.Image.open().size[0] < page_width_px` before rendering.
  (Verified 2026-06-10 with funding timeline chart overflowing.)
  **Hard rule for every chart PNG before PDF render:** width MUST
  be ≤ 870px (allowing 39px slack for `bbox_inches='tight'` crop).
  Add this assertion to `make_charts.py` as the final pre-step —
  fail loud, don't ship overflow.

- **(2026-07-10) Bar value labels at `v+offset` AND priority
  badges at negative-x collide with the y-tick labels.** Pattern
  was `ax.text(aud + 8, ..., ha='left')` for the value (right of
  the bar) and `ax.text(-25, ..., ha='right')` for the badge
  (left of the bar, in the negative-x gutter). The badge was in
  the same x-band as the y-tick text. **Fix:** move the badge
  **inside** the bar at the left edge — `ax.text(2, ..., ha='left',
  color=PAPER, weight='bold')` — paper-colored text reads on the
  colored bar and never collides with anything. Also tighten
  `set_xlim` to start at 0 (no negative-x gutter) and add a paper-
  colored bbox to the right-side value label so it reads cleanly
  past the bar end.

- **(2026-07-10) Annotation labels collide with legends sharing
  the same corner.** `ax.legend(loc='lower left')` puts a 4-item
  size legend in the bottom-left. A nearby bubble at (1,1) with
  label-offset `(-14, +14, 'right')` puts the label *right* of
  the bubble — directly over the legend's "Fort" item. **Fix:**
  don't rely on `(-dx, +dy)` for points in the lower-left
  quadrant. Either (a) push the label *up-right* with
  `(+14, +18, 'left')` so it sits above the legend, or (b)
  shrink the legend (`labelspacing`, `borderpad`) and move it
  with `bbox_to_anchor=(0.02, 0.02)` to give the label space.
  Diagnose before guessing: vision missed this collision on
  chart 6; only a pixel-band scan caught it.

- **(2026-07-10) Bottom-of-axis callouts (milestone text, source
  lines, lede footnotes) sit flush against x-tick labels.**
  `ax.text(day, -0.6, txt, va='top')` puts the milestone box at
  y=-0.6 with no background — the x-axis tick labels at y=0
  visually crash into it. **Fix:** wrap callouts in a paper-color
  bbox (`bbox=dict(boxstyle='round,pad=0.25', fc=PAPER,
  ec='INK_FAINT', lw=0.4, alpha=0.9)`) and increase y-limit
  headroom (`set_ylim(-1.6, ...)` instead of `-1.2`). The bbox
  both visually separates and lets the text slightly overlap the
  tick band without becoming unreadable.

- **(2026-07-10) In-bar text on a categorical barh stacks on the
  FIRST row.** `ax.barh(label, ...)` builds a categorical y-axis.
  Calling `ax.text(cx, 0, txt)` or `ax.text(cx, idx, txt)` to label
  each bar puts the text at the *numeric* y-coordinate 0/idx, which
  matplotlib resolves to the FIRST category — so all three in-bar
  labels collapse onto Phase 0. **Fix:** pass the category NAME as
  the y coordinate: `ax.text(cx, label, ...)`. For sub-labels
  *below* the bar, use `ax.annotate(sub, xy=(cx, label),
  xytext=(0, -22), textcoords='offset points', ...)` — this also
  decouples the sub-label from the categorical y-resolution. Full
  pattern in `references/matplotlib-label-collision.md` (Fix 7).
  Symptom: vision audit says only the first bar has its in-bar
  text and the others are empty.

- **(2026-07-10) Paper-color bbox backplates used to "fix" label
  overlap instead of actually separating label positions.** When
  two `ax.annotate()` labels collide, the instinct is to add
  `bbox=dict(boxstyle='round,pad=0.25', fc=PAPER, ec='none',
  alpha=0.85)` to each and call it fixed. **The bbox only paints a
  paper-colored box over the colliding text — the underlying
  geometry is still overlapping.** Three rounds of this pattern
  produced three visually-clean charts that were still
  layout-colliding under the bboxes; the user flagged the same
  issue repeatedly. **Fix hierarchy:** (1) actually move labels
  apart (Fix 1/2/6/7 of `references/matplotlib-label-collision.md`,
  or numbered-marker side-legend past 12 labels); (2) THEN add
  bbox backplates for legibility when labels are still close —
  never as the primary fix. **Verification:** read the source
  `text()` and `(dx, dy, ha)` tuples, not the rendered PNG —
  pixel-band scan can catch *some* bbox-masked overlap but the
  source-level check is faster. Treat any chart that needed bboxes
  to "look clean" as a code review item, not a finished chart.

- **Pre-size the figure, don't just post-verify.** A naive
  `(9, 4.2)` inch figure at `dpi=150` produces a 1350×630 PNG
  (~7" wide after `bbox_inches='tight'` crops a bit), which trips
  the 870px limit. The skill's `verify_width` assertion catches
  it post-savefig but wastes a render cycle. **Fix at the source:**
  use `(7, 3.6-4.2)` inches at `dpi=120` for A4 single-column
  charts, `(9, 4.2)` at `dpi=120` only for full-spread hero
  charts that can span both columns. The formula that survives
  `bbox_inches='tight'` crop reliably: `png_width_px ≈
  figsize_inches × dpi × 1.05`. Keep that ≤ 870. Verified
  2026-07-10 on the Cahier de Dictées market brief — six charts
  all landed at 813-847px wide on first attempt after applying
  this sizing rule.

- **Source line collides with x-axis tick labels.**
  `fig.text(0.01, 0.005, ...)` with default `bbox_inches='tight'`
  puts the source at the same y-level as the bottom of the
  x-tick labels. **Fix:**
  1. Call `fig.subplots_adjust(bottom=0.22)` BEFORE the source
     text.
  2. Place the source at `fig.text(0.01, 0.015, ...)`.
  3. For complex charts use `bottom=0.24` or higher.
  4. After regeneration, **verify the gap with pixel analysis** —
     see Pre-delivery audit below. Target: gap > 30 pixels.

- **`ax.text(..., transform=ax.transAxes, ...)` for notes on a
  log-scale chart lands in the wrong place.** **Fix:** put the
  note in the source attribution (`fig.text(...)`) or as a
  `fig.text` outside the axes entirely. Or use a side legend
  table.

- **(2026-07-10) Scatter/bubble chart `annotate()` labels stack
  on top of each other when multiple points share a y-band.**
  The textbook pattern `ax.annotate(name, xy, xytext=(0, 14),
  ha='center')` puts every label *above* its point — when 3+ bubbles
  are at similar y (e.g. three competitors at y≈0.3 with x spread
  0/1/2), the labels overlap. **Fix:** per-name offset dict
  `{(dx, dy, ha)}` so labels radiate in 8 directions, plus
  paper-colored bbox for visual separation. Companion fixes:
  `set_ylim(..., top + 0.25)` for dy=+24 headroom, `set_xlim(-0.3, ...)`
  for dx=-12 left-edge room, increase `figsize` height (e.g.
  `(7, 4.6)` from `(7, 3.8)`). Escalate to numbered markers +
  side legend past ~12 labels. Full pattern and verification
  recipe in `references/matplotlib-label-collision.md` (Fix 6).
  Verified on Cahier de Dictées `02_positioning.png` — 8 distinct
  label y-bands (168, 183, 203, 297, 310, 361, 375, 448 px),
  zero collisions.

### Design-specific pitfalls (soft-modern — verified 2026-06-09)

- **Donut center text overlapping the ring.** A subtitle line
  ("DELAWARE · 2021") often extends past the inner hole even
  when the main label fits. Cleanest fix: drop the subtitle,
  keep a single short word in the center ("PBC") and put
  details in the surrounding legend. If you must have a
  subtitle, increase the radial hole to 38–40% and shrink the
  text.

- **Source lines wrapping inside `.card-head`.** When the card
  title is long, the source line wraps. **Fix:**
  `white-space: nowrap; flex-shrink: 0;` on `.card .src` and
  shorten the source string ("SRC · PR / 8-K" beats "SRC ·
  COMPANY DISCLOSURES").

- **Drop-cap line spacing.** The CSS `::first-letter { float:
  left }` drop cap needs `line-height: 0.82` (tighter than
  default) and a small `padding-right: 2.5mm`. A `line-height:
  0.85` (the default for a 38pt cap) leaves a visible gap on
  the first wrapped line.

- **Source-attribution alignment in pullquotes.** The opening
  curly quote (`"`) at 22pt looks misaligned unless you add
  `text-indent: -5mm; padding-left: 5mm` to the blockquote.

- **Cream background vs white-default assumption.** When
  embedding chart PNGs in the HTML, the chart background MUST
  match `--paper` (`#f6f1e8`). The default matplotlib white
  background creates a visible "white rectangle" on the cream
  page. The `make_charts.py` helper sets
  `fig.patch.set_facecolor('#f6f1e8')` and
  `ax.set_facecolor('#f6f1e8')` — don't remove these.

### Vision-model unreliability (verified 2026-06-09, confirmed live 2026-06-27)

- **Vision-analyze hallucinates layout percentages.** Vision
  consistently reports "30–65% blank at bottom" on pages that are
  fine (the 16mm page margin is ~8% blank; vision inflates it 4-8×),
  and reports "labels overlapping" on charts that are geometrically
  clean. **Fix:** vision is reliable for *relative* layout problems
  (is chart X more crowded than chart Y?) but unreliable for
  *absolute* percentages and for asserting "these specific N labels
  overlap". Trust `pdfimages -list` (real chart embeds) and
  `pdftotext -layout` (real text flow) instead of vision for layout
  truth. (Pixel-audit script retired 2026-06-27 — single-flow
  pagination made it unnecessary.)

- **(2026-07-10) For matplotlib chart label collisions specifically,
  vision is even worse than for page layout.** Across 4 vision calls
  on chart 6 of the Cahier de Dictées brief, vision returned
  "User Safety: safe" (no description) twice, gave a generic
  thumbnail description twice, and never named the actual collision
  (the "Apps.éducation" label overlapping the "Fort" legend item).
  **Fix:** use a PIL pixel-band scan to find real text collisions
  before trusting vision. The scan finds text rows (consecutive
  y-rows with dark pixels) and flags any two adjacent bands whose
  vertical gap is < 4px AND whose x-ranges overlap by > 30px:

  ```python
  from PIL import Image
  import numpy as np
  img = np.array(Image.open('chart.png').convert('RGB'))
  gray = img.mean(axis=2)
  dark = (gray < 80).sum(axis=1)
  # Find text bands
  bands = []
  in_run = False; s = 0
  for i, v in enumerate(dark):
      if v > 5 and not in_run: in_run = True; s = i
      elif v <= 5 and in_run:
          in_run = False
          if i - s >= 2: bands.append((s, i))
  # Detect collisions
  for idx, (s, e) in enumerate(bands):
      cols = (gray[s:e] < 80).any(axis=0)
      nz = np.where(cols)[0]
      if len(nz) == 0: continue
      if idx + 1 < len(bands):
          s2, e2 = bands[idx+1]
          cols2 = (gray[s2:e2] < 80).any(axis=0)
          nz2 = np.where(cols2)[0]
          gap = s2 - e
          if gap < 4 and (max(0, min(nz[-1], nz2[-1]) - max(nz[0], nz2[0])) > 30):
              print(f"COLLISION: y={s}-{e} vs y={s2}-{e2}")
  ```

  False-positive rate: some "collisions" are multi-line label
  sub-bands (e.g. "AUDIENCE\nESTIMÉE (K)" rendered on two lines).
  Treat any positive as a *candidate* — crop the region and
  vision-analyze the crop to confirm. This scan caught the
  chart-6 Apps.éducation/legend collision in seconds; vision
  missed it entirely.

- **(2026-06-27, 30-day world briefing) Vision will confidently
  describe a full-width text layout as "narrow vertical column on
  the left" when the grid layout is visually dense.** The page had
  10 numbered items spanning the full 174mm content width; vision
  returned "narrow column on the left side... the rest of the page
  is wide/empty space." pdftotext + pixel-audit both confirmed
  full-width horizontal paragraphs. **Fix:** when vision reports a
  layout problem, always cross-check with `pdftotext -layout` and a
  PIL pixel-density scan *before* believing it. The decision rule:

  ```bash
  # 1. Extract text with positioning
  pdftotext -layout briefing.pdf -

  # 2. Pixel density per row
  python3 -c "
  from PIL import Image; import numpy as np
  img = np.array(Image.open('preview-N.png').convert('L'))
  # column of ink-density per column, to detect narrow-column layouts
  ink = (img < 200).any(axis=0)
  ink_left = ink[:ink.size//2].sum()
  ink_right = ink[ink.size//2:].sum()
  print(f'left-half ink columns: {ink_left}/{ink.size//2}')
  print(f'right-half ink columns: {ink_right}/{ink.size//2}')
  print(f'ratio: {ink_left/ink_right:.2f} (1.0 = balanced)')
  "
  ```

  A ratio near 1.0 = full-width text; a ratio >>1 = genuine narrow
  column. Don't trust vision's "narrow column" claim without this
  check.
  colored markers via flood-fill.

## When the user reports a layout bug (post-delivery feedback loop)

The first delivery is rarely the final one. Thomas reports
issues like "labels overlap" or "blank space between sections"
or "chart cut off on the right". The fix loop has a strict
order — follow it or you will waste a render cycle chasing
the wrong thing.

### 1. Identify the page first

Ask which page or chart is affected. If Thomas sent a
screenshot, find the page number from the screenshot's footer
("— N / 12 —"). Don't ask "is it page 7?" — pin it from the
screenshot before you start.

### 2. Re-render to PNG and check the file, not the PDF

```bash
pdftoppm -r 110 briefing.pdf check -png -f N -l N
```

Inspect the PNG via PIL pixel sampling first, vision second.
Pixel sample the suspected region:

```python
import numpy as np
from PIL import Image
arr = np.array(Image.open(f'check-{N:02d}.png'))
# Sample the right 10% of the hero chart region
right_strip = arr[hero_top:hero_bot, -100:, :3]
print('right-strip mean:', right_strip.mean())
# If ~250 (cream paper) — no chart content there, it's cut off
# If ~50-100 (dark) — chart is rendering but overflowing
```

### 3. Vision-audit only after pixel evidence

Vision is reliable for *which labels are colliding* but
unreliable for *whether* they collide (it hallucinates both
"labels overlap" on clean charts and "no overlap" on
colliding ones). Use vision to **list candidate labels** in
the broken region, then verify with pixel analysis:

- For label-on-label overlap: crop the suspect region, run
  OCR or just count text-pixel rows vs background rows in
  narrow vertical bands. Adjacent bands with text rows at the
  same y = collision.
- For chart width overflow: `PIL.Image.open(chart_path).size[0]`
  vs `pdf_page_width_px` (909 for A4 at 110dpi). If chart >
  page width, you have a confirmed overflow regardless of
  what vision says.
- For source-line collision: sample the row band at y =
  `chart_height * 0.93-0.97`. If there are text pixels in
  both the source position and the x-tick position on the
  same y-band, confirmed collision.

### 4. Fix in the right place

Three common landing sites, in order of frequency:

1. **The chart PNG itself** — too wide, bad label placement,
   wrong aspect ratio. Fix in `src/make_charts.py`, regenerate
   the PNG, then re-render the PDF.
2. **The HTML container** — `max-width`, padding, the `.card`
   or `.callout` wrapper. Fix in `briefing.html`. The HTML
   will only catch a PNG that's *slightly* over — chromium
   `--print-to-pdf` does NOT respect `max-width` on images,
   so for genuine overflow you must resize the PNG.
3. **The CSS in the template** — affects all pages that use
   the same class. Fix in `templates/briefing.html` AND
   `briefing.html` (they diverge over time — check both).

### 5. Re-render and re-audit the EXACT page

Don't re-render the whole document if you only changed one
chart. But for delivery, always re-run the full `pdfinfo |
pdfimages -list | pdftotext` trio — a chart regen can break
the image embed count.

### 6. Update this skill with the new pattern

If the bug class is new, add a pitfall to the layout-density
sections above AND a one-line entry to
`references/anthropic-ipo-briefing-2026-06-10.md` (or the
relevant worked example) with the symptom → diagnosis → fix
trilogy. The pitfalls list is the agent's institutional
memory; the worked-example file is the session's audit log.

## What you do NOT need anymore (2026-06-27)

The old pre-delivery audit script (`scripts/audit_layout.py`)
and the per-chart width checker (`scripts/chart_width_check.py`)
were removed. They existed to catch bug classes that came from
forced page boxes:

1. **Bottom-blank % per page** — gone because no fixed-height
   page boxes means no orphan halves or 90%-blank pages.
2. **Chart marker overlap** — still possible at the chart
   level; catch it with `pdftoppm` + `vision_analyze` on a
   single chart PNG before embedding.
3. **Image embed count** — `pdfimages -list` is the check
   (covered in verification trio above).
4. **Body column width** — gone because no grid-`1fr` collapse
   inside `@page { margin: 0 }` containers (we don't use those
   containers anymore).

If you find yourself writing a pixel-density script or a
bottom-blank detector for a briefing: stop and re-read
"The single most important rule" at the top of this file.

## Chart-width hard rule (still in force)

Chromium `--print-to-pdf` does NOT respect CSS `max-width: 100%`
on images for PDF output. Charts wider than the page content
width will overflow the right edge of the PDF regardless of
the CSS. **Hard rule for every chart PNG before PDF render:**
width MUST be ≤ 870px (allowing ~39px slack for
`bbox_inches='tight'` crop on A4 with 18mm margins). Add this
assertion at the end of `make_charts.py`:

```python
from PIL import Image
for p in chart_paths.values():
    w, h = Image.open(p).size
    assert w <= 870, f"{p} is {w}px wide (max 870px)"
```

### Vision-hallucination reality check (2026-06-27)

Vision said the page-2 list of the 30-day briefing was "in a
narrow left column" — turned out vision was **right that
time** (the `display: grid; grid-template-columns: 12mm 1fr`
inside `@page { margin: 0 }` collapses to ~50px in chromium
`--print-to-pdf`; pixel audit confirmed 78–136px ink width).
Vision was wrong earlier in the same session when it said
"labels overlap" on a clean chart (chart 04) — flood-fill
proved no overlap. **Rule:** treat vision as a hypothesis
generator, never as ground truth. Always run the pixel audit
before delivery, and when vision contradicts the audit,
*re-run the audit* before trusting vision. The audit is the
ground truth; vision gets to vote, not decide.

## What a good briefing looks like (structural template)

A research briefing that reads as institutional-quality has these
sections, in this order:

1. **Cover** — cream paper, large display title, drop-cap lede,
   3-stat KPI triptych, prepared-date line, sources line,
   disclaimer in 7pt grey. Keep the cover visually dense.
2. **TOC + Executive summary** — TOC with 8-10 items; exec
   summary that fits on one page in a "lede" callout box, then
   a "verdict" box with the actual call.
3. **What it is** — segment by segment, 1-2 paragraphs each,
   with the key numbers inline.
4. **The real numbers** — full income statement, segment
   chart, capex chart, balance sheet snapshot.
5. **Valuation** — 3-5 price scenarios, implied multiples
   chart, "how to think about the multiple" callout.
6. **Capital structure & ownership** — dual-class reality,
   dilution items, ownership split chart.
7. **Growth story** — 2-3 horizons (near/mid/long).
8. **Top 10 risks** — heatmap chart + ranked table with
   severity.
9. **Why now** — strategic logic of the timing.
10. **My view & what I'd watch** — week 1, month 1/3/6/12
    catalysts.
11. **Appendix** — sources, methodology, uncertainty
    disclosures.

That's 12 pages minimum, 17-20 pages typical. Don't pad to hit
a page count; don't cut to hit a tighter count.

## Charts that work (and what doesn't)

These chart types render reliably at 9×4.2 inches with the
soft-modern palette:

- **Stacked bars by period** (revenue by segment over time)
- **Dual-axis bars+line** (subscribers on left axis, ARPU on
  right axis)
- **Grouped bars** (segment data by year)
- **Stacked horizontal stacked bar** (capex by segment)
- **Vertical bar scenarios** (price/valuation scenarios with
  reference lines for peers)
- **Numbered-marker scatter** (risk heatmap with side legend)
- **Grouped horizontal bars** (ownership / voting split)
- **Donut / ring chart** (CSS conic-gradient, not matplotlib
  pie — see `templates/briefing.html` for the pattern)

What doesn't work:
- Pie charts (always look amateur; use horizontal bars instead)
- 3D anything (never)
- More than 5 series on a single axis (cluttered)
- Charts without explicit data labels on the bars

**Palette discipline (soft-modern):** use `--ink` (near-black)
for the primary series, `--accent` (terracotta) for the
emphasis / delta / latest, and one of `--gold/--olive/--plum/
--slate` for context series. Never use the same accent for
more than one purpose on a chart. Source line in
`--ink-faint` italic 7pt at the very bottom — separated from
x-tick labels by `subplots_adjust(bottom=0.22)`.

## Source code patterns (re-runnable, for the next briefing)

The three scripts you need:

1. **Pull** — `curl` with a real User-Agent. ~5 lines.
2. **Extract** — Python script that downloads the PDF, runs
   `pdftotext -layout`, greps the structured fields. ~50 lines.
3. **Charts + HTML + PDF** — one Python file that uses
   matplotlib for charts, writes a single HTML by copying the
   template and substituting content, and shells out to Chrome
   for the PDF. ~500 lines for a 17-page briefing.

Keep all three in a single working directory (e.g.
`~/Desktop/<topic>-briefing/`) so the next session can re-run
with new data. Include the source HTML in the deliverable so
Thomas can re-style if he wants.

## Edge cases

- **The source is a single PDF** (not a webpage). `pdftotext
  -layout` is your friend; without `-layout` the columns get
  smashed together.
- **The source is an HTML S-1 filing from EDGAR.** The 12MB
  main document is HTML, not a PDF. Pull the index file first,
  find the most recent S-1/A's accession number, then `curl`
  the `*d.htm` main document. Parse with a tiny `HTMLParser`
  subclass that strips tags but preserves block-level newlines.
  Grep the section headers (`PROSPECTUS SUMMARY`, `RISK
  FACTORS`, `MD&A`, `BUSINESS`) to find the byte ranges.
  **Verified 2026-06-08 on SpaceX S-1/A No. 2**: 12MB → 1.5M
  chars → 12 section files in ~3s. Don't try to load the whole
  thing into an LLM context — it's too big and the structure
  gets lost. Grep > LLM for this stage.
- **The source is an interactive dashboard** (e.g. EDGAR's
  filing browser). Pull the JSON endpoints (e.g.
  `https://data.sec.gov/submissions/CIK<padded>.json`).
- **The source is a press release with no financial detail.**
  Use the S-1/prospectus for the numbers, the press release for
  the framing. Cite both.
- **The company is rumored / announced to IPO but has NOT yet
  filed a public S-1** (e.g. Anthropic, June 2026: confidential
  S-1 filed with SEC per Axios, but not on EDGAR). This is
  recurring for any "deep research on [unicorn] IPO" task in
  2026. **Do not refuse, and do not fabricate.** The pattern:
  (1) Confirm via EDGAR full-text search that no public S-1
  exists — `efts.sec.gov/LATEST/search-index?q=%22<name>%22
  &forms=S-1`. Expect 0 hits from the company itself. (2) Pull
  the company's own press releases for round/valuation
  disclosures. Try URL patterns like
  `<company>.com/news/series-h`, `/news`, `/press`. (3) Pull
  Wikipedia, Reuters, CNBC, Bloomberg, NYT, Axios for
  everything else. (4) Build the briefing and **flag clearly
  on the cover and in the methodology section that the S-1 is
  confidential / not yet public**. Worked example:
  `references/anthropic-ipo-briefing-2026-06-10.md`.

## Related skills

- `deep-research-obsidian` — for vault-style research (500+
  pages, interconnected notes) rather than a single PDF
- `fast-research-digest` — for real-time market commentary
  via HN/Algolia
- `web-design-guidance` — for design-system-level UI review
  (not for PDF briefing layout specifically)
- `html-to-telegram` — for sending HTML content to Thomas
  on Telegram
- `sandy` — for deterministic replay of a multi-step
  research workflow

## Support files in this skill

- `templates/briefing.html` — the default 12-page template in
  the soft-modern data journal aesthetic. Copy and edit for
  each new briefing. All design tokens in `:root`; the
  chart `<img>` slots are clearly commented.
- `references/anthropic-ipo-briefing-2026-06-10.md` — worked
  example of building an Anthropic briefing in this template
  from scratch (source pull, chart generation, HTML
  assembly, audit). Has the bug → fix log for the two
  recurring chart-geometry defects: mixed-size stacked bar
  labels (side-callout table pattern) and chart-width
  overflow (chromium ignores `max-width` on images).
  **Note:** the worked example still references
  `scripts/audit_layout.py` in its pre-delivery verification
  block. That file is no longer shipped with this skill
  (removed 2026-06-27 with the single-flow pagination
  migration). Use the `pdfinfo` + `pdfimages -list` +
  `pdftotext` trio in the "Verification trio" section above
  instead.
- `references/spacex-ipo-briefing-2026-06-08.md` — worked
  example from the first briefing (S-1/A extraction, EU
  prospectus, 17-page output, navy+gold design — predecessor
  to the current default).
- `references/cahier-dictees-briefing-2026-07-10.md` — worked
  example for a French ed-tech market brief: 9 pages → 10 pages
  fix cycle, the orphan-header bug on dense sections,
  heading-glue CSS pattern, source pull methodology. **Iteration 3
  (added 2026-07-10, same session)** documents the chart-level
  label collisions Thomas flagged post-delivery: 5 of 6 charts
  had at least one collision (chart 5 P-badges in y-tick band,
  chart 6 Apps.éducation over the legend, chart 4 milestones
  flush against x-tick labels). Plus the verification recipe that
  actually caught them — the PIL pixel-band scan, since vision
  failed repeatedly on chart-level layout. **Add this to the
  bug → fix log:** the `break-after: avoid` on h2 alone is
  insufficient when section content density forces an internal
  page break — needs the bidirectional heading-glue pattern
  (h* + p { break-before: avoid }) PLUS the section-level rule
  (`section.spread { break-before: page }`) for dense sections.
- `references/matplotlib-label-collision.md` — the
  side-callout table pattern for stacked bars with
  mixed-size segments, plus the chart-width overflow diagnosis
  flow.
- `references/design-system.md` — full token list, type
  pairing rationale, visual grammar.
- `references/single-flow-pagination.md` — the working
  template and chromium flags for the new pattern. Read this
  before rendering any briefing PDF.
- `references/break-avoid-patterns.md` — when and how to
  apply `break-after: avoid`, `break-before: avoid`, and
  `page-break-inside: avoid` for section headers, end-strips,
  and other "glue" elements. **Companion to bug #8 and bug
  #9 in `devops/chromium-pdf-layout-pitfalls`.** Note: the
  patterns here are necessary but not sufficient for dense
  sections — also apply the section-level `break-before: page`
  rule when content + folio won't fit one page.
- `scripts/audit_layout.py` — RETIRED 2026-06-27. The audit
  layer was a band-aid for fixed-height page boxes that left
  orphan halves and bottom-blank sections. With the
  single-flow pagination pattern (`page-break-inside: avoid`
  on charts, no per-section `height: 297mm; overflow: hidden`
  boxes, plus `break-after: avoid` on `.section-head` and
  `break-before: avoid` on `.end-strip`), the browser
  paginates correctly and the audit's job is done by the
  browser. The file may still be on disk as a fossil; if you
  see other skills calling it, replace those calls with
  the `pdfinfo` + `pdfimages -list` + `pdftotext` trio.
  Don't reintroduce the script.ic
