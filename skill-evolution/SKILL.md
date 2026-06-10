---
name: skill-evolution
description: Mine Hermes sessions for lessons, evaluate skill quality, and evolve skills over time. Use when "learn from this", "improve this skill", "evolve skill", "evaluate skill", "measure skill quality", "mine sessions".
allowed-tools: Read,Bash,write,edit,execute_command
---

# Skill Evolution

Extracts patterns, lessons, and gaps from Hermes session history to improve skill quality over time.

## Memory Structure

All data lives at `~/.hermes/.pi/skill-memory.json`:

```json
{
  "lessons":  [],   // Extracted insights from sessions
  "gaps":     [],   // Identified skill deficiencies
  "patterns": [],   // Recurring tool/approach patterns
  "evaluations": [], // Skill quality scores
  "sessions":  [],   // Mining run history
  "evolutions": []   // Skill change log
}
```

## Mining: Extract Lessons from Sessions

### Manual Run

```bash
python3 ~/.hermes/skills/skill-evolution/scripts/mine-hermes-sessions.py
```

### What to Mine

Scan `~/.hermes/sessions/*.jsonl` for these pattern types:

| Type | Stored in | Patterns | Priority |
|------|----------|---------|----------|
| `correction` | `lessons` | actually, no,, wrong, stop doing, I said... | High |
| `preference` | `lessons` | I prefer, from now on, always use... | High |
| `decision` | `lessons` | I decided, we're using, the plan is... | High |
| `lesson` | `lessons` | learned, figured out, found that... | Medium |
| `recurring` | `lessons` | again, every time, as usual... | Medium |
| `gap` | `gaps` | error, failed, crash, not working, stuck... | High |
| `approach` | `patterns` | delegate then verify, check before, try except... | Medium |

### What to Extract Per Hit

- The verbatim content (up to 500 chars)
- Role (user = high confidence, assistant = medium)
- Session file + timestamp
- 2 messages of context before and after

### Storage Rules

- Deduplicate by first 80 chars of lesson/gap/pattern summary
- `lessons`: keep last **50** (cap at 100)
- `gaps`: keep last **30** (cap at 50)
- `patterns`: keep last **30** (cap at 50)
- `sessions`: keep last **50** session summaries
- Lessons from user messages get `confidence: "high"`, assistant messages get `"medium"`

### Output Format Per Lesson

```json
{
  "id": "a1b2c3d4",
  "lesson": "[correction] user said 'actually no, that's not right'",
  "type": "correction",
  "source_session": "session_20260515_094728",
  "timestamp": "2026-05-15",
  "confidence": "high"
}
```

## Evaluation: Score Skill Quality

When evaluating a skill, run the LLM-as-judge rubric:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Follows procedure | 30% | Does agent follow skill's steps? |
| Output quality | 30% | Is result correct and useful? |
| Conciseness | 20% | Within token budget? Not verbose? |
| Completeness | 20% | All required elements present? |

Score ranges:

| Score | Label | Action |
|-------|-------|--------|
| 90-100 | Excellent | Skill is performing well |
| 70-89 | Good | Minor improvements possible |
| 50-69 | Needs Work | Significant gaps identified |
| <50 | Poor | Major rewrite recommended |

## Evolution: Apply Lessons to Skills

When a skill has enough low-scoring evaluations:

1. Read the skill's current SKILL.md
2. Pull related lessons from skill-memory.json
3. Identify the specific gap (wrong command, missing step, etc.)
4. Patch the skill with the fix
5. Record the evolution in skill-memory.json

## Cron Job

The `hermes-session-miner` cron runs this every 24h:
- Schedule: `every 1440m`
- Script: `mine-hermes-sessions.py --limit 50`
- Skills: `skill-evolution`
- Delivery: `local` (silent unless new lessons found)

## Supporting Scripts

All scripts live at `~/.hermes/skills/skill-evolution/scripts/`:

| Script | Purpose | Cron |
|--------|---------|------|
| `mine-hermes-sessions.py` | Extract lessons, gaps, patterns from sessions | `hermes-session-miner` (24h) |
| `cleanup-sessions.py` | Remove old request dumps (>48h) and session .json files (>7 days) | `session-cleanup` (6h) |
| `backup-memories.py` | Backup memories dir to timestamped tar.gz, keep last 4 | `memory-backup` (weekly Sun 09:00) |
| `watch-hermes-health.py` | Health watchdog: gateway process, cron scheduler, memory files, disk | `hermes-health-watchdog` (30min) |

Run manually: `python3 ~/.hermes/skills/skill-evolution/scripts/<script-name>.py [--verbose]`

