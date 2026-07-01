# CSS break-avoid patterns for chromium `--print-to-pdf`

Companion to bugs #8 and #9 in `devops/chromium-pdf-layout-pitfalls`.

The single-flow pagination pattern (no fixed-height page boxes)
relies on the browser's built-in `page-break-*` and
`break-*` properties to glue related elements together.
Without the right rules, sections orphan to the bottom of
pages and end-strips get pushed to blank trailing pages.

## The three properties (and what each does)

| Property | Meaning | When to use |
|---|---|---|
| `page-break-inside: avoid` | Don't split THIS element across pages | Charts, tables, callouts, pullquotes, list items |
| `break-after: avoid` | Don't break right AFTER this element | Section headers, list items that introduce a block |
| `break-before: avoid` | Don't break right BEFORE this element | End-strips, colophons, "see next page" pointers |
| `page-break-before: always` | ALWAYS break before this element | Use sparingly: only for deliberate "start fresh on page N" |

Both `break-after` (CSS3) and `page-break-after` (CSS2.1)
are recognized by chromium. Use both for forward-compat
with browsers that only support one.

## Canonical patterns

### Section header that must stay with its first content

```css
.section-head {
  /* layout properties */
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin: 6mm 0 4mm 0;
  border-top: 0.5pt solid var(--rule);
  padding-top: 5mm;

  /* glue rules — both forms for compatibility */
  break-after: avoid;
  page-break-after: avoid;
}
```

The header + `<hr class="hair">` + first content card now
travel as a unit. Without this, chromium happily orphans the
header to the bottom of one page while its chart lands at
the top of the next.

### End-of-document strip that must NOT claim its own page

```css
.end-strip {
  /* layout properties */
  display: flex;
  gap: 6mm;
  font-family: "JetBrains Mono", monospace;
  font-size: 7pt;
  border-top: 0.5pt solid var(--rule);
  padding-top: 4mm;
  margin-top: 8mm;

  /* glue rules — all three */
  page-break-inside: avoid;       /* don't split the strip itself */
  break-before: avoid;            /* don't push to a new page */
  break-after: avoid;             /* don't push past to a new page */
}
```

Apply the same triple to `.colophon`, `.credits-final`,
`.appendix-footer`, and any document footer that must
appear with the last content block.

### Grid of cards that should stay together if they all fit

```css
.watch-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 3mm 5mm;
  margin-bottom: 4mm;
  /* Do NOT set page-break-inside: avoid here.
     The whole grid will overflow the page instead of breaking. */
}

.watch-card {
  border-top: 0.5pt solid var(--ink-faint);
  padding-top: 1.5mm;
  /* individual cards CAN break if needed */
}
```

**Gotcha:** setting `page-break-inside: avoid` on a grid
container is dangerous. If the container + remaining content
won't fit on the current page, chromium pushes the whole
container to the next page, even if some of its children
would have fit. Apply `page-break-inside: avoid` to individual
children instead, or to logical sub-groups, never the whole
grid if it's tall.

## Verification flow

After rendering, check pagination in this order:

```bash
# 1. Expected page count
pdfinfo output.pdf | grep Pages

# 2. Section headers + content are not split across pages
pdftotext -layout output.pdf - | grep -B 1 -A 2 "§ 0[1-9]"

# 3. End-strip is on the last page (not alone on a trailing page)
pdftotext -layout output.pdf - | tail -5
```

If `pdftotext` shows a `§ NN` header with a page break before
its content, bug #8 fired. If `pdfinfo` shows N+1 pages and
the last page has only one or two thin lines, bug #9 fired.

## What doesn't work

- `break-inside: avoid` on a grid container (see gotcha above)
- `page-break-after: always` on every `h2` (forces orphan pages — see layout-density pitfalls in the main SKILL.md)
- `min-height: 100%` on section blocks (defeats single-flow pagination)
- Wrapping the whole body in `display: flow-root` thinking it solves pagination (it doesn't)