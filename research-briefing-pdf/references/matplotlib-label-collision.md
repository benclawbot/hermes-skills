# Matplotlib Chart Label Collision — Decision Tree

When a chart's labels overlap (each other, axes, source lines, or run off the page), there are only a handful of robust fixes. Pick by chart type. Verified across 8+ charts in the Anthropic IPO briefing build (2026-06-09/10) and the Cahier de Dictées briefing (2026-07-10).

## The seven robust fixes

### 1. Numbered markers + side legend table

**When:** scatter heatmap or dense grid with **>12 points** where inline text labels collide (unmaintainable past 12 — see Fix 6 for the 5–12 range).

```python
# Plot points as circles with numbers
for i, (x, y, name) in enumerate(risks, start=1):
    ax.scatter([x], [y], s=120, color=color_for_severity(i), zorder=3)
    ax.text(x, y, str(i), ha='center', va='center', fontsize=8,
            color='white', weight='bold', zorder=4)

# Render legend as a separate text block below the figure or in HTML
```

**Why it works:** removes ALL inline label text from the chart area. Numbers are unambiguous; the legend can be wider than the chart.

### 2. Side-callout table (stacked bar with small segments)

**When:** stacked horizontal bar where a few segments are too small for in-bar text (e.g. 12% and 8% next to each other — labels collide as "Compute partEmployees").

```python
# Draw leader lines from each small segment down to a common y-row
for cx, label, pct in small_label_positions:
    ax.plot([cx, cx], [0, -0.85], color=INK_FAINT, linewidth=0.4, clip_on=False)

# Place text at FIXED, evenly-spaced x positions (NOT the segment center)
# This decouples label position from segment position.
ax.text(58, -0.95, 'Compute partners', ha='center', va='top', ...)
ax.text(58, -1.12, '12%', ha='center', va='top', ...)
ax.text(78, -0.95, 'Employees & advisors', ha='center', va='top', ...)
ax.text(78, -1.12, '8%', ha='center', va='top', ...)
```

**Why it works:** even when segments are close in x, fixed label positions prevent horizontal collision. Decoupling is the key.

### 3. In-bar for large, leader-line-down for small

**When:** stacked horizontal bar with mixed sizes (32%, 48% + 12%, 8%).

```python
for label, pct, color in segments:
    cx = cum + pct/2
    if pct >= 15:
        # Large — fits in bar, white centered text
        ax.text(cx, 0, f'{label}\n{pct}%', ha='center', va='center',
                color=PAPER, weight='bold', fontsize=8.5)
    else:
        # Small — leader line down to a label below
        ax.plot([cx, cx], [0, -0.45], color=INK_FAINT, linewidth=0.4, clip_on=False)
        ax.text(cx, -0.55, label, ha='center', va='top', fontsize=7.5)
        ax.text(cx, -0.78, f'{pct}%', ha='center', va='top', fontsize=7)
    cum += pct
```

**Why it works:** the 15% threshold is empirical — text at fontsize 7-8 fits comfortably in segments ≥15% wide.

### 4. Source line in a reserved bottom margin

**When:** the `fig.text(0.01, 0.005, ...)` source attribution collides with x-axis tick labels under `bbox_inches='tight'`.

```python
# WRONG — source at y=0.005 sits in the same band as the x-tick labels
fig.text(0.01, 0.005, 'Source: ...', ...)

# RIGHT — reserve bottom space, then place source in that margin
fig.subplots_adjust(bottom=0.22, left=0.07, right=0.97, top=0.90)
fig.text(0.01, 0.025, 'Source: ...', ...)
```

**Why it works:** `subplots_adjust(bottom=0.22)` reserves the bottom 22% of the figure for the source line. The x-axis ticks sit above it. Critical for log-scale charts where tick labels are dense.

### 5. Native chart width matches page content width

**When:** a chart PNG is wider than the page content area and overflows the right edge in PDF render.

**Root cause:** Chromium's `--print-to-pdf` does NOT respect CSS `max-width: 100%` on images. The HTML can say `width:100%` and the chart will still overflow.

**Fix:** regenerate the chart at a width that fits the page natively.

```python
# For A4 with 18mm margins, content area is 174mm ≈ 6.8" ≈ 1020px at 150dpi
# At 110dpi (PDF preview), content area is 909px wide
fig, ax = plt.subplots(figsize=(6.6, 2.6))   # narrow figure
fig.subplots_adjust(bottom=0.22, left=0.04, right=0.97, top=0.88)
```

**Verify before render:**
```python
from PIL import Image
img = Image.open('chart.png')
assert img.size[0] <= 909, f"Chart is {img.size[0]}px wide, page is 909px"
```

### 6. Per-name label offset dict + paper-colored bbox (scatter/annotate) — *companion to Fix 1*

