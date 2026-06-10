# Worked example: SpaceX (SPCX) IPO Briefing, 2026-06-08

A real session that produced a 17-page PDF briefing on the SpaceX
IPO from a 12MB S-1/A + EU prospectus + FWP interview transcript.

## Source acquisition

```bash
# 1. Find the CIK
curl -sL -A "Hermes Research research@hermes.local" \
  https://www.sec.gov/files/company_tickers.json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); \
    [print(v) for k,v in d.items() \
     if 'space' in v['title'].lower() and 'exploration' in v['title'].lower()]"
# -> {'cik_str': 1181412, 'ticker': 'SPCX', ...}

# 2. List filings
CIK=1181412
curl -sL -A "..." "https://data.sec.gov/submissions/CIK${CIK}.json" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
    [print(f'{r[\"filingDate\"]} {r[\"form\"]} {r[\"accessionNumber\"]} {r[\"primaryDocument\"]}') \
     for r in zip(d['filings']['recent']['filingDate'], \
                  d['filings']['recent']['form'], \
                  d['filings']['recent']['accessionNumber'], \
                  d['filings']['recent']['primaryDocument'])]"

# 3. Pull the S-1/A Amendment No. 2 (most current preliminary)
ACC=0001628280-26-040364
ACC_NO_DASH=$(echo $ACC | tr -d '-')
curl -sL -A "..." \
  "https://www.sec.gov/Archives/edgar/data/${CIK}/${ACC_NO_DASH}/spaceexplorationtechnologib.htm" \
  -o /tmp/spacex-ipo/s1/spaceexplorationtechnologib.htm
# 12MB main document
```

## Extraction

The S-1 is HTML, not a PDF, so `pdftotext` doesn't apply. A tiny
`HTMLParser` subclass strips tags and keeps newlines at block
boundaries. Output is ~1.5M chars, 28K lines, indexed by
section name. 12 major sections extracted to separate files
(summary, risk_factors, use_of_proceeds, capitalization, dilution,
mda, business, management, etc.).

For the briefing, the key sections were:
- L773–2460: PROSPECTUS SUMMARY (the executive summary + headline
  numbers)
- L2460–4515: RISK FACTORS (2055 lines, 204KB)
- L4999–9074: MD&A (financial discussion)
- L9074–12644: BUSINESS (segment detail)

Key numbers extracted via grep:
- Q1 2026 revenue: $4,694M total ($619M Space, $3,257M Connectivity, $818M AI)
- FY 2025 revenue: $18,674M (49.8% YoY Connectivity growth)
- Starlink: 10.3M subs Q1'26, $66 ARPU, 164 countries
- Capex FY25: $20,737M (Space $3.8B, Connectivity $4.2B, AI $12.7B)
- Anthropic: $1.25B/month through May 2029, 90-day exit
- Cursor option: $60B equity, ~444M shares dilutive
- 13,076M total shares post-IPO → ~$1.77T at $135

## Charts (8 total)

1. **Revenue by segment** — disclosure-anchored bars for FY25 + Q1'26
   (skipped FY23/FY24 because segment splits weren't in the summary)
2. **Starlink subscribers + ARPU** — dual-axis bars+line, showing
   4.5× subscriber growth + 33% ARPU decline in 27 months
3. **Segment Adjusted EBITDA** — grouped bars FY23/FY24/FY25
4. **Capex by segment** — Q1'26 + FY25 grouped bars
5. **Implied equity value scenarios** — vertical bars for $100-$200
6. **Risk heatmap** — scatter with likelihood × impact
7. **Ownership / voting** — grouped horizontal bars (Class A vs B)
8. **Implied multiples** — grouped bars (EV/Rev + EV/EBITDA at
   each price scenario) with reference lines for Palantir and
   CrowdStrike

## HTML rendering

The HTML was a single self-contained file with embedded CSS. Key
choices:
- `@page { size: A4; margin: 18mm 16mm; }` for the right page size
- `@page :first { ... }` to suppress headers/footers on the cover
- `display: table` for grids (NOT flexbox — flexbox is flaky in
  headless Chrome's print engine)
- Charts as `<img class="chart" src="file:///tmp/spacex-ipo/charts/01_...">`
  with absolute file:// paths
- Color-coded callouts: `.callout`, `.callout-red`, `.callout-green`,
  `.verdict` (dark navy box for the final call)
- Tables as `<table class="data">` with `<thead>` for navy headers,
  alternating row backgrounds via CSS

## PDF rendering

```bash
CHROME=~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome
$CHROME --headless --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --print-to-pdf=/tmp/spacex_ipo_briefing.pdf \
  --no-pdf-header-footer \
  --virtual-time-budget=15000 \
  file:///tmp/briefing.html
```

8 pages of layout-only first → 17 pages after charts embedded.
243KB → 855KB jump confirms the chart PNGs were actually written
into the PDF.

## Verification

```bash
pdfinfo /tmp/spacex_ipo_briefing.pdf | grep -E "Pages|File size"
# -> Pages: 17, File size: 855513 bytes

pdfimages -list /tmp/spacex_ipo_briefing.pdf | head
# -> 8 large image entries (1284-1578px wide, ~50-100KB each) + 1-2 small
#    ones (the bullet characters in the Lede summary)

pdftotext /tmp/spacex_ipo_briefing.pdf - | grep -c "10.3M\|555,555,555\|88.5%\|1.77T"
# -> 4 matches (all key numbers present)

pdftoppm -png -r 90 -f 1 -l 1 /tmp/spacex_ipo_briefing.pdf /tmp/preview
# Then vision_analyze on the PNG
```

The vision model caught a "13.076M" typo on the cover (should have
been "13,076M"). Fixed and re-rendered before delivery.

## Output location

```
~/Desktop/spacex-ipo/
├── spacex_ipo_briefing.pdf     (17 pages, 855KB)
├── briefing.html               (source, 45KB)
├── make_charts.py              (re-runnable when S-1 numbers update)
└── charts/                     (8 PNGs, 92-125KB each)
```

## Lessons from this specific run

1. **The S-1's segment data table was the single highest-value
   source** — it had the exact FY25/Q1'26 segment splits plus the
   Starlink subscriber/ARPU trajectory. Without it, the briefing
   would have had to estimate segment splits from MD&A prose.
2. **The EU prospectus revealed the $162 max price** (vs US
   $135 expected). Critical for the "price scenarios" chart.
3. **The Dimon-Musk interview transcript** gave qualitative
   context that the S-1 didn't (the "we need capital for
   that" quote, the Starship cost-per-launch claim, the Terra
   Fab motivation). Worth reading even though it wasn't
   financial.
4. **The class structure is the most important governance fact.**
   88.5% Class B voting = permanent 5-15% governance discount.
   Called out in the briefing as a separate risk + the verdict
   section.
5. **The Cursor $60B option is more material than the S-1
   makes it look.** 444M shares + $10B in termination fees if
   SpaceX walks. The market will price this optionality over
   time. Worth its own callout.
