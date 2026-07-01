---
name: pdf-briefing-recipe
description: How to produce a 30-day research briefing PDF from engine output — story-heavy, single-flow pagination, multi-source pitfalls, chromium print gotchas.
version: "1.0.0"
---

# PDF briefing recipe — `scripts/briefing.py --engine-out`

## User preference (story-heavy, ~5 pages)

When the user asks for a "30-day report", "briefing", "research digest", or "what's happening in X", they want **narrative** (story bodies, top-comment quotes, per-source read) over charts and bar rankings.

Default render:
- 10 headlines with 1-line meta + 240-char body excerpt
- 4 in-depth cards with 480-char body excerpt + top-comment quote pulled from `metadata.top_comments[0].body`
- Per-source narrative blocks (5–7 of them, ~15mm each)
- 3 charts total: themes (vertical bar) + source-mix (stacked horizontal) + scatter
- Adaptive "what the data says" synthesis paragraph (reads `theme_of()` + source counts)
- Caveats + end-strip

Drop these unless explicitly requested: top-10 bar chart, timeline chart. They are stat-heavy and steal vertical space from prose.

Default target: **5 pages at A4** with `@page { size: A4; margin: 18mm 18mm 16mm 18mm; }`. If the user names a page count, hit it — shrink `.source-narrative` padding and depth-card gap first, not the chart figsize.

## Multi-source plan schema — REQUIRED to light up non-Reddit sources

Reddit is always on. TikTok/Instagram/YouTube/Polymarket/GitHub return 0 unless the plan and source-specific flags are populated. **The plan is NOT a list of subreddits** — it's a per-source query map:

```json
{
  "queries": {
    "reddit":     ["GPT-5", "Claude 4", "..."],
    "hackernews": ["GPT-5", "OpenAI", "..."],
    "youtube":    ["GPT-5 release", "AI news this week", "..."],
    "tiktok":     ["AI", "ChatGPT", "humanoidrobot", "..."],
    "instagram":  ["AI", "ChatGPT", "..."],
    "github":     ["openai/openai-python", "anthropics/claude-code", "..."],
    "polymarket": ["GPT-5 release", "AGI by 2027", "..."]
  }
}
```

Each key is optional but missing = empty source. Also pass source-specific creator/hashtag/repo flags:

- `--subreddits=MachineLearning,LocalLLaMA,ChatGPT,...`
- `--tiktok-creators=OpenAI,AnthropicAI,GoogleAI,...`
- `--ig-creators=openai,anthropicai,googleai,...`
- `--github-repo=openai/openai-python,anthropics/claude-code,...`
- `--polymarket-keywords=GPT,AGI,AI,chip`

Verify with `python3 scripts/last30days.py --diagnose` and check `available_sources`. SCRAPECREATORS_API_KEY unlocks TikTok + Instagram; `yt-dlp` on PATH unlocks YouTube; `gh` or `GITHUB_TOKEN` unlocks GitHub.

## Pitfalls baked into `briefing.py` (read before editing)

### 1. Engine JSON shape → `load_from_engine()`
The dump's `items_by_source` dict has per-source engagement shapes:
- Reddit/YouTube/HN: `engagement.{score,num_comments}`
- GitHub: `engagement.{comments,reactions}` — `score` is reactions
- TikTok/Instagram: `engagement.{likes,views,shares,comments}` — synthesize score from likes

`load_from_engine()` already normalizes all of these into `{title, score, time, comments, url, source, body, quote}`. Don't reimplement per-source parsing in new code — call the helper.

### 2. `body` field has a title echo
Many sources return `body = "{title}\n{actual body}"`. Strip the leading line if it equals the title. Also strip `"None"` / `"null"` literal bodies that some Reddit scrapers return.

### 3. Top-comment quote
Pull from `metadata.top_comments[0].body` (or `.text`). Trim to 280 chars. Not every item has a quote — wrap with `{f'<div class="quote">…</div>' if quote else ''}`.

### 4. CHART_FIGSIZE = (8.5, 3.0)
Wide+short aspect for full-width stacked charts. At A4 content width (~170mm) rendered height is ~33mm instead of ~60mm at the old (6.4, 4.0) default. Fits one chart per page instead of pushing to next page.

### 5. `.cols > div { flex:1 1 0; min-width:0 }` collapses charts in print
Chromium `--print-to-pdf` interprets flex 1fr + min-width:0 as 0 width — chart images inside disappear. Two fixes:
- **Stack vertically** (preferred for §02 themes/source-mix): drop the `<div class="cols">` wrapper, render two full-width `.card` blocks.
- **Explicit width**: replace `flex:1 1 0; min-width:0` with `width:calc(50% - 4mm); flex:0 0 auto`.

### 6. f-string CSS escaping
When editing CSS inside an f-string in `build_html()`, every `{` and `}` in CSS must be escaped as `{{` `}}`. The CSS for `.depth-card`, `.source-narrative`, `.pullquote`, `.cols`, `.card` is all inside one big f-string — lose the escaping and Chromium sees broken CSS.

### 7. `--allow-file-access-from-files` chromium flag
Required so `file://` chart PNGs load under `--headless --print-to-pdf`. Already passed by `render_pdf()`. Don't remove it.

### 8. Audit tmp dir not cleaned
`/home/thames/.hermes/skills/research-briefing-pdf/scripts/audit_layout.py` writes PNGs to `/tmp/audit_layout_<stem>/` and doesn't clear it between calls. If the PDF shrinks from N pages to N-1, stale `page-N.png` remains and the audit reads phantom pages. Always `rm -rf /tmp/audit_layout_*` before re-running the audit on a regenerated PDF.

## Section template (default 5-page layout)

| § | Page | Content |
|---|------|---------|
| Cover | 1 | brand strip + h1.display + lede + 3 KPIs + headlines 01–02 |
| §01 headlines | 1–2 | 10 items, body excerpts |
| §02 shape | 3 | themes chart + source-mix chart (stacked, full-width) |
| Pullquote | 3 | adaptive 2-sentence synthesis |
| §03 depth | 3–4 | 4 story cards with body + quote |
| §04 by source | 4–5 | per-source narrative grid |
| §05 takeaways | 5 | scatter chart + adaptive analysis + caveats + end-strip |

If user wants N pages, scale §03 depth-cards count and §04 narrative count, not chart figsize.

## Story-heavy "what the data says" template

Adaptive — reads actual sources + themes. NOT hardcoded "chip race / IP suit" copy:

```python
def what_the_data_says(stories, kpis):
    src_counts = ...; themes = ...
    top_theme = max(themes) ; top2 = sorted(themes)[:2]
    top_src = source_label(max(src_counts))
    return (
        f"The 30-day window is dominated by <strong>{top_theme}</strong>"
        + (f" paired with <strong>{top2[1]}</strong>" if len(top2)>1 else "")
        + f" across {kpis['total']} posts from {len(src_counts)} sources. "
        + f"<strong>{top_src}</strong> carried the loudest single signal "
        + f"(top score: {kpis['top_score']:,})."
        + " The most-discussed thread is where readers pushed back hardest — "
        + "the consensus split, which is usually where the next quarter's "
        + "product decisions get made."
    )
```

## Render command

```bash
python3.14 ~/.hermes/skills/research/last30days/scripts/briefing.py \
  --engine-out /tmp/engine-out.json \
  --output ~/Desktop/last30days-<slug>-<date>.pdf
```

`python3.14` (not `python3`) — system `python3` is 3.11; briefing needs 3.12+ for the matplotlib aggregator syntax.