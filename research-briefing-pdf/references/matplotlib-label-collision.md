# Matplotlib Chart Label Collision — Decision Tree

When a chart's labels overlap (each other, axes, source lines, or run off the page), there are only a handful of robust fixes. Pick by chart type. Verified across 8+ charts in the Anthropic IPO briefing build (2026-06-09/10).

## The five robust fixes

### 1. Numbered markers + side legend table

**When:** scatter heatmap or dense grid with >8 points where inline text labels collide.

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

## Decision tree

```
Label collision in chart?
│
├── Inline labels overlap (heatmaps, scatter with 8+ points)
│   └─→ Fix 1: numbered markers + side legend
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
└── Chart overflows page edge in PDF
    └─→ Fix 5: regenerate at native page width (no CSS will save you)
```

## Anti-patterns (do not do)

- **`ax.text(..., transform=ax.transAxes, ...)` for notes on log-scale axes** — the transform lands at the wrong place because log-scale axis units are non-linear. Use `fig.text` outside the axes or a side legend.

- **Long inline text labels in dense grids** — guaranteed to collide. The text width is non-negotiable; the only fix is to remove the inline label and reference a legend.

- **2-line x-tick labels** ("Anthropic\n(Series H, May 2026)") — tick labels are at the bottom of the chart, two lines means the source line collides with line 2. Shorten the tick label, put the detail in the chart subtitle or a footnote.

- **Trusting vision model output for spatial layout** — vision hallucinated "65% blank" and "garbled text" on actual-fineline charts in the briefing build. Use `pdftotext`, `pdfimages -list`, and pixel-counting instead. Vision is fine for "is there a chart here at all" but unreliable for "is the bottom 15% blank."

## Verification

Before declaring a chart done, render it into the PDF and check the actual pixels:

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