## Pitfalls

### Session ID not propagated to inner function (May 2026)
`session_id` was read from the outer loop (`session["session_id"]`) but never passed into `find_mining_hits()`. Result: all 95 lessons had `source_session: "unknown"`. Fix: add `session_id=session["session_id"]` as an explicit argument at the call site. Always verify outer-scope contextual IDs propagate into helper functions.

### Content truncation before pattern matching
Very long context-compaction messages (10k+ chars) were being pattern-matched directly, creating false positives and duplicating lessons. Fix: truncate to 500 chars in `extract_messages()` before storing. Lesson: always size-cap content before it enters pattern matching or deduplication.

### Duplicate processing loop in mine_sessions()
After patching session_id propagation, the function accidentally developed two identical processing loops. The first loop populated `all_hits` and `session_summaries`; then both were reinitialized to empty before the second loop ran, losing all data from the first pass. Symptom: the return dict showed zero new lessons on second run even though content existed. Fix: initialize `all_hits = []` and `session_summaries = []` only once, before the session loop, not twice.

### Session file formats: .jsonl vs .session_*.json (May 2026)
Hermes sessions come in two formats with different naming conventions:
- `.jsonl` files: named `YYYYMMDD_HHMMSS_<hash>.jsonl` — historical transcripts
- `.session_*.json` files: named `session_<date>_<hash>.json` — current sessions

The miner must handle both. Both are JSONL format internally (one JSON object per line with `role`, `content`, `timestamp` fields). The `load_recent_sessions()` function must detect type by filename pattern and extract session_id from the filename, not from the JSON content (which may not have a session_id field). Always check both glob patterns: `*.jsonl` and `session_*.json`.

### Gateway process name for health checks
The Hermes gateway runs as `hermes_cli.main` (not `hermes-gateway`). pgrep pattern must be `hermes_cli.main|hermes-gateway` to match the actual process command line. A pattern that only matches `hermes-gateway` will always return empty even when the gateway is healthy.

### Script must live at ~/.hermes/scripts/ (May 2026)
Cron jobs with `script: <filename>` look for the file at `~/.hermes/scripts/<filename>`. If the script lives only in a skill's `scripts/` subdirectory, the job fails with "Script not found". For health watchdog cron jobs:
1. Ensure the script is copied to `~/.hermes/scripts/` (not just in the skill directory)
2. If the script lives in `skills/<skill>/scripts/`, copy it to `~/.hermes/scripts/` after any change
3. The canonical location for cron-executed scripts is `~/.hermes/scripts/` — skills are storage, not execution entry points

Real incident: `hermes-health-watchdog` (job_id: da927a240778) failed with "Script not found: /home/thomas/.hermes/scripts/watch-hermes-health.py" — the script was only at `~/.hermes/skills/skill-evolution/scripts/watch-hermes-health.py`. Fix: `cp ~/.hermes/skills/skill-evolution/scripts/watch-hermes-health.py ~/.hermes/scripts/`.

### Cron ticker stop false-positive (May 2026)
The gateway logs "Cron ticker stopped" and "Cron ticker started (interval=60s)" as a normal restart cycle — this is not an anomaly. The old `check_gateway_log()` alerted on any "Cron ticker stopped" entry regardless of whether the ticker had already restarted, causing spurious alerts every 30 minutes.

Fix: Only alert on sustained stoppage:
- Ticker stopped **and** never restarted in the last 50 log lines → alert
- Ticker stopped **and** restarted within ≤60s → normal restart cycle, no alert
- Ticker was down for **>60s** before restarting → alert with gap duration (possible instability signal)

```python
# Parse both timestamps to check gap
stopped_lines = [l for l in recent_lines if "Cron ticker stopped" in l]
restarted_lines = [l for l in recent_lines if "Cron ticker started" in l]
if stopped_lines and not restarted_lines:
    ANOMALIES.append("Cron ticker stopped with no restart — cron jobs may not be running")
elif stopped_lines and restarted_lines:
    last_stop = stopped_lines[-1]
    last_start = restarted_lines[-1]
    try:
        stop_ts = datetime.strptime(last_stop.split(",")[0], "%Y-%m-%d %H:%M:%S")
        start_ts = datetime.strptime(last_start.split(",")[0], "%Y-%m-%d %H:%M:%S")
        gap = (start_ts - stop_ts).total_seconds()
        if gap > 60:
            ANOMALIES.append(f"Cron ticker was down for {int(gap)}s before restart — may indicate instability")
    except Exception:
        if not restarted_lines:
            ANOMALIES.append("Cron ticker stopped with no restart — cron jobs may not be running")
```

