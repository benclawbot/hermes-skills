#!/usr/bin/env python3
"""
last30days HN fallback retriever.

Use this when the engine returns zero items on a "what's happening in the
world / breaking news / current events" topic. Symptoms:
  - Engine logs: "Reddit: 0 threads, YouTube: 0 videos, HN: 0 stories..."
  - RedditPublic 403 forbidden (reddit.com/search.json rate-limits/bans
    headless callers — common on shared egress IPs)
  - No SCRAPECREATORS_API_KEY and no web search backend (BRAVE/EXA/SERPER)
  - Engine's planner LLM call returns HTTP 400 (model/reasoning mismatch)

Hacker News's public Firebase API (hacker-news.firebaseio.com) is open,
keyless, and rate-tolerant. It is the only source that "just works" in a
zero-config environment, but only if you query topstories.json and filter
by `time >= now - 30d` client-side — the engine's HN subquery uses the
Algolia HN search API which frequently returns no results for vague
breaking-news phrases.

Usage:
  python3 hn_fallback.py [topic_filter] [--days N] [--limit N] [--json]

Examples:
  python3 hn_fallback.py                            # last 30d, top by score
  python3 hn_fallback.py "ai OR gpt" --limit 20     # keyword filter on title
  python3 hn_fallback.py --json | jq '.[:5]'        # machine-readable
"""
from __future__ import annotations
import argparse, json, sys, urllib.request
from datetime import datetime, timezone, timedelta

UA = "curl/8"
TOPSTORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def fetch(limit: int = 120):
    req = urllib.request.Request(TOPSTORIES, headers={"User-Agent": UA})
    ids = json.loads(urllib.request.urlopen(req, timeout=15).read())[:limit]
    out = []
    for i in ids:
        try:
            it = json.loads(urllib.request.urlopen(ITEM.format(i), timeout=10).read())
            if it and it.get("type") == "story":
                out.append({
                    "id": i,
                    "title": it.get("title"),
                    "score": it.get("score", 0),
                    "time": it.get("time"),
                    "comments": it.get("descendants", 0),
                    "url": it.get("url") or f"https://news.ycombinator.com/item?id={i}",
                })
        except Exception:
            continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", nargs="?", default="", help="optional keyword filter (case-insensitive, substring against title)")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    items = fetch(min(args.limit * 3, 200))
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=args.days)).timestamp()
    recent = [x for x in items if (x.get("time") or 0) >= cutoff]
    if args.topic:
        needle = args.topic.lower()
        recent = [x for x in recent if needle in (x.get("title") or "").lower()]
    recent.sort(key=lambda x: x["score"], reverse=True)
    recent = recent[: args.limit]

    if args.json:
        json.dump(recent, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    print(f"HN last {args.days}d, {len(recent)} stories (of {len(items)} fetched)")
    for it in recent:
        t = datetime.fromtimestamp(it["time"], tz=timezone.utc).strftime("%m-%d")
        print(f"[{t}] {it['score']:5d}↑ {it['comments']:4d}c  {it['title'][:120]}")


if __name__ == "__main__":
    main()
