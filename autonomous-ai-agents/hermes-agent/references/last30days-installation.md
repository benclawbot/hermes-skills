# last30days Skill — Installation & Invocation Reference

## What is `last30days`

Full multi-source research skill: Reddit, X/Twitter, YouTube, TikTok, Bluesky, Hacker News, Polymarket, GitHub, web search. NOT the same as `fast-research-digest` (which is HN + GitHub only, terminal curl commands).

Repo: https://github.com/mvanhorn/last30days-skill

## Installing in Hermes

```bash
# 1. Create skill directory
mkdir -p ~/.hermes/skills/research/last30days

# 2. Download SKILL.md
curl -sL --max-time 30 "https://raw.githubusercontent.com/mvanhorn/last30days-skill/main/skills/last30days/SKILL.md" \
  -o ~/.hermes/skills/research/last30days/SKILL.md

# 3. Download scripts + lib (one-shot via GitHub API listing)
SKILL_DIR="$HOME/.hermes/skills/research/last30days"
mkdir -p "$SKILL_DIR/scripts" "$SKILL_DIR/scripts/lib"
curl -sL --max-time 15 "https://api.github.com/repos/mvanhorn/last30days-skill/contents/skills/last30days/scripts" \
  | python3 -c "import sys,json; [print(f['name'], f['download_url']) for f in json.load(sys.stdin) if f['type']=='file']" \
  | while read name url; do
    curl -sL --max-time 15 "$url" -o "$SKILL_DIR/scripts/$name" 2>/dev/null && echo "OK: $name" || echo "FAIL: $name"
  done

# 4. Download lib/ modules (all .py files in scripts/lib/)
curl -sL --max-time 15 "https://api.github.com/repos/mvanhorn/last30days-skill/contents/skills/last30days/scripts/lib" \
  | python3 -c "import sys,json; [print(f['name'], f['download_url']) for f in json.load(sys.stdin) if f['type']=='file']" \
  | while read name url; do
    curl -sL --max-time 15 "$url" -o "$SKILL_DIR/scripts/lib/$name" 2>/dev/null && echo "OK: $name" || echo "FAIL: $name"
  done
```

## Python Version Requirement

last30days requires **Python 3.12+**. On this machine:
- `python3` = 3.11 (incompatible)
- `python3.13` = 3.13.7 ✓ — available at `/usr/bin/python3.13`

Always set `LAST30DAYS_PYTHON=python3.13` in the invocation.

## Correct Invocation Pattern

```bash
SKILL_ROOT="$HOME/.hermes/skills/research/last30days"
cd "$SKILL_ROOT" && PYTHONPATH="$PWD/scripts" LAST30DAYS_PYTHON=python3.13 LAST30DAYS_MEMORY_DIR="$HOME/Documents/Last30Days" python3.13 scripts/last30days.py "AI agent" --emit=compact
```

Key points:
- `PYTHONPATH="$PWD/scripts"` — last30days.py does `from lib import ...` so lib/ must be in PYTHONPATH relative to the scripts dir
- `LAST30DAYS_PYTHON=python3.13` — overrides the python3.12+ check in env.py
- `LAST30DAYS_MEMORY_DIR` — optional, defaults to `~/Documents/Last30Days`
- Must `cd "$SKILL_ROOT"` first — the script resolves SKILL_ROOT relative to cwd

## Diagnosis

```bash
cd ~/.hermes/skills/research/last30days && PYTHONPATH="$PWD/scripts" python3.13 scripts/last30days.py --diagnose
```

Expected output:
```json
{"available_sources": ["reddit", "youtube", "hackernews", "polymarket", "github"], ...}
```

## Quick Update (Pull Latest)

```bash
cd /path/to/last30days-skill  # wherever you cloned it
git pull
bash skills/last30days/scripts/sync.sh
```

Or re-run the download commands above for a fresh SKILL.md + scripts.

## For Cron Jobs Using last30days

The prompt must include the full invocation. Example (daily digest at 06:00):

```
Fetch today's AI agent news digest and deliver it. Use the last30days research skill at ~/.hermes/skills/research/last30days:

1. Run: SKILL_ROOT="$HOME/.hermes/skills/research/last30days" && cd "$SKILL_ROOT" && PYTHONPATH="$PWD/scripts" LAST30DAYS_PYTHON=python3.13 LAST30DAYS_MEMORY_DIR="$HOME/Documents/Last30Days" python3.13 scripts/last30days.py "AI agent" --emit=compact

2. Synthesize the results into a Telegram-friendly digest. Follow the last30days LAWs: badge first (v3.2.1 + date), then "What I learned:" prose, then "KEY PATTERNS" numbered list, then pass through the emoji-tree footer verbatim. No trailing Sources block.

3. Deliver the final digest to the origin channel.
```