Real incident: `hermes-health-watchdog` alert at 14:30 said "Cron ticker stopped — cron jobs may not be running" but the log showed ticker had restarted at 14:10:43 (36 min prior). False alarm from normal restart cycle.

## Reference

- Pi-Agent-Optimus source: `~/Pi-Agent-Optimus/skills/skill-evolution/`
- Hermes sessions: `~/.hermes/sessions/*.jsonl`
- Memory store: `~/.hermes/.pi/skill-memory.json`
- Skills sync mechanics: `references/skills-sync.md`

## Pitfalls (additional)

### Skill description trigger phrases must match the user's actual phrasing (2026-06-07)

When a skill is created, its `description` field is what the loader matches against the user's request. If you paraphrase the trigger ("test what you built" instead of "test what you implemented") the skill won't fire on the user's literal wording.

**Fix:** after writing the skill, run a description-vs-known-phrasings cross-check:

```python
desc = skill_description.lower()
known_user_phrasings = [...]   # the exact phrases the user has used for this class
for phrase in known_user_phrasings:
    if phrase.lower() not in desc:
        print(f"MISS: '{phrase}' — add to description or frontmatter")
```

The test is in-session cheap (no API call). Better than discovering it six turns later when the user says "you have a skill for this, why didn't you load it?" Real example: `test-what-you-built` was created with "test what you built" in its description, but the user's actual wording was "test what you implemented." The skill didn't match; the user had to say "now test it" to load it. Fix: add the literal phrase to the description.

Lesson: trigger phrases in a skill description are a *contract* with the user. If the user said it a certain way, that exact way belongs in the description.

### Cross-reference job IDs to detect orphan output dirs (2026-06-07)

When auditing cron health, `cron/output/` accumulates directories named after job IDs. When jobs are deleted, the dirs are often left behind. To find orphans:

```bash
# Find output dirs whose job_id is no longer in jobs.json
for d in ~/.hermes/cron/output/*/; do
  jobid=$(basename "$d")
  if ! grep -q "\"$jobid\"" ~/.hermes/cron/jobs.json; then
    echo "ORPHAN: $jobid ($(ls "$d" | wc -l) files)"
  fi
done
```

Orphan dirs are disk rot (a `d14ed388c60f/` was found with 69 files from a 32-day-old deleted job). They also confuse cron health checks because `ls -lt cron/output/` looks like the job is still running.

Lesson: when auditing any state dir named by ID (cron jobs, sessions, sessions/.session_watchdog_state, etc.), cross-reference against the registry. If the ID is in the dir but not the registry, it's dead weight.

### Three skill-removal paths, one for each install source (2026-06-07)

Skill cleanup is not a single operation. The right tool depends on how the skill got installed:

| Install source | Detection | Removal tool | What it cleans |
|---|---|---|---|
| **Hub-installed** (via `npx skills add` or `hermes skills install`) | `_meta.json` present in skill dir AND entry in `~/.hermes/skills/.hub/lock.json` | `hermes skills uninstall <basename>` | Disk + hub lock.json atomically |
| **Agent-installed** (created by Hermes or you) | No `_meta.json`, or `created_by: "agent"` in `.usage.json` | `hermes curator archive <basename>` | Moves to `.archive/`, reversible via `hermes curator restore` |
| **Bundled** (shipped with Hermes) | In `~/.hermes/skills/.bundled_manifest` | NEVER remove | — |

**Critical:** `hermes skills uninstall` takes the **basename**, not the path. The skills CLI walks category subdirs. So `hermes skills uninstall creative-ideation` works; `hermes skills uninstall creative/creative-ideation` does not.

`rm -rf <skill-dir>` is **always wrong** for these cases:
- For hub skills: leaves the `lock.json` entry orphaned, future audits report them as missing-installed
- For agent skills: bypasses `.archive/`, so the curator has no recovery path
- For bundled skills: the next install re-seeds them anyway

**Real session example:** A `.hermes/` audit found 50+ skills to remove. Wrong: `rm -rf` each one (lost recovery, broke hub lock, broke PM umbrella). Right: `hermes skills uninstall <name>` for the 4 hub-installed (taste-skill + 3 others), `hermes curator archive <basename>` for the 45 agent-installed.

Lesson: when the user says "remove X skill" or "clean up skills", identify the install source first. The wrong tool either leaves state inconsistent or makes the operation unrecoverable.

### Identifying dangerous skills before audit (2026-06-07)

`hermes skills audit` re-scans all hub-installed skills and prints the verdict. Always run this before any hub-skill cleanup — it tells you:

