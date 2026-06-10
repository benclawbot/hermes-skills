# Anthropic IPO Briefing — 2026-06-10 (worked example)

Built the Anthropic pre-IPO research briefing in the
`research-briefing-pdf` template. Final: 12 pages, 8 charts,
533KB, `~/Desktop/anthropic_ipo_briefing_2026-06-10.pdf`.

## Source pull (no public S-1 exists)

- **EDGAR full-text search** (`efts.sec.gov`): zero S-1s from
  Anthropic PBC. Confirmed via Axios (Jun 1 2026) that the
  filing is confidential.
- **Anthropic PR pages**: pulled Series H announcement for the
  $965B post-money / $65B raised / $47B run-rate / 11.5 GW
  compute / $15B hyperscaler commitments.
- **Wikipedia "Anthropic"**: founding, board, round history,
  Pentagon timeline, Project Panama copyright suit.
- **News**: Reuters, NYT (Sorkin), Axios, CNBC.

## Design

Soft-modern data journal (the default in the template). Cream
paper, terracotta accent, Iowan Old Style + JetBrains Mono.
12 sections, 8 charts, 12 pages.

## Charts (matplotlib, soft-modern palette)

| # | File | Type | Notes |
|---|------|------|-------|
| 01 | `01_cumulative_equity.png` | Vertical bars, log y | Series A through H, $124M → $123B |
| 02 | `02_runrate.png` | Vertical bars, $ values | Q1 2024 → May 2026 run-rate ramp |
| 03 | `03_ipo_scenarios.png` | Vertical bars | 15x/20x/25x/Series H scenarios |
| 04 | `04_risk_heatmap.png` | Numbered-marker scatter | 12 risks in 5×5 likelihood×severity grid |
| 05 | `05_ownership.png` | Stacked horizontal bar | 32% / 48% / 12% / 8% split (see bug 1 below) |
| 06 | `06_compute.png` | Vertical bars | 4 compute partners, 11.5 GW total |
| 07 | `07_peers.png` | Vertical bars, log y | Frontier-AI lab valuations |
| 08 | `08_timeline.png` | Horizontal timeline | 13 funding events, 2021→2026 (see bug 2 below) |

## Bug log (two recurring chart-geometry defects)

### Bug 1: Stacked horizontal bar — small-segment label collision

**Symptom** (user-reported from screenshot of page 6): the
"Compute partners 12%" and "Employees & advisors 8%" labels
were colliding horizontally into "Compute partEmployees &
advisors".

**First fix attempted** (insufficient): leader lines from
each small segment down to its label at the segment's x-center.
Labels at x=68 (12% center) and x=88 (8% center) — close enough
that the long label strings still overlapped.

**Second fix (correct)**: side-callout table.
1. Draw leader lines from each small segment down to a common
   y-row (y = -0.85).
2. Place text labels at **fixed, evenly-spaced x positions**
   (e.g. 58 and 78) regardless of segment center.
3. Two-row label per slot: name on top (italic serif), value
   below (mono, color-matched to the segment).

**Pattern**: when two small labels are close in x AND the
label strings are long enough to touch, decouple label x
position from segment x position. The side-callout is robust
because label spacing is now a function of the available
horizontal space, not the segment geometry.

### Bug 2: Chart width overflow on chromium `--print-to-pdf`

**Symptom**: the funding timeline chart on page 11 had the
"Series H · $65B" label clipped at the right edge of the page.

**Diagnosis**: the chart PNG was 1125px wide; page content is
909px at 110dpi. Despite HTML having `width:100%; max-width:100%`
on `.callout img.chart`, the rightmost label was cut off.

**Root cause**: chromium's `--print-to-pdf` does NOT respect
CSS `max-width` on images. It scales the page to fit, so an
oversized image simply runs off the page boundary.

**Fix**: regenerate the chart at native page width.
- Old figsize: 7.5×3.0 inches → 1125×450px at 150dpi
- New figsize: 6.6×2.6 inches → 990×390px at 150dpi (saves
  with `bbox_inches='tight'`, ends up ~1002×399 actual px,
  fits within 909px content)

**Verification before re-render**:
```python
from PIL import Image
assert Image.open('charts/08_timeline.png').size[0] < 909
```

**Generalization**: every chart that goes in a `.callout` or
`.card` div must be sized to fit the page natively. Don't
rely on CSS to scale it down. Run the PIL assertion on every
chart before each render.

## Audit trail (vision-hallucination events)

- Vision said page 11 "Series H · $65B" was clipped — TRUE.
  Verified by pixel sample of right strip showing cream paper
  pixels where the label should be.
- Vision said page 6 labels were overlapping — TRUE. Verified
  by direct re-render of just chart 05.
- Vision said chart 04 "labels overlap markers" on first
  audit — FALSE. The numbered markers were geometrically
  distinct (flood-fill verification confirmed 12/12 markers,
  0 close pairs). Vision was hallucinating because the chart
  is visually dense.
- Vision said page 4 was "35-40% blank" — FALSE. It was
  showing the natural page footer margin. Pixel audit
  confirmed bottom-30% band was 92% paper-background, the
  expected 16mm margin.

## Pre-delivery verification (run for every deliverable)

```bash
pdfinfo ~/Desktop/anthropic_ipo_briefing_2026-06-10.pdf \
    | grep -E "Pages|File size"
# → Pages: 12, File size: 533K

pdfimages -list ~/Desktop/anthropic_ipo_briefing_2026-06-10.pdf \
    | head
# → 8 large PNGs, 990-1830px wide

pdftotext ~/Desktop/anthropic_ipo_briefing_2026-06-10.pdf - \
    | grep -E "965B|47B|11.5 GW|Pentagon"
# → All key facts present

python ~/.hermes/skills/research-briefing-pdf/scripts/audit_layout.py \
    ~/Desktop/anthropic_ipo_briefing_2026-06-10.pdf \
    ~/anthropic-briefing/charts/
# → No chart marker collisions, all images embedded, all
#   page widths within bounds
```

## What I'd do differently next time

- **Resize every chart to native page width from the start.**
  Add the PIL assertion to `make_charts.py` as a final
  pre-step. Catches the overflow before render.
- **Side-callout table for any stacked bar with > 2 small
  segments from the start.** Don't try inline leader lines
  first; the table pattern always works.
- **Run `scripts/audit_layout.py` BEFORE the user ever sees
  the PDF.** The pixel audit catches things vision misses
  and avoids the "first delivery, second pass" cycle.
