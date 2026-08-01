# ⚠️ HOST-AGENT PLANNING GATE (LAW 7) — READ BEFORE INVOKING

If you are a reasoning-model agent (Hermes, Claude Code, Codex, Gemini, any LLM runtime) invoking `last30days` on a **named-entity or named-event topic**, you ARE the planner. Do NOT call the script bare.

## Why this gate exists

The deterministic fallback path runs without a `--plan`, but the engine emits a `DEGRADED RUN WARNING` banner and demotes every evidence cluster with `Why: fallback-local-score (entity-miss demotion)`. On named topics the run comes back ~50% useful. A 70-second wait + a degraded result is worse than no result — it costs the user time AND erodes trust in the next call.

## Mandatory pre-flight for host agents

1. **Generate a JSON plan yourself.** Schema in `references/plan-schema.md`. Required fields: `intent`, `freshness_mode`, 3–5 paraphrased `subqueries`, `sources`. No API key needed — you are the LLM.
2. **Resolve named entities first.** If the topic names specific X handles, GitHub repos, or subreddits, resolve them via your own web_search tool (Step 0.55). Bare entity names like `"AI important news"` get demoted because the engine can't anchor them.
3. **Pass the plan via `--plan '$JSON'`.** Quote-escape carefully — the JSON contains nested quotes.

## When bare invocation IS fine

- Cron / headless heartbeat with a fixed query already validated upstream.
- Watchlist items previously planned and stored in the watchlist DB.
- Generic fuzzy topics ("best new restaurants in Brooklyn") where any signal beats none — and you're OK with the degraded banner.

## Python runtime

The script hard-requires Python 3.12+. On systems where `python3` is 3.11 (e.g. Debian/Ubuntu LTS), install 3.13 first:

```bash
uv python install 3.13
uv run --python 3.13 --with requests --with openai --with httpx \
  python ~/.hermes/skills/research/last30days/scripts/last30days.py \
  '<query>' --plan '<json>'
```

## What a good plan looks like

```json
{
  "intent": "breaking_news",
  "freshness_mode": "strict_recent",
  "cluster_mode": "story",
  "subqueries": [
    {"label": "primary",   "query": "Moonshot Kimi K3 release",          "sources": ["reddit","hackernews","youtube","github"]},
    {"label": "reaction",  "query": "Kimi K3 vs GPT-5 vs Claude reactions","sources": ["reddit","tiktok","youtube"]},
    {"label": "technical", "query": "Kimi K3 architecture benchmarks MoE", "sources": ["hackernews","github"]}
  ]
}
```

Bad plan: vague subqueries that re-state the topic. Good plan: paraphrases that pull different facets of the same story into different sources.