1. Which skills are flagged DANGEROUS (block install, force uninstall)
2. What the findings are (CRITICAL persistence = modifies AGENTS.md/CLAUDE.md = tries to persist into every future session; MEDIUM supply_chain = global npm install; MEDIUM execution = subprocess.run with no sandbox)
3. Whether the verdict can be overridden (`--force does not override a dangerous verdict`)

The `scan_verdict: "dangerous"` in `~/.hermes/skills/.hub/lock.json` is the same data — audit re-runs tirith, lock.json is the cached result. Audit is fresher.

**Pattern recognition for instant-danger skills:**
- "Updates AGENTS.md / CLAUDE.md / SOUL.md so every session starts with X" → CRITICAL persistence → uninstall
- "Run `npm install -g <cli>`" → MEDIUM supply chain → uninstall unless user wants the CLI
- "subprocess.run / os.system in skill scripts/" → MEDIUM execution, often OK if scoped to one task
- Trust level `community` + ANY finding → prefer uninstall

A skill that was previously blocked (in `audit.log`) but still got installed (e.g. via `--force`) and is loaded today is the highest-priority removal — the security gate fired twice and was overridden. Don't second-guess it.

### Empty category dirs after archive (2026-06-07)

`hermes curator archive` moves the skill to `.archive/` but does **not** remove the parent category dir. If `apple/apple-notes` is the last skill under `apple/`, you're left with:

```
apple/
└── DESCRIPTION.md   # <- prevents rmdir
```

`rmdir apple` fails with "Directory not empty". You must remove DESCRIPTION.md first:

```bash
rm /home/thomas/.hermes/skills/<category>/DESCRIPTION.md
rmdir /home/thomas/.hermes/skills/<category>
```

Three categories (`apple/`, `gaming/`, `smart-home/`) were left empty after archiving all 4-5 skills in each. Each had a 130B `DESCRIPTION.md` stub that exists only as a category marker. If you don't care about the marker, remove + rmdir. If you do, leave it.

### `hermes cron rm` cleans its own output dir (2026-06-07)

When removing a cron job via `hermes cron rm <job-id>`, the gateway automatically deletes the corresponding `cron/output/<job-id>/` directory. **Do not** also `rm -rf cron/output/<job-id>/` — race condition with the next scheduled run can leave a half-deleted state. Verified: removing a job immediately after its schedule fired, the output dir was gone within seconds.

Conversely, if you delete the cron job by **editing `jobs.json` directly** (don't do this — use the tool), the output dir WILL be orphaned. So the orphan detection script in the previous pitfall catches only that case, not the tool-removal case.

### Skill audit workflow (the class) (2026-06-07)

When the user says "audit skills", "clean up skills", "remove risky skills", "remove unused skills", or "prune skills", execute this:

1. **Snapshot first**: `hermes curator backup` (tar.gz at `~/.hermes/skills/.curator_backups/`)
2. **Identify all three categories** in one pass:
   ```bash
   # Hub-installed with verdicts
   hermes skills audit
   # Active + stale + agent-created
   hermes curator status
   # Never-used (last_used_at == null)
   python3 -c "import json; d=json.load(open('/home/thomas/.hermes/skills/.usage.json')); print('\n'.join(k for k,v in d.items() if v.get('last_used_at') is None and v.get('last_viewed_at') is None))"
   ```
3. **Tier the removals**:
   - Tier 1 — Dangerous (audit verdict = dangerous): always remove
   - Tier 2 — Wrong platform (Apple skills on Linux, Mac-only on Windows): remove if not planned
   - Tier 3 — Never used (last_used_at == null): remove if low-impact (Apple cluster, PM subskills, decorative) — **but preserve if the skill is part of a live umbrella** (e.g. PM subskills feed a real dashboard at `pm-dashboard.html`)
4. **Execute in this order**:
   - `hermes skills uninstall <name>` for hub-installed (one at a time, with `echo "y" |` for the confirm prompt)
   - `hermes curator archive <basename>` for agent-installed (basename only, no path prefix)
   - `rm <category>/DESCRIPTION.md && rmdir <category>` for empty category dirs
5. **Verify**: `hermes curator status | grep -E "active|archived"` and `ls ~/.hermes/skills/.archive/ | wc -l`

Skill audit is non-destructive via this path (recoverable from `.archive/` and the curator backup). Restore via `hermes curator restore <name>` if you deleted the wrong one.

Real session numbers: 1 dangerous (taste-skill) + 4 hub-installed (wrong platform) + 45 archived + 3 empty category dirs removed in one pass. PM cluster (36 subskills) preserved because the live dashboard at `pm-dashboard.html` calls them programmatically — they look "never used" but are load-bearing.