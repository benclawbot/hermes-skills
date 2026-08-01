---
name: chromium-pdf-layout-pitfalls
version: "1.4.0"
description: "Verified chromium headless layout bugs and fixes - PDF briefs with thin charts or orphan pages, plus viewport-width --screenshot verification for static pages and SPAs at mobile / tablet / desktop."
category: devops
---

# Chromium `--print-to-pdf` layout pitfalls

Verified 2026-06-27 on Linux + headless Chromium 1223 (Playwright build at `~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome`). These are real bugs that have shipped. Apply BEFORE rendering, not after.

## The 9 bugs (and their fixes)

### 1. Chart bar labels become unreadable in narrow columns
**Symptom:** Matplotlib bar chart renders OK standalone; in the printed PDF, the bars are "extremely thin, almost invisible" and y-axis text is "cut off or improperly aligned" (vision's verdict on the 2026-06-27 AI/tech briefing).

**Root cause:** Chart PNG is sized for full page width (~175mm at A4 with 18mm margins). When placed in a flex/grid `flex:1 1 0; min-width:0` column with `width:100%` on the `<img>`, the chart scales down to half-width. At 110dpi, the half-width column is ~370px. Original 8pt font renders at ~4pt — illegible.

**Fix (column context, side-by-side):** Render the chart at a larger figsize (7.2×4.5 inches instead of 6.4×4.0) with fontsize 9–10 for y-axis labels, 8.5 for tick labels, 8 for the footer. Cut title length to ~42 chars. The taller figsize + bigger fonts scale down more gracefully.

**Fix (full-width stacked, 2026-06-27):** When charts are stacked vertically as full-width cards (one per `page-break-inside: avoid` unit), use a **wide+short aspect (8.5×3.0 inches)** instead. The shorter height (~33mm at 110dpi vs ~106mm for 6.4×4.0) lets two stacked charts fit on the same page or one chart fit alongside the next section's header. The horizontal aspect gives plenty of width for category labels at 9pt without scaling artifacts. This is the inverse of bug #1's column context — same root cause (font-size-at-rendered-size), opposite fix direction (taller for narrow columns, shorter for full-width).

### 2. Page 3 ends with 40%+ empty bottom (orphan-half bug)
**Symptom:** `pdfinfo` shows 3 pages, but `pdftoppm` of page 3 shows the content stops at y≈70% with the bottom 30% blank. Vision reads it as "unfinished" or "missing chart". The user sees a thin, padded-out last page.

**Root cause:** Single-flow pagination works, but if the last section's content (2 charts + caveats + end-strip) fits in the top 2/3 of the page, the browser doesn't redistribute. Single-flow doesn't mean "fill every pixel" — it means "let the browser decide page boundaries."

**Fix:** Add an analysis paragraph that fills the bottom third of the last page. Don't let the page end with a small content block + vast empty space. Pair this with `audit_layout.py` to catch regressions.

### 3. `pdfimages -list` parser misses embedded images
**Symptom:** Audit script reports "no chart images embedded" while `pdfimages` actually returns 4 PNGs.

**Root cause:** `pdfimages -list` lines start with whitespace (the page column is padded). Naive `line[0].isdigit()` filters the header line correctly but misses whitespace-prefixed data rows.

**Fix:** Use `line.lstrip().split()[0].isdigit()` to detect data rows. Document this in the audit script.

### 4. Chromium silently drops `file://` chart references in `--print-to-pdf`
**Symptom:** HTML has `<img src="file:///tmp/charts/01.png">`; chart titles render as text but the chart images are blank rectangles. No error in stderr.

**Root cause:** Chromium's `--print-to-pdf` blocks `file://` reads by default since 2022 for security.

**Fix:** Add `--allow-file-access-from-files` to the chromium command. Without it, the PDF is technically valid but visually broken.

### 5. CSS `::first-letter` drop-cap renders unreliably in print
**Symptom:** Drop-cap floats incorrectly; first character appears on the previous line; text wraps around it in pdftotext-flattened output.

**Root cause:** Chromium's print pipeline doesn't fully support `float` + `::first-letter` in `--print-to-pdf`. The CSS standard says it should work; chromium's print rendering is inconsistent.

**Fix:** Don't use CSS drop-cap in print-stylesheet briefs. The accent lives on the `<h1>` (`<em>` for emphasis) instead.

### 6. `.cols > div { flex:1 1 0; min-width:0 }` collapses chart images to zero width
**Symptom:** Two charts sit side-by-side in a flex container; both have valid `src=` paths and load fine when viewed in a browser, but in the printed PDF one or both chart images are blank rectangles (the `<img>` box is 0×0). `pdfimages -list` shows fewer images than `<img>` tags in the HTML.

**Root cause:** Chromium `--print-to-pdf` interprets `flex:1 1 0` + `min-width:0` inside a `display:flex` parent as zero intrinsic width. The `<img>` inside with `width:100%` collapses to 0. Browser screen render is fine; print pipeline is not.

**Fix (two options):**
1. **Stack vertically** (preferred for full-width briefs): drop the `<div class="cols">` wrapper and render each chart as its own full-width `.card`. Each card has `page-break-inside: avoid` and pagination handles them individually.
2. **Explicit width on the flex item**: replace `flex:1 1 0; min-width:0` with `width:calc(50% - 4mm); flex:0 0 auto`. The explicit width survives the print pipeline.

**Detect:** Run `pdfimages -list` and count images vs `<img>` tags in the rendered HTML. Mismatch = this bug.

### 7. `audit_layout.py` tmp dir not cleaned between calls — phantom pages
**Symptom:** Audit reports 6 pages when `pdfinfo` says 5. Or: audit fails page-N/5 with 100% blank when N is past the actual page count.

**Root cause:** `scripts/audit_layout.py` writes page PNGs to `/tmp/audit_layout_<stem>/` and never clears the directory between calls. If a previous run produced more pages than the current PDF (e.g., shrunk from 6 to 5 after a layout fix), the stale `page-6.png` is still there and gets counted.

**Fix:** `rm -rf /tmp/audit_layout_*` before re-running the audit on a regenerated PDF. Or patch `render_pages()` in `audit_layout.py` to `shutil.rmtree(tmp, ignore_errors=True)` at entry.

### 8. Section-head orphans at the bottom of a page
**Symptom (2026-06-27, last30days world briefing):** `§ 02 / shape of the conversation` header landed at the bottom of page 2 alone, with the first chart caption ("STORIES BY THEME") immediately below it. Page 3 then starts with the second chart's caption ("WHERE EACH SOURCE SPENT ITS ATTENTION") orphaned at the top with no header context. The section-head visually separates from its content because of how chromium splits a `.section-head` + `<hr>` + `.card` sequence.

**Root cause:** Without `break-after: avoid` on `.section-head`, chromium treats the header as a small standalone unit and is happy to push it to the end of a page even when its first content (the chart card) is on the next page.

**Fix:** Add `break-after: avoid; page-break-after: avoid;` to `.section-head`. This tells chromium "don't break right after me — keep me with my following content." The header now stays glued to its first card.

```css
.section-head {
  /* ... existing layout ... */
  break-after: avoid;
  page-break-after: avoid;
}
```

**Detect:** Look for a section header at the bottom of one page with the section's first content (chart, table, list) on the next page. `pdftotext -layout` is the right tool — the layout output shows the section name and first content on adjacent page boundaries.

### 9. End-of-document strip pushed to its own blank page
**Symptom (2026-06-27, last30days world briefing):** The final document strip (`ACCENT / BASELINE / END · 30D · 2026-06-27`) ended up alone on page 6 of a 5-page intended document, with a 100% blank page 6 tripping the audit. The prior section (§ 06 forward-look cards) filled page 5 to its last available row, and the end-strip got pushed past the bottom margin.

**Root cause:** Two failure modes. (a) Without `page-break-inside: avoid` on the end-strip, chromium splits it as a normal flex row; (b) without `break-before: avoid`, the strip is treated as a new page-eligible unit and moves with whatever overflow happens upstream.

**Fix (both at once):**

```css
.end-strip {
  /* ... existing layout ... */
  page-break-inside: avoid;       /* don't split the strip itself */
  break-before: avoid;            /* don't push it to a new page */
  break-after: avoid;             /* don't push past to another new page */
}
```

**Generalization:** Any document footer / colophon / final-credit row that should ALWAYS appear with the last content block needs all three: `page-break-inside: avoid` (don't split), `break-before: avoid` (stay with prior content), `break-after: avoid` (don't claim a new page). Apply the same triple to `.colophon`, `.credits-final`, `.appendix-footer` and similar.

**Detect:** `pdfinfo` shows N+1 pages when the design intends N. The (N+1)th page has only one or two thin lines of text at the top (the orphan strip) with vast empty space below.

## The single-flow pagination principle

**Old (broken):** N fixed-height `.page` boxes, each `width:210mm; height:297mm; box-sizing:border-box; padding:18mm; page-break-after:always`. The browser paginates but each section can overflow → truncated content + orphan-half pages → requires an audit layer.

**New (correct):** One continuous HTML body. Sections flow with normal CSS layout. `page-break-inside: avoid` on charts keeps them intact. The browser handles pagination. No audit needed for layout *itself*, only for the bug class above (orphan-half on last page, missing chart embeds).

## Lean audit: what to check, what to skip

Keep this small. Don't reintroduce a full pixel-audit layer.

`scripts/audit_layout.py` should check exactly two things:
1. **Last page bottom-blank %** — orphan-half bug detection. Threshold: >40% blank in bottom 30% = FAIL. Sample every 4th pixel (still 100k+ samples).
2. **Chart embeds via `pdfimages -list`** — missing chart bug detection. Threshold: 0 images = FAIL.

Skip these (they were the audit's false-positive noise):
- Bottom-blank % on non-last pages (legitimate editorial whitespace)
- Marker overlap via flood-fill (vision is unreliable here; chart font fix solves the real case)
- Body-column-width (single-flow eliminates the grid-`1fr` collapse)

## Verification commands

After every PDF render:
```bash
pdfinfo output.pdf | grep Pages        # expected: 3
pdfimages -list output.pdf | head      # expected: N image rows
pdftotext -layout output.pdf - | head  # spot-check text flow
pdftoppm -r 110 output.pdf /tmp/preview -png  # render for vision check
```

If audit fails, look at the page that flagged, not the whole PDF.

## Bonus: headless `--screenshot` for viewport-width responsive verification

Same chromium binary, different mode. Use when verifying a static page or SPA renders correctly at mobile/tablet/desktop widths. Verified 2026-07-13 on Linux + Chromium 142 snap at `/snap/bin/chromium`.

Full recipes: see `references/headless-screenshot-verification.md` (4-viewport capture loop, sandbox output gotchas, screenshotting every tab of a pure-state SPA, and the vision_analyze reliability notes).

### The single most common responsive bug: inline `grid-template-columns` overrides media queries

A page can have 18 beautifully-tuned `@media` rules and still break on mobile because a template-literal-rendered div has `<div class="grid" style="grid-template-columns:1fr 1fr">` — inline styles beat class rules. The CSS audit looks perfect. The phone is broken. **Source-audit alone is insufficient; viewport screenshots are mandatory.**

**Fix pattern:** extract the hardcoded grid to a class, give the class a media query.

```css
.reports-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:700px){.reports-grid{grid-template-columns:1fr!important;gap:14px}}
```

### The 4-viewport screenshot recipe

```bash
# Each capture needs a unique --user-data-dir to avoid lock contention
# Use --virtual-time-budget=4000 so JS SPAs have time to render
# Window height = target + slack (1500px) so the full page is captured

for spec in "360x800" "390x844" "414x896" "768x1024"; do
  IFS=x read w h <<< "$spec"
  chromium --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --user-data-dir=/tmp/cr-prof-$spec \
    --window-size=$w,$((h+1500)) --virtual-time-budget=4000 \
    --screenshot=${spec}.png "http://localhost:8765/index.html" 2>/dev/null
done
```

### Sandbox gotchas

- **Output path:** `--screenshot=path.png` honors CWD, not the literal path in some confined environments. If the file is reported "written" but `ls` can't find it, write to a non-`/tmp` path (e.g. `~/shots/`) or `cd` into the target dir before invoking.
- **Unique `--user-data-dir` per invocation** — concurrent or sequential runs without it can collide. Pattern: `/tmp/cr-prof-<unique-id>`.
- **Single-page-app screenshots need `--virtual-time-budget=4000+`** — chromium screenshots before JS render completes otherwise. The 130KB JS bundle in the 2026-07-13 case required 4 seconds.

### Screenshotting every tab of a JS SPA without DevTools

Pure-state SPAs (no hash routing) can't be deep-linked. Cheap workaround: copy the source, swap the initial-state declaration, render each variant.

```python
import shutil, os
src = 'index.html'
work = '/tmp/work'
os.makedirs(work, exist_ok=True)
for tab in ['home', 'students', 'reports', 'settings']:
    dst = os.path.join(work, f'{tab}.html')
    shutil.copy(src, dst)
    with open(dst) as f: html = f.read()
    # Only patch the FIRST occurrence (the declaration site)
    html = html.replace("let currentPage='home'", f"let currentPage='{tab}'", 1)
    with open(dst, 'w') as f: f.write(html)
    # then run chromium --screenshot="file:///tmp/work/{tab}.html"
```

### Verify across every tab, not just home

If a SPA has a sidebar/nav with multiple tabs (`.page` elements or route views), the home page is usually the simplest layout — bugs hide in the more complex tabs. The 2026-07-13 `cahier-de-dictees` audit found zero mobile issues on home/students/dictations/entry/settings, and a clear overflow on **reports** (a 2-column `.grid` that ignored media queries). Always screenshot ≥1 non-home tab.

### Vision feedback loop is noisy

`vision_analyze` on screenshot PNGs sometimes returns `{"analysis": "User Safety: safe"}` with no actual description, with no error. Retry once or two before changing strategy; don't conclude the page is broken based on empty vision output alone. If 2 retries are empty, trust the source audit + `grep` for known bad patterns (inline `grid-template-columns`, `width:max-content` without overflow handling) instead of looping on vision.
