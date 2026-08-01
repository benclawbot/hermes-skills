# Cahier de Dictées market brief — worked example (2026-07-10)

French ed-tech market research PDF for a sister-built web app
(Cahier de Dictées). 10-page output, soft-modern data journal
aesthetic, 6 matplotlib charts. Produced on the first delivery
after one bug-fix iteration.

This file logs the bug → fix cycle that's now embedded as a
pitfall in the parent SKILL.md.

## The deliverable

- `cahier-dictees-briefing.pdf` — 10 pages, 444KB
- Source: 15+ competitor sites + Wikipedia + Play Store
- Sections: cover + 9 (verdict, paysage, concurrents,
  positionnement, SWOT+océan bleu, marché, GTM, risques, annexes)
- Charts: market segments, positioning scatter, feature depth,
  GTM timeline, channels, blue-ocean matrix

## The bug → fix cycle

### Iteration 1 (9 pages)

First render came out at 9 pages with single-flow pagination
(no `break-before: page` on sections). Layout was
*mostly* clean, but page 6 had a defect:

```
PAGE 6
  TOP: § 06 / MARCHÉ ADRESSABLE
  ...
  [chart + caption + callout]
  ...
  BOTTOM: § 07 / PLAN GO-TO-MARKET   <-- ORPHAN HEADER
```

The §07 section header sat at the bottom of page 6 with its
content (the two GTM charts) on page 7. Classic orphan
heading from the layout-density pitfall list.

`break-after: avoid` on h2 alone was insufficient because the
section content density forced a page break *inside* the
section's content area, not at the heading.

### Iteration 2 (10 pages, fixed)

Two changes:

1. Added `section.spread { break-before: page }` so each
   major section gets its own page. Eliminates orphan headers
   at the cost of +1 page. The rule was paired with
   `section.cover { break-before: page }` so the cover stays
   page 1.

2. Added `h1, h2, h3, h4 { break-inside: avoid }` and
   `h* + p, h* + .lede, h* + .callout { break-before: avoid }`
   as belt-and-suspenders. Even if a section ever splits
   across pages again, the heading stays glued to its first
   paragraph.

3. §08 (risques + 10-item action list + callout) overflowed
   by ~60mm. Two fixes:
   - Tightened `ol.numbered > li` padding from 2.5mm to 1.8mm.
   - Tightened `.callout` padding from 3mm to 2.5mm.
   - Tightened `.folio` margin-top from 8mm to 6mm.
   - Cut the action list from 10 items to 8 (items 9-10 were
     the Instagram/TikTok accounts and the bilan 90j — kept in
     a follow-up list elsewhere, less critical).

Result: 10 pages, every section on its own page, no orphan
headers, no empty trailing pages.

## Verification trio used

```bash
pdfinfo cahier-dictees-briefing.pdf | grep -E "Pages|File size|Title"
# Pages: 10, File size: 444451, Title: Cahier de Dictées — Étude de marché & Go-To-Market

pdfimages -list cahier-dictees-briefing.pdf | head
# 6 chart embeds confirmed, 813-847px wide each (under 870px limit)

pdftotext -layout cahier-dictees-briefing.pdf - | awk -v RS="\f" \
  'NR>1 {print "P"NR": "substr($0,1,80)}'
# Confirmed: P1 = cover, P2-P10 = one section per page, no orphan headers
```

