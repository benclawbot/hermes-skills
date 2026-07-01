# Zero-config fallback: when the engine returns nothing

**Symptom:** `python3 last30days.py --quick '<topic>'` prints
`Reddit: 0 threads, YouTube: 0 videos, HN: 0 stories, ...` and the
`Ranked Evidence Clusters` section is empty, even though the topic is real.

Two failure modes stack on top of each other in a default install:

1. **Reddit 403.** `reddit.com/search.json` rate-limits headless callers
   from shared egress IPs. Every install behind NAT / a cloud VM hits
   this within a few queries. The engine logs:
   `RedditPublic] 403 forbidden: https://www.reddit.com/search.json?...`
2. **Engine planner 400.** When the only LLM key is `OPENROUTER_API_KEY`
   and the default model doesn't match, the engine's internal planner
   returns `HTTPError: HTTP 400: Bad Request` and silently falls back to a
   single-word deterministic query — which then also 403s on Reddit.

Without `SCRAPECREATORS_API_KEY` (X/TikTok/IG) and without
`BRAVE_API_KEY` / `EXA_API_KEY` / `SERPER_API_KEY` (general web), every
named source has been throttled to nothing. The output looks like a
planner failure when it is really a *source-availability* failure.

**Fix: fall back to Hacker News's public Firebase API.**

`hacker-news.firebaseio.com/v0/topstories.json` is keyless, unauthenticated,
and tolerant. The engine's HN adapter uses the Algolia search endpoint,
which returns empty for vague breaking-news phrases ("what happened",
"world news", "AI news today"). Pulling `topstories.json` directly and
filtering `time >= now - 30d` client-side sidesteps both problems.

```bash
# default invocation: last 30d, top 50 by score
python3.14 ~/.hermes/skills/research/last30days/scripts/hn_fallback.py

# with keyword filter
python3.14 ~/.hermes/skills/research/last30days/scripts/hn_fallback.py "ai OR gpt" --limit 20

# JSON output for piping into the synthesis step
python3.14 ~/.hermes/skills/research/last30days/scripts/hn_fallback.py --json --limit 100
```

The output is a plain ASCII list (`[mm-dd] SCORE↑ COMMENTSc  TITLE`) or
JSON. Treat it as raw evidence, then apply the same `What I learned:` /
KEY PATTERNS / CITATIONS synthesis the engine output would normally
follow. The skill's HN subquery path cannot produce this signal in a
zero-config environment; this script is the documented workaround.

**When NOT to use this:** if `BRAVE_API_KEY` (or any web backend) is
configured, the engine's auto-resolve path will pull real-time web
evidence and you should let the engine run. The HN fallback is only
the right move when (a) the engine has produced zero items on a topic
the user clearly cares about, AND (b) no web backend is configured.
