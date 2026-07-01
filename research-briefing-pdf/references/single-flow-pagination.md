# Single-flow pagination (the right way to render a multi-page PDF)

Lesson from 2026-06-27: the original briefing template used
`<section class="page">` boxes with `width:210mm; height:297mm;
page-break-after:always` for each section. This caused a chain of
phantom bugs that needed an audit layer to detect. Thomas's
correction:

> "instead of trading the bottom of the page isn't empty, isn't it
> easier that the text is continuous with no page break from one
> section to the next? That's a lot of testing done just to produce
> a simple PDF"

The fix is structural, not cosmetic. Use one continuous HTML
document; let the browser paginate; add `page-break-inside: avoid`
to elements that shouldn't split across pages.

## The pattern

```css
/* Page setup: use the @page margin; do NOT wrap content in fixed boxes */
@page { size: A4; margin: 18mm 18mm 16mm 18mm; }

html, body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: <serif>;
  font-size: 10.5pt;
  line-height: 1.5;
}

/* Elements that must NOT split across pages */
img.chart, table, .callout, .pullquote, ol.lede-list li {
  page-break-inside: avoid;
  break-inside: avoid;
}

/* NO class="page" wrapper. NO height: 297mm. NO overflow: hidden. */
/* NO page-break-before/after on every h2. */
```

That's it. The browser handles everything else.

## HTML structure (continuous flow)

```html
<!-- COVER (first content block, not a page box) -->
<section class="cover">
  <h1 class="display">Title</h1>
  <p class="lede">Lede paragraph with drop cap...</p>
  <div class="hero-figure">...KPI cards...</div>
</section>

<!-- Each "section" is just a content block, no page wrapper -->
<div class="section-head">
  <h2>Ten stories that defined the month.</h2>
</div>
<hr class="hair">
<ol class="lede-list">
  <li>...</li>
</ol>

<div class="section-head">
  <h2>What dominated, and when it peaked.</h2>
</div>
<div class="cols">
  <div><img class="chart" src="..."></div>
  <div><img class="chart" src="..."></div>
</div>

<div class="pullquote">
  <blockquote>...</blockquote>
</div>

<!-- ...more sections, no page wrappers... -->
```

## Chromium flags required (verified 2026-06-27)

```bash
chrome \
  --headless \
  --disable-gpu \
  --no-sandbox \
  --hide-scrollbars \
  --no-pdf-header-footer \
  --allow-file-access-from-files \    # WITHOUT this, chart <img> tags render as blank rectangles
  --print-to-pdf=output.pdf \
  file:///path/to/briefing.html
```

| Flag | Why |
|---|---|
| `--allow-file-access-from-files` | Lets `<img src="file:///tmp/charts/...">` embed. Without it, the PDF has the chart title text but the chart image is empty. **Hard requirement for any briefing that embeds local PNGs.** |
| `--no-pdf-header-footer` | Strips chromium's default date/url footer. |
| `--hide-scrollbars` | Prevents scrollbars appearing in screenshots you might take for QA. |

**Use Chrome for Testing** (`~/.cache/ms-playwright/chromium-<rev>/chrome-linux64/chrome`),
NOT `/snap/bin/chromium`. Snap lies about file writes.

## Still required (the rules that survive single-flow pagination)

1. **Chart width ≤ 870px** before rendering. Chromium ignores
   `max-width: 100%` on images in `--print-to-pdf`. Generate the
   PNG at the right width.
2. **Flexbox not CSS Grid** for 2-column list items. Grid
   `1fr` collapses inside `@page { margin: 0 }` containers —
   even though we no longer use that container pattern, the
   flexbox pitfall remains valid for any list layout that has
   counter-styled margin content.
3. **`page-break-inside: avoid` on charts, tables, callouts,
   pullquotes, list items.** Without this, a chart at the bottom
   of a page will be split with the top half on one page and the
   bottom half on the next.
4. **`pdfinfo` + `pdfimages -list` + `pdftotext -layout`**
   verification trio before delivery. These catch real bugs
   (missing chart embeds, wrong page count, content present but
   not visible) that vision hallucinates around.

## When the cover needs to look different

A common need: the cover should be visually distinct (large
display title, drop cap, hero-figure triptych) from the
interior pages. Don't wrap it in a `.page` box. Instead:

```css
.cover {
  border-bottom: 0.5pt solid var(--rule);
  padding-bottom: 8mm;
  margin-bottom: 8mm;
}
.cover h1.display {
  font-size: 38pt;
  /* ... */
}
```

The `.cover` is just a `<section>` with a bottom border; the
browser may or may not break the page after it depending on
content. That's fine — the cover is its own visual unit and
the user doesn't care if interior content flows immediately
after or starts on the next page.

## When you still need a forced break

For a deliberate "executive summary on page 2, deep dive on
pages 3+" pattern, force ONE break:

```css
.section-head:first-of-type {
  page-break-before: always;  /* explicitly start major content on a new page */
}
```

Don't put `page-break-before: always` on every section. The
bug-class comes from putting it on every section, not from
ever using it.

## Sanity check

After rendering, check:

```bash
pdfinfo output.pdf | grep Pages           # Should match your design
pdfimages -list output.pdf | wc -l        # Should be (charts + 1 header row) minimum
pdftotext -layout output.pdf - | head    # First page should be the cover, not a blank
```

Don't add: bottom-blank %, body-column-width, marker-overlap
flood-fills. The browser gets these right when the structure
is right.