**When:** scatter or bubble chart with 5–10 inline labels, where the natural `annotate()` default puts every label *above* its point at `(0, +N)`. When two points share a y-band (e.g. three competitors all at y≈0.3 with x spread 0, 1, 2), the labels stack on top of each other.

**Root cause:** matplotlib `ax.annotate(name, xy, xytext=(0, 14), ha='center')` is the textbook pattern — but it's an "all labels up" assumption. The fix is to give each label a *unique* (dx, dy, ha) tuple from a per-name dict, so they radiate in 8 directions rather than stacking.

```python
# Per-name offset dict: (dx, dy, ha) in points
label_offsets = {
    'Projet Voltaire':               (-10, 22, 'right'),
    "SuperOrthographe\n(Digischool)":(  0, 24, 'center'),
    'Edumoov':                       ( 14, 14, 'left'),
    'Beneylu School':                ( 14, -8, 'left'),
    "Génération 5\n(Meilleur Ortho)":(-12, -16, 'right'),
    "L'Escapadou":                   (-12, 14, 'right'),
    "Bout de Gomme\n(influenceur)":  (  0, 24, 'center'),
    'Cahier de Dictées':             (  0, 20, 'center'),
}
for name, x, y, size, c in competitors:
    ax.scatter(x, y, s=size*5, c=c, alpha=0.85, edgecolors=INK,
               linewidths=0.8, zorder=3)
    dx, dy, ha = label_offsets[name]
    weight = '500' if name == 'Cahier de Dictées' else 'normal'
    ax.annotate(name, (x, y), xytext=(dx, dy),
                textcoords='offset points', ha=ha, va='center',
                fontsize=8, color=INK, weight=weight,
                bbox=dict(boxstyle='round,pad=0.25', fc=PAPER, ec='none', alpha=0.85))
```

**Companion fixes that make this reliable:**

1. **Reserve enough y-range** — high labels at `dy=+24` need `set_ylim(..., top + 0.25)` headroom. Same for left/right at the x edges (`set_xlim(-0.3, ...)` when using `dx=-12`).
2. **Increase figsize height** — `figsize=(7, 4.6)` instead of `(7, 3.8)` to absorb the spread. Don't squeeze y-limits tighter to "fit" — the labels *are* the chart's information density.
3. **The paper-colored bbox** is for **legibility when labels are close, NOT for hiding overlap**. See anti-pattern #4 below.

**Why not the alternatives:**
- *Fix 1 (numbered markers + side legend)* is more robust but adds a side artifact — overkill for ≤10 labels where the user actually wants to *see* the names.
- *Fix 3 (leader-line down)* requires manual y-position math per label and doesn't scale beyond 4-5 points.
- *Just `dy=+14` for everyone* (the default pattern) is the bug. The fix is explicitly per-name.

**Verified:** Cahier de Dictées positioning chart, 2026-07-10 — three competitors in the y≈0.3 band now radiate top/left/right with paper backplates; vision audit confirmed no overlap. Pixel-band scan (y-rows 168, 183, 203, 297, 310, 361, 375, 448) shows 8 distinct label bands, no collisions.

**When to escalate to Fix 1 instead:** if you have >12 labels, the per-name dict becomes a maintenance burden AND the chart becomes unreadable regardless of bbox backplates. Numbered markers + side legend is the right answer past ~12 labels.

### 7. Categorical-axis labels — use the category NAME as the y coordinate, not a numeric index

**When:** `ax.barh(label, ...)` makes the y-axis categorical, then you try to add an in-bar label with `ax.text(cx, 0, ...)` or `ax.text(cx, idx, ...)`. The `0` and `idx` are interpreted as **numeric data coordinates** that map to the FIRST category — so every text() call lands on the top bar, regardless of which bar you intended.

**Symptom (verified 2026-07-10 on Cahier de Dictées Gantt chart):** Vision audit says "Phase 0 shows J+0 → J+14, Phase 1 shows nothing, Phase 2 shows nothing" — the in-bar day labels all stacked on Phase 0 because `ax.text(cx, 0, ...)` was used three times.

**Fix:** pass the category NAME (not a number) as the y coordinate:
```python
for label, start, end, color, sub in phases:
    ax.barh(label, end - start, left=start, color=color, height=0.55, edgecolor='none')
    cx = (start + end) / 2
    ax.text(cx, label, f'J+{start} → J+{end}',   # <-- label, not 0 or idx
            ha='center', va='center', fontsize=10, color=PAPER, weight='bold',
            family='monospace')
```

**Why it works:** matplotlib resolves the string to the matching categorical position. The bar at index 2 gets its text on index 2, not on index 0.

**Companion fix for sub-labels BELOW the bar (instead of in the bar):** use `annotate` with `xytext` offset points so the y-resolution doesn't bite you:
```python
ax.annotate(sub, xy=(cx, label), xytext=(0, -22),
            textcoords='offset points', ha='center', va='top', ...)
```

