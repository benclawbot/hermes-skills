# Dreams Consolidation — Sandy Scenario

Deterministic 4-phase memory consolidation via Sandy scenario replay.

## When to Use

Cron job `hermes-dreams` runs this scenario every 24hrs (4am). Can also be triggered manually:
```bash
python3 ~/.hermes/skill-assets/sandy/scripts/play.py ~/.hermes/sandy/scenarios/dreams.json --debug
```

## Scenario: dreams.json

```json
{
  "name": "dreams",
  "description": "4-phase memory consolidation — orient, gather signal, consolidate, prune index",
  "version": "1.0.0",
  "vars": {
    "HERMES_HOME": "~/.hermes",
    "OBSIDIAN_VAULT_PATH": "~/Desktop/Memory",
    "SESSIONS_DIR": "~/.hermes/sessions",
    "MEMORY_DIR": "~/.hermes/memory",
    "LAST_DREAM_FILE": "~/.hermes/.last-dream",
    "MAX_AGE_DAYS": "7",
    "MEMORY_INDEX_MAX_LINES": "200"
  },
  "steps": [
    {
      "tool": "claude__bash",
      "description": "Check if 24+ hours since last dream",
      "command": "bash -c \"[ $(($(date +%s) - $(cat ~/.hermes/.last-dream 2>/dev/null || echo 0))) -gt 86400 ]\" && echo 'DREAM_NECESSARY=1' || echo 'DREAM_NECESSARY=0'"
    },
    {
      "tool": "claude__bash",
      "description": "Orient — list recent session files",
      "command": "find ~/.hermes/sessions/ -name '*.jsonl' -mtime -7 | sort -r | head -20"
    },
    {
      "tool": "claude__bash",
      "description": "Gather signal — user corrections",
      "command": "grep -il \"actually\\|no,\\|wrong\\|incorrect\\|stop doing\\|don't do\\|I said\\|I meant\\|correction\" ~/.hermes/sessions/*.jsonl 2>/dev/null | head -10"
    },
    {
      "tool": "claude__bash",
      "description": "Gather signal — preferences",
      "command": "grep -il \"I prefer\\|always use\\|never use\\|I like\\|I want\\|from now on\\|going forward\\|remember that\" ~/.hermes/sessions/*.jsonl 2>/dev/null | head -10"
    },
    {
      "tool": "claude__bash",
      "description": "Gather signal — decisions",
      "command": "grep -il \"let's go with\\|I decided\\|we're using\\|the plan is\\|switch to\\|decision\\|we agreed\" ~/.hermes/sessions/*.jsonl 2>/dev/null | head -10"
    },
    {
      "tool": "claude__bash",
      "description": "Gather signal — recurring patterns",
      "command": "grep -il \"again\\|every time\\|keep forgetting\\|as usual\\|same as before\\|we always\\|the usual\" ~/.hermes/sessions/*.jsonl 2>/dev/null | head -10"
    },
    {
      "tool": "claude__bash",
      "description": "Check memory directory state",
      "command": "ls ~/.hermes/memory/ 2>/dev/null && wc -l ~/.hermes/memory/MEMORY.md 2>/dev/null"
    },
    {
      "tool": "claude__bash",
      "description": "Read current MEMORY.md index",
      "command": "cat ~/.hermes/memory/MEMORY.md 2>/dev/null | head -50"
    },
    {
      "tool": "claude__bash",
      "description": "Write dream timestamp after completion",
      "command": "date +%s > ~/.hermes/.last-dream && echo \"Dream timestamp updated: $(cat ~/.hermes/.last-dream)\""
    }
  ],
  "on_success": {
    "output": "NO_ANOMALIES",
    "notify": false
  },
  "on_failure": {
    "notify": true,
    "escalate": true
  }
}
```

## Cron Job Definition

```bash
hermes cron create "0 4 * * *" \
  --skill "dreams" \
  --prompt "Run 4-phase memory consolidation for all Hermes sessions. Read ~/.hermes/skills/note-taking/dreams/SKILL.md and execute: ORIENT (scan sessions), GATHER SIGNAL (grep corrections/preferences/decisions), CONSOLIDATE (merge to memory), PRUNE & INDEX (rebuild MEMORY.md under 200 lines). Stay silent on success. Notify only if significant corrections were found and merged. Timer file: ~/.hermes/.last-dream." \
  --name "hermes-dreams" \
  --deliver local
```

## Verification Commands

```bash
# Manual trigger
touch ~/.hermes/.dream-pending

# Check timer age
stat ~/.hermes/.last-dream 2>/dev/null

# Run scenario debug
python3 ~/.hermes/skill-assets/sandy/scripts/play.py ~/.hermes/sandy/scenarios/dreams.json --debug

# Verify consolidation
wc -l ~/.hermes/memory/MEMORY.md
grep -c "yesterday\|last week\|last month" ~/.hermes/memory/*.md 2>/dev/null || echo "No relative dates found"
```

## Dependencies

- Sandy runtime at `~/.hermes/skill-assets/sandy/scripts/`
- Hermes sessions at `~/.hermes/sessions/*.jsonl`
- Memory at `~/.hermes/memory/MEMORY.md`
- Timer at `~/.hermes/.last-dream`