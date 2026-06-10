#!/usr/bin/env python3
"""AI News Digest — strict 24h window, no commentary.
Replaces last30days-based digest (which defaulted to 30-day window and produced stale repeats).
"""
import urllib.request, json, time, sys
from datetime import datetime, timezone, timedelta

NOW = datetime.now(timezone.utc)
CUTOFF_TS = int((NOW - timedelta(hours=24)).timestamp())
CUTOFF_ISO = (NOW - timedelta(hours=24)).strftime('%Y-%m-%d')
TODAY = NOW.strftime('%Y-%m-%d')

lines = [f"# 🤖 AI News — last 24h · {TODAY}", ""]

# ── HN ─────────────────────────────────────────────────────────────────────
hn_queries = [
    ("AI+agent", "AI agents"),
    ("LLM+OR+AI+OR+automation", "LLM / AI"),
    ("AI+coding+OR+cursor+OR+claude+OR+gemini", "AI coding"),
]

all_hn = []
seen_hn = set()
for q, _ in hn_queries:
    url = (f"https://hn.algolia.com/api/v1/search?query={q}&tags=story"
           f"&hitsPerPage=15&numericFilters=created_at_i%3E{CUTOFF_TS}")
    req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    for h in data.get("hits", []):
        t = h["title"].lower()
        if t not in seen_hn and len(t) > 10:
            seen_hn.add(t)
            all_hn.append(h)

all_hn.sort(key=lambda h: h.get("points", 0), reverse=True)

if all_hn:
    lines.append("**Hacker News:**")
    for h in all_hn[:12]:
        ts = h.get("created_at_i", 0)
        age_h = (time.time() - ts) / 3600
        pts = h.get("points", 0)
        title = h["title"]
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"
        lines.append(f"• [{title}]({url})")
        lines.append(f"  {age_h:.0f}h · {pts}pts")
    lines.append("")

# ── GitHub (new repos only, 24h window) ───────────────────────────────────
url = (f"https://api.github.com/search/repositories"
       f"?q=AI+OR+agent+OR+LLM+created:{CUTOFF_ISO}..{TODAY}"
       f"&sort=stars&order=desc&per_page=15")
req = urllib.request.Request(url, headers={"User-Agent": "Hermes"})
with urllib.request.urlopen(req, timeout=10) as r:
    gh_data = json.loads(r.read())

gh_repos = gh_data.get("items", [])
if gh_repos:
    lines.append("**GitHub — new today:**")
    for r in gh_repos[:10]:
        stars = r["stargazers_count"]
        desc = r.get("description", "") or ""
        lang = r.get("language", "") or ""
        lines.append(f"• [{r['full_name']} ⭐{stars}]({r['html_url']})")
        if desc:
            lines.append(f"  {desc[:80]}")
        if lang:
            lines.append(f"  {lang}")
    lines.append("")

lines.append(f"*next run tomorrow 06:00 UTC*")
sys.stdout.write("\n".join(lines))