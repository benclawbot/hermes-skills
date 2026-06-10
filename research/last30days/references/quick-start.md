# last30days — Hermes Quick-Start

> The full skill contract (LAWs, step-by-step, source configs, all flags) lives in `references/full-skill.md`. This file is the Hermes-specific quick-start only.

## One-shot install

```bash
SKILL_ROOT="$HOME/.hermes/skills/research/last30days"
mkdir -p "$SKILL_ROOT/scripts/lib"
curl -sL "https://raw.githubusercontent.com/mvanhorn/last30days-skill/main/skills/last30days/SKILL.md" -o "$SKILL_ROOT/SKILL.md"
for f in last30days.py briefing.py store.py watchlist.py compare.sh sync.sh; do
  curl -sL "https://raw.githubusercontent.com/mvanhorn/last30days-skill/main/skills/last30days/scripts/$f" -o "$SKILL_ROOT/scripts/$f"
done
curl -sL "https://api.github.com/repos/mvanhorn/last30days-skill/contents/skills/last30days/scripts/lib" | python3 -c "import sys,json; [print(f['download_url']) for f in json.load(sys.stdin) if f['type']=='file']" | while read url; do
  f=$(basename "$url"); curl -sL "$url" -o "$SKILL_ROOT/scripts/lib/$f" 2>/dev/null
done
```

**Requires:** `python3.13` (3.12+), `yt-dlp` for YouTube transcripts.

## Run

```bash
SKILL_ROOT="$HOME/.hermes/skills/research/last30days"
cd "$SKILL_ROOT" && PYTHONPATH="$PWD/scripts" \
  LAST30DAYS_PYTHON=python3.13 \
  LAST30DAYS_MEMORY_DIR="$HOME/Documents/Last30Days" \
  python3.13 scripts/last30days.py "TOPIC" --emit=compact 2>&1
```

## Cron / delegate_task synthesis checklist

1. Run the command above, capture full output
2. `EVIDENCE FOR SYNTHESIS` block → transform into `What I learned:` prose (do NOT emit verbatim)
3. `PASS-THROUGH FOOTER` block → emit verbatim after synthesis
4. `DEGRADED RUN WARNING` → emit verbatim before synthesis (skip on clean runs)
5. **Links section:** extract all item URLs from evidence → `[Title](URL)` grouped by source, no scores or item counts
6. **Output LAWs:** badge first · no `##` headers in prose body · no em-dashes · no trailing `Sources:` block

## `--plan` flag (mandatory on named-entity topics)

```bash
python3.13 scripts/last30days.py "TOPIC" \
  --plan '{"intent":"concept","freshness":"evergreen_ok","cluster_mode":"none","subqueries":3,"source":"llm"}' \
  --emit=compact
```

You ARE the planner — generate JSON yourself, no credentials needed.

## Sources

| Source | Auth | Free |
|--------|------|------|
| Reddit, HN, Polymarket, GitHub, YouTube | — | ✅ |
| X/Twitter | `AUTH_TOKEN+CT0` (browser) or `XAI_API_KEY` | partial |
| TikTok, Instagram | `SCRAPECREATORS_API_KEY` | ❌ |
| Web search | `BRAVE_API_KEY` | ❌ |

## vs fast-research-digest

- `fast-research-digest`: 2 sources (HN + GitHub), manual curl, no engine. Lightweight pulse check only.
- `last30days`: 9+ sources, Python engine, ranked evidence, transcripts. Real research.