# last30days Cron Job Setup

## Installation

Installed at `~/.hermes/skills/research/last30days/` (NOT in the plugin cache).

Key files:
- `SKILL.md` — full skill contract
- `scripts/last30days.py` — main engine
- `scripts/lib/` — 17 Python library modules
- `scripts/lib/vendor/bird-search/` — X/Twitter search client

## Required Environment

```bash
LAST30DAYS_PYTHON=python3.13
LAST30DAYS_MEMORY_DIR="$HOME/Documents/Last30Days"
SKILL_ROOT="$HOME/.hermes/skills/research/last30days"
PYTHONPATH="$SKILL_ROOT/scripts"
```

Python 3.12+ required — system has 3.13.15 at `/usr/bin/python3.13`.

## Running from cron/headless

Use `--emit=compact` for short output suitable for delivery. The skill runs a full multi-source search (Reddit, YouTube, HN, GitHub, Polymarket) and outputs structured evidence with `URL:` lines.

```bash
SKILL_ROOT="$HOME/.hermes/skills/research/last30days"
cd "$SKILL_ROOT" && PYTHONPATH="$PWD/scripts" \
  LAST30DAYS_PYTHON=python3.13 \
  LAST30DAYS_MEMORY_DIR="$HOME/Documents/Last30Days" \
  python3.13 scripts/last30days.py "AI agent" --emit=compact
```

## Extracting URLs for links section

The `--emit=compact` output includes `URL: https://...` lines for each item. Regex to extract:
```
^\s+-\s+URL:\s+(https?://\S+)
```

Group URLs by domain:
- YouTube: `youtube.com`
- GitHub: `github.com`
- HN: `abcnews.com` (HN submissions about external articles)
- Reddit: `reddit.com`
- Polymarket: `polymarket.com`

## Cron job pattern

For single-script execution (no LLM), use a Python wrapper that:
1. Runs `last30days.py --emit=compact`
2. Extracts `URL:` lines and groups by source
3. Outputs clean digest to stdout

The stdout becomes the cron output file content.

**IMPORTANT:** Do NOT use the Hermes agent+skill path for this. The agent layer adds overhead and the LLM re-synthesizes content that's already been synthesized by the skill engine. A direct Python script is faster and produces cleaner output.

## DEGRADED RUN warning

When run bare (without `--plan`), the skill shows a `DEGRADED RUN WARNING` banner. This is expected in cron/headless contexts — it's informational, not an error. The skill still produces valid output from keyword fallback.

To suppress: the skill requires handle resolution via `WebSearch` before running with full richness. For automated cron use, accept the degraded mode — it's the expected mode for headless execution.

## Active sources

4 active in degraded mode: GitHub, Hacker News, Reddit, Youtube.
Sources requiring API keys (X/Twitter, TikTok, Instagram, Brave Search) are unavailable without keys.

## Script file location

`~/.hermes/scripts/last30days-digest.py` — the working digest script used by `last30days-digest_sandy.sh`.