Vision-analyze called on pages 5 and 8 (chart-heavy pages)
to confirm visual layout. Vision was reliable here because
the questions were qualitative ("are both charts fully
visible?") not absolute ("is the bottom 30% blank?").

## New CSS pattern: the heading-glue rule

This is the canonical "no orphan headings" CSS block now in
the briefing template:

```css
/* Headings stay glued to the following paragraph.
   break-after: avoid alone leaves the heading on the bottom
   of page N and its paragraph on top of N+1 — ugly. Pairing
   with break-before: avoid on the first child fixes that. */
h1, h2, h3, h4 {
  break-after: avoid;
  page-break-after: avoid;
  break-inside: avoid;
}
h1 + p, h1 + .lede, h1 + .callout,
h2 + p, h2 + .lede, h2 + .callout,
h3 + p,
h4 + p {
  break-before: avoid;
  page-break-before: avoid;
}
```

Plus the section-level rule for clean breaks:

```css
/* Each spread section starts on its own page. Prevents
   orphan section headers stuck at bottom of previous page
   when section content density forces an internal break. */
section.spread {
  break-before: page;
  page-break-before: always;
}
section.cover {
  break-before: page;
  page-break-before: always;
}
```

The cost is +1 page per dense section. The benefit is zero
orphan headings and zero near-empty trailing pages.

## Reference data sources (raw HTML in research/raw/)

- Beneylu (`beneylu.com`, 59KB) — confirmed Beneylu School
  Infini is positioned as a 3000-resource subscription
  catalogue adopted by Académie de Créteil.
- Projet Voltaire (`projet-voltaire.fr`, 296KB) — confirmed
  B2B/B2C pricing, CPF eligibility, CE1+ modules.
- Edumoov (`edumoov.com`, 61KB) — confirmed freemium trial
  model (Edulivret 2 mois, Educartable 2 mois, Edujournal
  1 mois). RGPD/CNIL mentioned. Pricing post-trial behind
  paywall (lacune).
- Génération 5 (`generation5.fr`, 87KB) — confirmed CHF 6.40
  pricing on "Meilleur en Orthographe" Play Store app.
- Bout de Gomme via Wayback (375KB) — confirmed Vanessa
  Cheutin's blog as the #1 French primary teacher influenceur
  with massive orthographe content (CE1-CM2) and JOCATOP
  publishing partnership.
- Cartable Fantastique (`cartablefantastique.fr`, 106KB) —
  niche dyspraxia adaptation association; not direct competitor.
- L'Escapadou (`lescapadou.com`, 251KB) — 700K app sales to
  schools; kids-facing spelling apps, not teacher tool.
- Apps.éducation (`portail.apps.education.fr`) — confirmed
  SPA architecture (every URL returns the same 32KB shell);
  catalogue exhaustiveness impossible without API access.

## Sources NOT accessible (lacunes)

- laclassenumerique.fr — domain appears to be HS since ~2023
- Bout de Gomme internal pages — Wayback Machine snapshots
  mostly redirect
- Charivari internal pages — same
- Edumoov pricing — post-login paywall
- Sialle / education.gouv.fr — bot protection blocks curl

All lacunes documented in the briefing's annex section so
the reader sees the methodology limits.

## Iteration 3 (chart-level label collisions, post-delivery)

After delivery, Thomas flagged that the 6 matplotlib charts
in the briefing still had label collisions in multiple
places. The Hermes viewer showed chart 6 specifically:
"Apps.éducation" label overlapping the size legend ("Fort"
item) in the lower-left. **Iteration 2 fixed the orphan
header in the PDF, but the *charts themselves* still had
layout bugs the page-level CSS could not catch.**

### What was wrong

| Chart | Bug | Source |
|-------|-----|--------|
| 01 segments | "120K" label past the right edge of the largest bar at the value-label offset | value at `v+2` too close to `set_xlim(0, 145)` |
| 02 positioning | 3 bubble labels (SuperOrtho, L'Escapadou, Génération 5) all at the same y-band stacked on top of each other | textbook `xytext=(0, 14)` for every bubble |
| 04 timeline | milestone callouts at `y=-0.6` crashed into the x-tick labels at `y=0` | no bbox, no y-limit headroom |
| 05 channels | "P1"-"P11" priority badges at `x=-25` (negative gutter) collided with the y-tick label band | badge in same x-band as tick text |
| 06 blueocean | "Apps.éducation" label (offset `(-14, +14)`) over the lower-left legend ("Fort" item) | annotation and legend sharing a corner |

Chart 3 (feature depth grouped bars) was clean.

### What fixed it

The fix script is the same for all five — open `make_charts.py`
and apply defensive patterns:

1. **Chart 2** — per-name `(dx, dy, ha)` offset dict (see
   `references/matplotlib-label-collision.md` Fix 6), paper-color
   bbox backplate on every label, `set_ylim(-0.1, 1.7)` for top
   labels, `figsize=(7, 4.6)` for height headroom.
2. **Chart 4** — wrap milestone `ax.text` in
   `bbox=dict(boxstyle='round,pad=0.25', fc=PAPER, ec='INK_FAINT',
   lw=0.4, alpha=0.9)`, increase `set_ylim(-1.6, ...)`.
3. **Chart 5** — move priority badges *inside* bars at `x=2` with
   `color=PAPER` (paper-on-bar). Drop `set_xlim` negative gutter.
   Wrap right-side value labels in paper-color bbox.
4. **Chart 6** — push "Apps.éducation" label up-right
   (`(14, 18, 'left')`) instead of `(-14, 14)`. Apply the same
   offset-dict pattern as chart 2 to all 7 products. Add leader
   lines (`arrowprops=dict(arrowstyle='-', color=INK_FAINT,
   lw=0.5, alpha=0.6)`) for clarity.

### How I verified (pixel-band scan, not vision)

Vision was unreliable here. Across 4 vision-analyze calls on
chart 6, vision returned "User Safety: safe" twice, generic
thumbnail descriptions twice, and never named the actual
collision. The fix that worked: a 30-line Python snippet that
loads the chart PNG with PIL, finds rows with > 5 dark pixels
(text bands), and flags any two adjacent bands whose vertical
gap is < 4px AND horizontal x-overlap > 30px. Caught the
chart-6 Apps.éducation collision in seconds. Full recipe
in the SKILL.md "Vision-model unreliability" section, dated
2026-07-10.

### Lesson

Layout-density pitfalls apply to charts too, not just to
the HTML. The original `make_charts.py` had the textbook
patterns (`xytext=(0, 14)`, `v+offset` bar labels, negative-
gutter badges) that look fine in isolation but collide when
multiple patterns are stacked on the same axes. The fix is
defensive — paper-color bboxes on every annotation,
per-element offset dicts, never rely on `(-dx, +dy)` for
labels in corners where legends live.

Three new pitfalls added to SKILL.md (matplotlib section,
2026-07-10):
- "Bar value labels + priority badges collide with y-tick labels"
- "Annotation labels collide with legends sharing the same corner"
- "Bottom-of-axis callouts sit flush against x-tick labels"

Plus a verification recipe (pixel-band scan) added to the
Vision-model unreliability section, since vision was the
weakest link on this bug class.