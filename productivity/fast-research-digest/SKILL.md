---
name: fast-research-digest
description: Lightning-fast AI research digest via HN Algolia API + GitHub API. Strict 24h window by default. Terminal-only, no browser.
version: 2.0.0
---

# Fast Research Digest

Lightning-fast AI research digest via HN Algolia API + GitHub API. Strict 24h window by default. Terminal-only, no browser.

## Strict 24h Filtering (IMPORTANT — default mode)

All queries MUST be limited to the last 24 hours. Without this, HN Algolia returns months-old stories sorted by relevance, making every run identical.

**HN — use `numericFilters` with Unix timestamp:**
```python
from datetime import datetime, timezone, timedelta
cutoff_ts = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())
url = f"https://hn.algolia.com/api/v1/search?query=QUERY&tags=story&hitsPerPage=15&numericFilters=created_at_i%3E{cutoff_ts}"
```
`tags=story` is still required. `numericFilters=created_at_i>{ts}` is the only way to get truly fresh HN data — the API has no natural date filter, default sort is relevance, and without the timestamp filter every run returns the same 30-day pool.

**GitHub — use `created:{yesterday}..{today}` date range:**
```python
cutoff_iso = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime('%Y-%m-%d')
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
url = f"https://api.github.com/search/repositories?q=AI+OR+agent+created:{cutoff_iso}..{today}&sort=stars&order=desc&per_page=15"
```
The two-dot range syntax (`..`) is required. `created:>{cutoff_iso}` alone is not reliable for fresh repo discovery — use the inclusive range.

## Commands

**HN News (strict 24h):**
```bash
python3 -c "
import urllib.request, json, time
from datetime import datetime, timezone, timedelta
cutoff = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())
url = f'https://hn.algolia.com/api/v1/search?query=AI+agent&tags=story&hitsPerPage=15&numericFilters=created_at_i%3E{cutoff}'
with urllib.request.urlopen(url, timeout=10) as r:
    data = json.loads(r.read())
for h in data['hits'][:12]:
    age = (time.time() - h['created_at_i']) / 3600
    print(f'{age:.0f}h | {h.get(\"points\",0)}pts | {h[\"title\"]}')
"
```

**GitHub new repos (strict 24h window):**
```bash
python3 -c "
import urllib.request, json
from datetime import datetime, timezone, timedelta
cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime('%Y-%m-%d')
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
url = f'https://api.github.com/search/repositories?q=AI+OR+agent+created:{cutoff}..{today}&sort=stars&order=desc&per_page=10'
with urllib.request.urlopen(url, timeout=10) as r:
    data = json.load(r.read())
for r in data['items']:
    print(f'[{r[\"full_name\"]}] {r[\"stargazers_count\"]} stars — {r.get(\"description\",\"\")[:60]}')
"
```

---

> **Deprecation note (v1 → v2):** `last30days` was previously used for daily digests but defaults to a 30-day window — every run returns the same stale pool. For truly fresh daily digests, use this skill with the strict 24h filters above. `last30days` is still correct for broad multi-source research without time constraints.

## HN Query Patterns (what actually works)

**Gold standard:** `tags=story` + `numericFilters=created_at_i>{cutoff}` — both always required.

**High-signal query patterns found through research:**
- `AI+agent` — agent news
- `LLM+OR+AI+OR+automation` — LLM/AI broad
- `AI+coding+OR+cursor+OR+claude+OR+gemini` — AI coding tools

**Low-signal / avoid:**
- Generic `AI+tool+2026` — too broad, returns noise
- Queries without `tags=story` — flooded with comments
- `Ask+HN` queries — rarely return structured project info
- Compound queries with 4+ OR terms — HN titles don't use all synonyms; keep to 2-3 terms

## GitHub Query Patterns

**Date ranges:** Use `created:YYYY-MM..YYYY-MM` format (two dots, no spaces).

**Stars range:** `stars:1000..5000` (two dots) — upper bound excludes massive repos, lower bound excludes experiments.

**Combining:** `stars:1000..5000+created:2025-01..2026-05+AI+OR+agent` — works reliably.

**Sorting:** `sort=stars&order=desc` for popularity. `sort=created&order=desc` for newest.

## Output format

Digest delivered to Telegram — compact, inline links only:

**HN — AI Agent News**
• [Title](url) — age · pts

**GitHub — New today**
• [repo ⭐ N](url) — description

No tables. No preamble. No "Top stories" editorial header. Open on the data immediately.

## Script

`scripts/ai-news-digest.py` — self-contained digest generator. Run directly:
```bash
python3 ~/.hermes/skills/productivity/fast-research-digest/scripts/ai-news-digest.py
```
Stdout is the digest. Exit 0 on success. No output = nothing fresh (silent watchdog, no delivery).