**Verified:** Cahier de Dictées `04_timeline.png`, 2026-07-10 — three day-range labels now render inside their respective bars; vision audit reads each correctly.

## Decision tree

```
Label collision in chart?
│
├── Inline labels overlap (heatmaps, scatter with 8+ points)
│   ├─→ 8-12 labels: Fix 6 (per-name offset dict + paper bbox)
│   └─→ >12 labels: Fix 1 (numbered markers + side legend)
│
├── Stacked bar with mixed-size segments
│   ├── Segments adjacent AND both small (<15%)
│   │   └─→ Fix 2: side-callout table (fixed x positions)
│   ├── Segments mixed (some ≥15%, some <15%)
│   │   └─→ Fix 3: in-bar for large, leader-line for small
│   └── ALL segments ≥15%
│       └─→ In-bar text works as-is
│
├── Source line collides with x-axis tick labels
│   └─→ Fix 4: subplots_adjust(bottom=0.22+) + source at y=0.025
│
├── Chart overflows page edge in PDF
│   └─→ Fix 5: regenerate at native page width (no CSS will save you)
│
├── In-bar text all stacks on the FIRST row of a categorical barh
│   └─→ Fix 7: use category NAME as y-coordinate, not 0/idx
│
└── Legend dots collide with adjacent labels due to bubble-size scaling
    └─→ Fix 1 side-legend with uniform marker size (Line2D handles)
```

## Anti-patterns (do not do)

- **`ax.text(..., transform=ax.transAxes, ...)` for notes on log-scale axes** — the transform lands at the wrong place because log-scale axis units are non-linear. Use `fig.text` outside the axes or a side legend.

- **Long inline text labels in dense grids** — guaranteed to collide. The text width is non-negotiable; the only fix is to remove the inline label and reference a legend.

- **2-line x-tick labels** ("Anthropic\n(Series H, May 2026)") — tick labels are at the bottom of the chart, two lines means the source line collides with line 2. Shorten the tick label, put the detail in the chart subtitle or a footnote.

- **(2026-07-10) **Bbox backplates to hide label overlap, not separate it.** The instinct when two `ax.annotate()` labels overlap is to add `bbox=dict(boxstyle='round,pad=0.25', fc=PAPER, ec='none', alpha=0.85)` and call it fixed. **It's not fixed** — the bbox just paints a paper-colored box over the colliding text, masking the overlap visually without changing the underlying label positions. Three rounds of "fix" produced three visually-clean charts that were still layout-colliding under the bboxes. **Fix hierarchy:**
  1. First, actually move the labels apart (Fix 1, 2, 6, or 7).
  2. THEN add the bbox for legibility when labels are still close — never as the primary fix.
  3. Verify by checking the source `text()` calls and `(dx, dy, ha)` tuples, not by eye. Pixel-band scan shows you the real overlap even when the bbox hides it.
  
  When the user says "same issue in those 2 examples again" — they are pointing at exactly this anti-pattern. Don't reach for bboxes. Fix the geometry.

- **(2026-07-10) **Trusting vision model output for spatial layout** — vision hallucinated "65% blank" and "garbled text" on actual-fineline charts in the briefing build, AND returned "no overlap" on charts that still had hidden bbox-masked overlap. Use `pdftotext`, `pdfimages -list`, and pixel-counting instead. Vision is fine for "is there a chart here at all" but unreliable for "is the bottom 15% blank" AND for "do these specific N labels overlap when both have paper-colored bboxes over them." Pixel-band scan is the ground truth.

## Verification

Before declaring a chart done, render it into the PDF and check the actual pixels — and inspect the source `text()` calls before declaring geometry clean:

```bash
# Convert PDF to PNGs at 110 dpi (matches typical preview)
pdftoppm -r 110 briefing.pdf check -png -f 11 -l 11  # specific page

# Inspect: load with PIL, check if any region is unexpectedly empty/dense
python3 -c "
from PIL import Image
import numpy as np
img = np.array(Image.open('check-11.png').convert('L'))
# Find dark text regions (low brightness)
dark = (img < 100).sum(axis=1)  # row-wise dark pixel count
print('Rows with >50 dark pixels:', (dark > 50).sum())"
```

If a chart page has long stretches of zero dark pixels in the middle (where the chart should be), labels are probably hidden or the chart didn't render.

**Source-level check (catches what pixel scan can't when bboxes are involved):** scan the `make_charts.py` for every `ax.annotate(...)` and `ax.text(...)` call. For each one, ask: at the given (x, y) data coords + (dx, dy) offset, does the label fall onto a region that already has another label or a shape? The `bbox=` argument in those calls is a *legibility hint*, not a *collision fix*. If two labels' final drawn rectangles overlap, the bbox is hiding it, not fixing it.