# last30days: Daily Digest Pattern

## What this is

A cron-friendly wrapper that runs `last30days.py` and formats the output as a clean Telegram digest — stats tree + links, no editorial "Top stories" summary.

## Files

- **Wrapper script**: `~/.hermes/scripts/last30days-digest.py`
- **Shell launcher**: `~/.hermes/scripts/last30days-digest_sandy.sh`
- **Output**: `/tmp/digest.md` + stdout (for cron delivery)

## How to invoke (cron/automated)

```bash
#!/bin/bash
exec python3.13 ~/.hermes/scripts/last30days-digest.py
```

The Python wrapper handles:
- Setting `SKILL_ROOT`, `PYTHONPATH`, `LAST30DAYS_PYTHON`, `LAST30DAYS_MEMORY_DIR` env vars
- Running `last30days.py "AI agent" --days 1 --emit=compact`
- Stripping "Top stories" from output (Thomas prefers raw data over editorial summaries)
- Parsing and grouping URLs by platform (YouTube, GitHub, HN, Reddit, Polymarket)
- Writing `/tmp/digest.md` + stdout

## Key learned preferences

- **Thomas wants `--days 1`** — default 30 produces stale/recurring content. Always pass `--days 1` for daily digest use.
- **No "Top stories" editorial** — Thomas wants stats and links directly, no bullet-list summary between them.
- **Use `--emit=compact`** — produces the stats tree + URL list that the digest script parses.
- **Python 3.13 required** — skill requires `python3.13`.

## Cron job setup

Job ID: `c74190680821` (name: `daily-ai-digest`)
- Schedule: `0 6 * * *` (daily at 06:00)
- Script: `last30days-digest_sandy.sh`
- Deliver: `origin` (Telegram DM)

## Common issues

- `last30days-digest_sandy.sh` wrapper uses Sandy scenario runner — if debugging silent failures, check the wrapper script path matches the scenario name.
- If digest produces 0 items from a source (e.g., Reddit at `--days 1`), that source may have no fresh content for that topic in the window. Not a bug — thin data.
- The skill's `--days` flag is named `--lookback-days` in the argparse definition but accepts `--days` as a shorthand.