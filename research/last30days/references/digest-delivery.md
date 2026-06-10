# last30days — Digest Delivery Reference

## The Repetitive Digest Problem

Thomas gets the daily AI digest at 06:00 via `last30days-digest_sandy.sh` → `last30days-digest.py`. He flagged that the content feels same-y every day. Investigation showed:

- Content IS genuinely fresh between runs (diffing consecutive outputs confirms new stories appear)
- But the query `"AI agent"` sits in a 30-day window — core narratives (Agent OS debates, "stop building agents" thread, major launches) persist for weeks and dominate every run
- last30days has **no caching layer** — there is no `--no-cache` flag or TTL mechanism to force

## The Fix: Query Diversification

When Thomas says the digest feels repetitive:
- **Do NOT** add cache flags — they don't exist in this tool
- **Do NOT** assume the tool is broken or stuck
- **DO** change the query topic to something with a different narrative arc

### Query alternatives for AI digest

| Query | What it surfaces |
|---|---|
| `"AI agent products"` | Launches, demos, product announcements |
| `"AI agent funding"` | VC rounds, startup funding, market dynamics |
| `"AI agent launches"` | New releases, version updates, integrations |
| `"AI agent open source"` | GitHub activity, model releases, tooling |
| `"AI agent safety"` | Policy, regulation, alignment discussion |

Rotate these to keep the digest varied. Schedule can stay daily — only the query changes.

## `--deep` Flag for Digest

The digest script currently uses default depth. Adding `--deep` to the last30days call increases per-stream fetch from 12 → 20 items, giving the formatter script more raw material to select from, which naturally produces more varied output.

Current cron script (`last30days-digest_sandy.sh`):
```bash
exec python3.13 ~/.hermes/scripts/last30days-digest.py
```

The digest.py calls last30days with no depth flag. To apply `--deep`, the change is in `last30days-digest.py` line 17 — add `--deep` to the subprocess call.

## Key Files

- Cron job: `daily-ai-digest` (job_id: `c74190680821`)
- Shell wrapper: `~/.hermes/scripts/last30days-digest_sandy.sh`
- Formatter/parser: `~/.hermes/scripts/last30days-digest.py`
- last30days skill: `~/.hermes/skills/research/last30days/scripts/last30days.py`

## Diagnosis Commands

```bash
# Check what's configured
python3.13 ~/.hermes/skills/research/last30days/scripts/last30days.py "AI agent" --diagnose

# Test a new query
python3.13 ~/.hermes/skills/research/last30days/scripts/last30days.py "AI agent products" --emit=compact --search=hackernews,reddit,github
```

## Updating the Digest Query

To change the query, edit `last30days-digest.py` line 17:
```python
["python3.13", f"{SKILL_ROOT}/scripts/last30days.py", "NEW QUERY HERE", "--emit=compact"],
```

To add `--deep`, same line:
```python
["python3.13", f"{SKILL_ROOT}/scripts/last30days.py", "AI agent", "--emit=compact", "--deep"],
```