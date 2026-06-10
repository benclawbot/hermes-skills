---
name: self-improvement-loop
description: "Design and operate a closed-loop self-improvement system for an AI agent — propose → judge → DECIDE (Telegram inline buttons) → apply → grade, with override-rate + help-ratio feedback signals, an avoid-list, judge calibration checkpoint, worked SQLite schema, and the cron-budget / patch-durability / column-drift / test-isolation / shared-state-per-process-path pitfalls learned the hard way. The env-var-overridable path pattern keeps test suites from polluting prod state across every writable path (DB, branch dirs, backup/marker dirs). Use when the user wants the agent to improve its own skills/memory based on session transcripts, says 'recursive self-improvement', 'improve yourself from sessions', or asks for a feedback loop where the agent proposes changes to its own config."
version: 1.5.0
author: Hermes Agent (Thomas)
license: MIT
metadata:
  hermes:
    tags: [self-improvement, eval-harness, feedback-loop, agent-eval, drift-detection, test-isolation]
    category: software-development
---

# Self-Improvement Loop

A closed-loop system where the agent reads its own past sessions, proposes
changes to its own skills/memory, has a separate model judge those proposals,
applies approved ones, and measures whether the changes *actually helped*.

## When to use this skill

- Thomas says "improve yourself", "recursive self-improvement", "build a
  feedback loop for your own skills", "mine sessions for lessons", "eval
  harness for self-modifications"
- The task is the *loop* itself (the architecture, the cron schedule, the
  database, the judge), NOT a single skill the loop is proposing to write
- The user wants both a feedback signal (did the judge call it right?) AND
  an outcome signal (did the applied change help?)

Do NOT use this skill for:
- General agent evaluation (use `harness-framework`)
- Single-skill quality improvement (use `skill-evolution`)
- Memory-only consolidation (use `memory-dreams`)
- Adapting a codebase to a spec (use `codebase-porting`)

## The 5 stages (added DECIDE — inline-keyboard decision — 2026-06-08)

```
  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ PROPOSE │ →  │  JUDGE  │ →  │ DECIDE  │ →  │  APPLY  │ →  │  GRADE  │
  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
       │              │              │              │              │
   (model A)      (model B)     (thomas via     (writes file)   (heuristics)
                                  Telegram
                                  buttons)
```

1. **Propose** — model A reads recent unmined sessions, emits candidate
   proposals (skill patch, memory add, rubric update). Strict JSONL output.
2. **Judge** — model B (different from A) reviews each proposal against
   the active rubric. Records verdict + reasoning. Calibration is the
   first feedback signal: override rate = judge failure rate.
3. **Decide** — thomas taps inline-keyboard buttons on the digest
   message (✅ Approve / ❌ Reject / ✏️ Modify per proposal). Polled by
   `handle_decision.py` via `getUpdates`; marks the proposal
   `merged`/`rejected` and edits the digest message with a decision
   stamp. **Inserted between Judge and Apply** because it's a separate
   concern (UI ↔ DB) with its own cron cadence (every minute) — the
   apply step doesn't need to know thomas came from a button, but the
   decider MUST NOT depend on the apply step's state machine. See
   `references/inline-keyboard-decisions-2026-06-08.md` for the full
   protocol (callback_data schema, polling offset persistence, message
   editing, `Modify` semantics, network-failure isolation).

   **User preference (2026-06-08):** when thomas says "use buttons for
   my answers, just like in clarify" (or any equivalent — "tappable
   options", "give me a UI", "let me tap to decide"), the SRI
   decision flow uses the inline-keyboard surface as the **default**,
   not the one-question-at-a-time text-reply fallback. The buttons
   ARE the decision protocol; the text-reply path
   (`approve #N | reject #N | modify #N: <note>`) is a manual
   fallback for when the bot or polling is broken, not the
   default. If you build a new decision surface for any SRI flow
   (not just the weekly digest — e.g. judge calibration prompts,
   rubric self-eval sign-off, memory-hygiene approval), reuse the
   same `sri-decision-handler` cron and the same `callback_data`
   schema rather than inventing a new UI. Two parallel decision
   surfaces drift; one grows.
4. **Apply** — approved proposals get written to skill/memory files.
   Safety: skip pinned/hub-installed skills, validate paths, back up.
5. **Grade** — heuristic grading of prior applied changes. Three signals:
   - **reverted**: file content matches a post-apply backup (rolled back)
   - **recorrected**: a later applied change touches the same region
   - **neutral**: 7+ days old with no negative signal (default; absence
     of evidence is not proof of help)
   - **helped**: explicitly observed (currently unsettable without manual
     mark — design for this hook to be filled later by a real eval)

Help ratio = `helped / (helped + reverted + recorected)`. Becomes a real
drift detector after ~10 graded outcomes.

## Two feedback signals, not one

A common mistake is treating "judge accuracy" as the only signal. It's not.
Override rate measures *judge calibration* — did the judge predict thomas's
call? It tells you nothing about whether the *change* itself helped.

| Signal       | Measures              | Slow?  | What it catches            |
|--------------|-----------------------|--------|----------------------------|
| Override rate| Judge calibration     | Fast   | Judge drift, rubric issues |
| Help ratio   | Change quality        | Slow   | Real-world impact of patches |

You need both. Override rate is the only signal that responds in a day.
Help ratio is the only one that tells you whether the loop is *actually*
making the agent better.

## Four more coverage-gap signals (v2 — Phases 1-4)

The two signals above don't catch every failure mode. After running
the loop for a few weeks, four more coverage gaps surfaced. Each
became a real, observable signal on its own table / column set. See
`~/Recursive-Self-Improvement/docs/roadmap-to-v2.md` for the full
design and `references/built-2026-06-07.md` for the build notes.

| # | Signal                | What it catches                                     | Where it lives        |
|---|-----------------------|------------------------------------------------------|-----------------------|
| 3 | Cost & latency        | Slow API drift, cost creep, jobs approaching cron cap | `cycle_stats`         |
| 4 | Memory staleness      | Memory entries whose source is gone or unsent 30+d   | `stale_memory_candidates` |
| 5 | Pipeline gaps         | API timeouts, parse failures, apply errors           | `lessons_learned` (`category='gap'`) |
| 6 | Self-incidents        | Loop's own cron jobs going silent / failing / slow   | `self_incidents`      |

**Cost & latency** wraps every API call with `time.monotonic()` and
captures `usage.prompt_tokens` / `usage.completion_tokens`. The digest
shows median + p95 cycle duration and an estimated dollar cost. Catches
perf drift weeks before thomas would notice.

**Memory staleness** flags lessons in `lessons_learned` that are
either (a) older than 30 days and never sent in a digest, or (b)
reference a source session that no longer exists. Surfaced in the
proposer's prompt as "Stale memory candidates" so it can propose a
refresh or removal. Never auto-deletes.

**Pipeline gaps** is the loop telling itself about its own parse/timeout/
apply errors. Every failure writes a `lessons_learned` row with
`category='gap'`; the next proposer cycle sees them as "Pipeline
gaps" and can propose a fix (shorter transcripts, JSON-mode prompt,
better error handling, etc.).

**Self-incidents** is `incident_watcher.py` — detects when the loop's
own cron jobs (sri-propose, sri-judge, sri-apply) go silent, fail
non-zero, or run > 110s. Per-job staleness thresholds (sri-apply runs
daily → 37h; sri-propose runs 8h → 13h) account for differing
cadences. Each incident is synthesized into a "session" the proposer
| 6 | Self-incidents        | Loop's own cron jobs going silent / failing / slow   | `self_incidents`      |
| 7 | Branch isolation      | A bad apply corrupts skill files until manual fix   | `data/branches/<id>/` + `sri-branch` skill |

**Branch isolation** wraps every apply cycle in a per-cycle snapshot
of all target files to `data/branches/<cycle_id>/`. If the change
turns out to be bad, `python src/apply.py --revert <cycle_id>`
restores the original files in one command and marks all linked
`applied_outcomes` rows as `outcome='reverted'`. The
kayba-ai/recursive-improve project calls this "branch-per-cycle";
the SRI version uses filesystem snapshots instead of git branches
because the target dirs (`~/.hermes/skills/`, `~/.hermes/memories/`)
are not git repos. The artifact is `sri-branch` skill
(`~/.hermes/skills/sri-branch/SKILL.md`); the live impl is
`src/branch.py`. Without this layer, a single bad judge approval
silently corrupts user-facing skills until thomas notices manually
— the worst failure mode of the loop. The revert command is the
**manual override signal** for grading: it overrides whatever the
heuristics would say, because a human chose to undo the change.

**Combined with the two original signals, the loop now has seven
independent drift detectors.** Phase 5 also includes a
benchmarking-style keep/revert gate, but its eval is the same
applied-outcome signal as the grading heuristics — no new
information, just a more aggressive gate. The real win of Phase 5
is the blast-radius boundary, not the benchmark.

## The avoid-list (negative patterns)

Override rate answers "did the judge call it right?" but the *proposer*
also needs a signal: "stop proposing the same class of bad idea."

Mechanism: on every reject/override, write a `negative_patterns` row
with thomas's note. On the next propose cycle, inject the 10 most recent
into the proposer's system prompt under "Patterns to AVOID". The cron
agent that consumes our prompt is non-interactive, so this MUST be
baked into the prompt at construction time — you can't ask the LLM to
query the DB mid-call.

Mark patterns as `used_in_prompt_at` after injecting so the set stays
fresh. Don't re-show patterns used < 24h ago.

## Safety rails (non-negotiable)

- **Hub-installed / pinned skills are read-only.** The loop can patch
  agent-created skills but must skip anything under `~/.hermes/skill-assets/`
  or marked with a hub marker. Those need a PR upstream or an umbrella.
- **Path validation.** Refuse any target_path outside `~/.hermes/skills/`
  or `~/.hermes/memories/`. Resolve symlinks.
- **Backups before writes.** Every applied change gets a copy in
  `data/backups/<timestamp>_<name>`. This is what `grade_outcomes.py`
  reads to detect reverts — the backup dir is the audit log.
- **Idempotency.** A `DONE_<proposal_id>_<path>` marker file prevents
  re-application if the cron fires twice. Cheap, deterministic.
- **Rubric updates never auto-merge.** They go through the same
  approve/reject queue as everything else. The loop modifying its own
  judge is the riskiest move — keep a human in the loop there.

## Model choice (do not share context between proposer and judge)

The proposer and judge should be **different models** calling the API
directly, NOT the same agent in two roles. Reasons:

- A shared context window means the proposer's framing leaks into the
  judge's evaluation. You get agreement, not calibration.
- A judge model with low temperature (0.2) and a proposer with higher
  temperature (0.4) reduces correlation between their outputs.
- Override rate is meaningless if both models think alike.

In the working impl: proposer is m3 (reasoning model), judge is m2.7
(faster, conservative). Both call `https://api.minimax.io/v1/chat/completions`
directly via `urllib.request` — no shared Hermes session.

## Cron schedule (worked, not theoretical)

The loop has 6 steps but they don't all need the same cadence, and
**all cron jobs must respect the 120s `no_agent` cap**. The cycle
was originally a single `sri-cycle` job but hit the cap on 2026-06-07
when a 353-message session's propose call exceeded the budget. It is
now split into two:

- **`sri-propose` (`:00` every 8h)** — propose only. ~30-60s.
  `--propose-only` flag exits before judge.
- **`sri-judge` (`:05` every 8h)** — judge + grade. ~30-60s.
  5-min offset so propose's output is visible by the time judge runs.
- **`sri-apply-merged` (daily 04:00)** — apply approved proposals
  that didn't get applied during the cycle. Cheap, no LLM.
- **`sri-rubric-self-eval` (monthly 1st @ 10:00)** — computes
  override rate on the last 20 proposals; if high, asks m3 to propose
  a refined rubric. Never auto-merges.
- **`sri-weekly-digest` (Monday 09:00)** — sends the formatted
  digest to thomas's home Telegram channel.
- **`sri-decision-handler` (every 1 min, `--once`)** — polls
  `getUpdates` for `callback_query` taps on the digest's inline
  keyboard. Marks proposals `merged`/`rejected`, edits the digest
  message with a ✅/❌ stamp. Delivers nothing on empty polls.
  The decision step and the digest step are intentionally separate
  jobs with separate cadences: the digest is weekly, the decision
  is per-minute. The handler MUST NOT regenerate the digest — see
  the cron-prompt rule below.

**Per-call urllib timeout rule:** never higher than the cron cap itself.
30-60s per call is right. The cron cap is 120s for `no_agent` jobs;
don't let one hung LLM call blow the whole budget.

**If a single stage legitimately needs more than 90s, split it.**
Don't try to make one script do everything. The `sri-cycle →
sri-propose + sri-judge` split is the worked example. Captured in
`autonomous-ai-agents/cronjob-ops` as the "120s cron cap vs LLM
call budgets" pitfall.

## Schema (SQLite is enough; don't reach for Postgres)

```sql
-- Core: the loop's main record
CREATE TABLE proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    source_session_id TEXT,
    target_kind TEXT,           -- skill_patch|memory_add|skill_create|rubric_update
    target_path TEXT,
    diff TEXT NOT NULL,
    rationale TEXT,
    evidence TEXT,
    confidence REAL,
    status TEXT DEFAULT 'pending',  -- pending|approved|rejected|overridden|merged
    rubric_version INTEGER,
    merged_at REAL
);

-- Judge verdicts
CREATE TABLE judge_verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER REFERENCES proposals(id),
    judged_at REAL NOT NULL,
    judge_model TEXT NOT NULL,
    rubric_version INTEGER NOT NULL,
    verdict TEXT,               -- approve|reject|needs_work
    score REAL,
    reasoning TEXT
);

-- Thomas's decisions — the actual training signal
CREATE TABLE thomas_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER REFERENCES proposals(id),
    feedback_at REAL NOT NULL,
    verdict TEXT,               -- approve|reject|modify
    note TEXT,
    was_overrides_judge BOOLEAN NOT NULL
);

-- Positive patterns: lessons from the cycle
CREATE TABLE lessons_learned (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    category TEXT,              -- pattern|gap|lesson|correction
    content TEXT NOT NULL,
    source TEXT,
    sent_in_digest_at REAL      -- weekly digest marks this
);

-- Negative patterns: avoid-list for the proposer
CREATE TABLE negative_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    proposal_id INTEGER REFERENCES proposals(id),
    target_kind TEXT NOT NULL,
    target_path TEXT,
    reason TEXT NOT NULL,       -- thomas's note (or 'overridden' if blank)
    was_overrides_judge BOOLEAN NOT NULL,
    used_in_prompt_at REAL      -- last time injected into a proposer prompt
);

-- Outcome measurement: did the change actually help?
CREATE TABLE applied_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    proposal_id INTEGER REFERENCES proposals(id),
    target_kind TEXT NOT NULL,
    target_path TEXT NOT NULL,
    diff TEXT NOT NULL,
    applied_at REAL NOT NULL,
    outcome TEXT DEFAULT 'unknown',  -- unknown|helped|neutral|reverted|recorrected
    outcome_detected_at REAL,
    outcome_evidence TEXT
);

-- v2 additions — coverage-gap signals (Phases 1-4)
-- See "Four more coverage-gap signals" section for what each catches.

-- Phase 1: cost & latency per cycle
CREATE TABLE cycle_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at REAL NOT NULL,
    finished_at REAL NOT NULL,
    duration_ms INTEGER NOT NULL,
    steps TEXT NOT NULL,        -- JSON: {propose: bool, judge: bool, apply: bool, grade: bool, memory_hygiene: bool, incident_watcher: bool}
    proposals_mined INTEGER,
    proposals_generated INTEGER,
    judge_calls INTEGER,
    grade_graded INTEGER,
    grade_skipped INTEGER,
    error TEXT
);
-- And on proposals / judge_verdicts:
--   ALTER TABLE proposals ADD COLUMN propose_ms INTEGER;
--   ALTER TABLE proposals ADD COLUMN propose_input_tokens INTEGER;
--   ALTER TABLE proposals ADD COLUMN propose_output_tokens INTEGER;
--   ALTER TABLE judge_verdicts ADD COLUMN judge_ms INTEGER;
--   ALTER TABLE judge_verdicts ADD COLUMN judge_input_tokens INTEGER;
--   ALTER TABLE judge_verdicts ADD COLUMN judge_output_tokens INTEGER;
--   ALTER TABLE judge_verdicts ADD COLUMN judge_error TEXT;

-- Phase 2: stale memory candidates (no auto-delete; always queue for thomas)
CREATE TABLE stale_memory_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER REFERENCES lessons_learned(id),
    detected_at REAL NOT NULL,
    reason TEXT                 -- 'source_gone' | 'unsent_30d' | 'both'
);

-- Phase 4: self-referential incident tracking (the loop's own cron health)
CREATE TABLE self_incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at REAL NOT NULL,
    job_name TEXT NOT NULL,     -- 'sri-propose' | 'sri-judge' | 'sri-cycle' | 'sri-apply'
    incident_type TEXT NOT NULL,-- 'timeout' | 'exit_nonzero' | 'no_output' | 'wall_time_high'
    detail TEXT,
    last_log_lines TEXT
);
```

The first four tables are obvious. The last two are the difference
between "loop that produces stuff thomas approves" and "loop that
produces stuff that works." Don't ship without them.

**Schema migration pattern (v2 onwards):** don't `DROP TABLE` and
re-seed. Each new table or column lives in `_MIGRATIONS` and is run
through `try: c.execute(stmt) except sqlite3.OperationalError: pass`.
Idempotent. Safe to run on existing prod DBs. The `db.init_db()`
function calls `_migrate(c)` after `executescript(SCHEMA)`.

**Migration order trap (verified 2026-06-07):** when the SCHEMA
references columns added by a migration (e.g. a `CREATE INDEX
... ON applied_outcomes(cycle_id)` for a column the migration
adds in the same release), `_migrate(c)` MUST run **before**
`executescript(SCHEMA)`, not after. The old order (`executescript`
→ `_migrate`) fails on existing prod DBs: the index creation in
SCHEMA references a column that doesn't exist yet, executescript
aborts, and the migration never runs. Reverse the order and
fresh-installs still work because `ALTER TABLE` on a non-existent
table raises `OperationalError` which the try/except swallows as
"column already exists." The check that catches this: `python3 -c
"import db; db.init_db()"` against an existing prod DB. If it
works, migrations are correctly ordered.

**Migration order bug, round 2 — silent column loss on fresh DBs
(verified 2026-06-07):** the `_migrate` → `executescript(SCHEMA)`
order is correct for **indexes that reference migrated columns**,
but it silently breaks the **column-add migrations themselves**
on fresh DBs. The trace: `_migrate(c)` runs
`ALTER TABLE proposals ADD COLUMN propose_ms INTEGER` *before*
`executescript(SCHEMA)` runs `CREATE TABLE IF NOT EXISTS proposals
(...)`. On a fresh DB, the table doesn't exist yet → the `ALTER`
raises `OperationalError: no such table: proposals` → the
`try/except OperationalError: pass` swallows it. Then
`executescript(SCHEMA)` runs `CREATE TABLE IF NOT EXISTS proposals`
**without** the migrated column. Result: every fresh DB loses the
migrated column silently. Prod DBs are fine (table pre-exists,
`ALTER` succeeds, column is added). The bug existed since the
Phase 1 columns were added in `deefbce` and only surfaced during
a rename audit that ran the full test suite on a fresh DB.

The fix — include migrated columns in BOTH `SCHEMA` and
`_MIGRATIONS` (yes, redundant — yes, required):

```python
SCHEMA = """
CREATE TABLE IF NOT EXISTS proposals (
    ...,
    merged_at REAL,
    -- Phase 1: cost & latency tracking (also in _MIGRATIONS for existing DBs)
    propose_ms INTEGER,
    propose_input_tokens INTEGER,
    propose_output_tokens INTEGER
);
"""

_MIGRATIONS = [
    # These are now no-ops on fresh DBs (the column was created by SCHEMA)
    # and additive ALTERs on existing DBs (the column didn't exist before).
    "ALTER TABLE proposals ADD COLUMN propose_ms INTEGER",
    ...
]
```

The comment "also in _MIGRATIONS for existing DBs" on the SCHEMA
column is the load-bearing detail — it tells the next reader why
the column is defined twice. Don't remove the redundancy; the
PR review should reject any attempt to "consolidate" the two
into one source of truth.

**The canary pattern — verify column coverage on every PR that
touches `db.py`:**

```bash
python3 -c "
import sys, tempfile
from pathlib import Path
sys.path.insert(0, 'src')
import db
TEST_DIR = Path(tempfile.mkdtemp(prefix='probe_'))
db.DB_PATH = TEST_DIR / 'test.db'
db.init_db()
import sqlite3
c = sqlite3.connect(str(db.DB_PATH))
for t in ['proposals', 'judge_verdicts', 'applied_outcomes']:
    cols = [r[1] for r in c.execute(f'PRAGMA table_info({t})').fetchall()]
    print(f'{t}: {cols}')
"
```

If a column is missing, the migration is silently failing on
fresh DBs. Run this against every PR diff. The probe is ~5 lines
and catches the bug class.

## Worked example

The reference impl lives at `~/Recursive-Self-Improvement/`. Source files:

- `src/db.py` — schema + helpers (with `_MIGRATIONS` for v2 columns)
- `src/loop.py` — orchestrator (6 stages: propose, judge, apply, grade, memory_hygiene, incident_watcher)
- `src/propose.py` — proposer (m3) + avoid-list / stale-memory / pipeline-gap / self-incident injection
- `src/judge.py` — judge (m2.7) with strict JSON verdict + error capture
- `src/apply.py` — writes to skill/memory files with backups + outcome recording. Per-cycle branch snapshot via `branch.cycle_start()`.
- `src/branch.py` — Phase 5: per-cycle snapshot isolation. Snapshots every target file before `apply.py` writes; `python src/apply.py --revert <cycle_id>` rolls back the whole cycle. See `~/.hermes/skills/sri-branch/SKILL.md`.
- `src/grade_outcomes.py` — heuristic grader (revert/recorrect/neutral). Reads `data/branches/` to detect manual reverts; that directory is the source of truth for "did a human undo this."
- `src/memory_hygiene.py` — Phase 2: stale lesson detection
- `src/incident_watcher.py` — Phase 4: self-referential cron health
- `src/checkpoint.py` — judge calibration snapshot (dumps
  `override_rate_50`, `help_ratio_50`, `judge_error_rate_50`,
  `drift_score` to `data/judge_state.json` after every real cycle;
  loaded on startup; skipped on `--propose-only` and `--dry-run`).
  The loop's mirror of the in-memory-state-durability problem
  — anything you want to survive a restart has to live on disk.
- `src/self_improve.py` — monthly rubric eval
- `src/digest.py` — weekly Telegram summary (with cost / outcome / hygiene / incident sections)

**Thomas's digest format (consolidated 2026-06-08, after he explicitly asked for "a more concise digest with rules proposed / rules judged not correct and confirmations requested for me to decide upon and for you to act after decision is taken"):** The digest is a **decision surface**, not a status report. **First, diagnose** — open `data/loop.db` and run the four count queries in the pitfall below BEFORE rendering. If thomas filed the digest because of a "loop is broken" complaint, the diagnose output IS the most useful thing he can read. Then render. Five sections, in this order, each with a clear semantic role:

1. **RULES PROPOSED** — pending proposals awaiting approve/reject/modify. Each row carries the proposal id, type, confidence, target path, and the rationale truncated to a scannable length. Reply template at the bottom: `approve #N | reject #N | modify #N: <note>`.
2. **RULES REJECTED** — proposals the judge said no to. FYI; thomas does not need to act on these. Brief — id, kind, judge rationale.
3. **JUDGE-OVERRIDES** — proposals where thomas overrode the judge (or vice versa). The drift signal. Flag with ⚠ if there are multiple.
4. **CONFIRM NEEDED** — things the system can't decide on its own (drift threshold, stale log investigation, etc.). Empty state is `(none — pipeline healthy)`.
5. **CONTEXT** — pipeline numbers, self-incidents, branch counts. **FYI only** — no decision asks in this section.

**Two non-obvious rules that bit during the 2026-06-08 session:**

- **Sandbox proposals must not inflate the "applied" count.** The SRI loop's own test fixtures write to `_sri_test_skill_/` and `/tmp/sri_*/` — they show up as `merged` in the DB. A digest that says "34 applied" is misleading when 31 of those are test runs. Filter by `target_path` substring (`_sri_test_skill_`, `/tmp/sri_`) and report `3 real applied (31 test/sandbox)` so thomas can tell production activity from loop self-test.
- **`memory_add` rows have `target_path=NULL`** — they describe a memory entry, not a file. The digest should fall back to the first 1-3 lines of the `diff` (which usually starts with the memory header) so the row is identifiable without a NULL column. Without this fallback, the row reads as `target:` and looks like a bug.

**The "decisions needed" list at the top of the digest is the load-bearing part.** Thomas reads it on mobile Telegram while doing other things. The format that works for him:

```
▸ RULES PROPOSED (awaiting your decision):
  #57 skill_patch  conf=0.82  since 2026-06-07 22:01Z
    target: /home/thomas/.hermes/skills/github-repo-management/SKILL.md
    why:    User explicitly directed that credential-leak prevention should be
            a basic rule in the GitHub skill — adding a Safety section...
  Reply: approve #N | reject #N | modify #N: <note>
```

Not tables, not JSON, not raw status counts. Each line is a noun phrase he can act on. The CONFIRM NEEDED section uses the same pattern but as bullet questions — `• Update rubric, raise judge strictness, or accept drift?` — three options he can pick from.

**Why the script must own the format (not the LLM cron):** When a cron agent reads the DB and synthesizes the digest itself, two things go wrong (verified 2026-06-08): (a) it conflates `merged` with `errors` and reports a 10x-worse pipeline state than reality, (b) the format drifts between runs (no schema to enforce it). The fix: `digest.py` reads the DB, formats, and sends the Telegram message itself when `TELEGRAM_BOT_TOKEN` + `TELEGRAM_HOME_CHANNEL` are in env; the cron prompt is a thin wrapper that reports `exit 0` + `[digest] Sent N chars to <chat>`. See `cronjob-ops` → "Companion rule: when the prompt says 'trust the script's output', do not regenerate the message from the DB."
- `prompts/proposer.md` — proposer system prompt
- `prompts/rubric.md` — judge rubric (versioned in `rubric_versions`)

Full session notes and a session-by-session build log are in
`references/built-2026-06-07.md`. The v2 design spec is in
`docs/roadmap-to-v2.md` in the loop's repo.

**Worked fix transcripts** (the actual chain of patches that got the
propose step back under the 120s cron cap on 2026-06-07) live in
`references/layered-llm-budget-fix-2026-06-07.md`. Read that file
before debugging a "loop.py ran but propose produced 0" symptom —
it's almost always one of the four layers in there.

**Apply-and-reject handoff** (the operator-side steps that
`apply.py` does NOT automate — diff format conversion, the
3-table rejection write, the `was_overrides_judge` derivation)
lives in `references/apply-and-reject-handoff-2026-06-07.md`. Read
that file the first time you try to operate the loop by hand,
before you run `apply.py` on a `skill_patch` whose diff is bare
markdown. The session-2026-06-07 worked transcript of approving
proposal #1 (premortem guardrail) and rejecting proposal #3
(single-session memory entry) is in there.

**Digest rewire 2026-06-08** (the worked transcript of the
"34 errors were actually 3 real applied" hallucination, the
5-section decision-surface format, the sandbox filter, and the
cron prompt change to a thin wrapper) lives in
`references/digest-rewire-2026-06-08.md`. Read it before touching
`src/digest.py` or the `sri-weekly-digest` cron prompt — the
format philosophy and the "do not regenerate from the DB" rule
both live there, and breaking either will silently make the
digest worse even if the script exits 0.

**Inline-keyboard decision flow 2026-06-08** (the worked
transcript of adding the DECIDE stage, the `callback_data`
schema, the poller's state machine, the Modify button's "signal
intent only" semantics, the data/decision_state.json persistence
pattern, and the two `apply.py` bugs the e2e test exposed) lives
in `references/inline-keyboard-decisions-2026-06-08.md`. Read it
before touching `src/handle_decision.py`, the
`sri-decision-handler` cron prompt, or the `inline_keyboard`
markup in `src/digest.py`. The five rules in the "Five rules
that bit" section are the load-bearing details — the protocol
itself is simple, but violating any of those five turns the
button flow into a foot-gun.

**Test isolation pitfall** (the worked transcript of the 18-dummy
proposal poisoning incident, the env-var-overridable path pattern,
the import-time assert that converts silent pollution into a hard
crash, and the diagnostic that catches the bug class) lives in
`references/test-isolation-pitfall-2026-06-07.md`. Read it
before trusting any "tests pass" report for this loop — the
lesson generalizes to any system where tests and prod share a
database, skill directory, or any other per-process state path
(branch dirs, backup/marker dirs, state JSON files). The 2026-06-07
incident also fixed a "47/47 passing" false negative that had been
silently polluting the prod DB on every test run. The general rule:
a passing test in a self-modifying system is a write-vulnerability
disguised as a safety net — the test suite is part of the trust
boundary, not outside it.

## Pitfalls (learned the hard way)

- **Don't share the proposer's context with the judge.** Override rate
  becomes meaningless. Two separate API calls, two different models.
- **The "approve what thomas approves" trap.** Without the outcome
  signal, the loop can drift toward producing things that *sound* like
  what thomas wants without producing things that work. Help ratio
  is the only counter.
- **Cron jobs for self-improvement should be no_agent script-only**
  when possible. The LLM adds latency and variance; the cycle script
  is deterministic and fast.
- **Don't auto-promote rubric updates.** The rubric is policy, not
  data. A bad rubric compounds across the entire system. Always queue
  for thomas.
- **The avoid-list grows stale.** Patterns stay useful ~30 days. Add
  a TTL/age filter so 2-year-old rejections don't drown the prompt.
- **The 7-day "neutral" default is conservative.** False neutral is
  cheap; false helped is dangerous (it inflates the help ratio and
  hides real drift). When in doubt, neutral.
- **The first 3 weeks produce no outcome signal.** That's expected.
  Don't panic and disable the grader because the digest shows
  "no graded changes yet."
- **Backups are the audit log AND the revert detector.** The grader
  reads them. Don't clean `data/backups/` automatically — it's the
  loop's memory of what changed.
- **Test isolation is more than the DB path.** When patching the
  test suite to use a temp DB, audit every other per-process state
  path the loop writes to. The SRI loop has at least four:
  `data/loop.db` (DB), `data/branches/` (cycle snapshots),
  `data/backups/` (per-file backups + `DONE_<id>_<path>` idempotency
  markers), and `data/judge_state.json` (calibration snapshot).
  Each one needs its own env-var override (`SRI_DB_PATH`,
  `SRI_BRANCHES_DIR`, `SRI_BACKUP_DIR`, etc.) AND a default that
  falls back to the prod path. Skip one and tests will silently
  share state with prod on a vector you didn't think to check.
  The `DONE_<id>_<path>` marker leak is the worst case: a marker
  written by an earlier test run survives in the prod backup dir,
  breaks idempotency on a later test run with a fresh temp DB
  (new auto-increment IDs collide with the old marker), and
  `apply.run()` returns 0 silently because the proposal "was
  already done." Verified on 2026-06-07: env-var pattern covers
  it, but only if every per-process path is in the env-var list.
  See `references/test-isolation-pitfall-2026-06-07.md` for the
  full checklist.
- **Import-time assert that the env-var override took effect.**
  After setting `SRI_DB_PATH` etc. and importing `db` / `branch`,
  the test should `assert str(db.DB_PATH).startswith("/tmp/")`.
  Without the assert, an accidental reordering of `os.environ`
  and `import` statements — or a future refactor that captures
  the constant at import time in a way the env-var override
  doesn't cover — silently starts writing to prod again, and
  the test goes back to "47/47 passing" with no warning. The
  assert costs <1ms and converts the silent failure into a
  hard crash. It's the part that makes the env-var pattern
  durable across future edits. Same pattern works for any
  test that overrides global state via env vars.
- **`unmined_sessions()` can silently return 0 even with eligible
  candidates.** Symptom: loop logs "No unmined sessions" while the
  sessions dir has plenty of unmined files. Cause: the function
  scans `list_sessions(limit=limit * 4)` and stops as soon as the
  scan window is exhausted. When the top `limit*4` recent files
  are all already-mined or oversized, the function gives up before
  reaching any eligible candidate. Fix: replace the `limit * 4`
  multiplier with a generous absolute `scan_window` (e.g. 200).
  Cheap (filename glob + `was_session_mined` check), and the
  "No unmined sessions" log line is no longer silently misleading.
  Verified on 2026-06-07: after the fix, 3 candidates surfaced from
  the 13th–15th most-recent files that the old `limit*4=12` window
  never reached.
- **The LLM timeout fix is belt-and-suspenders, not one knob.** When
  the propose call starts timing out on long sessions, four fixes
  are needed together, not one: (1) bump `urllib.request.urlopen`
  timeout from 30s → 60s (the cron cap is 120s for `no_agent`;
  30-60s per call is the in-spec band — see the cron schedule
  section above). (2) chunk `load_session()` aggressively
  (head 15 + tail 15 = 30 msg cap is the worked value; 60 was too
  generous). (3) drop `max_tokens` from 4000 → 1500 (proposals are
  short JSONL; the larger headroom just lets m3 ramble past the
  budget). (4) add a hard `max_messages` filter (e.g. 200) to
  `unmined_sessions()` so very long sessions are skipped outright
  before they hit the proposer. Each fix alone is insufficient:
  bumping the timeout alone blows the cron cap; chunking alone
  still times out on a 350-msg session; lower max_tokens alone
  doesn't help if the *input* is too big; the message cap alone
  hides real signal. All four together get the cycle under budget.
  Worked order: timeout first (cheapest), then chunk cap, then
  max_tokens, then max_messages filter, then the scan_window fix
  above. See `references/layered-llm-budget-fix-2026-06-07.md`
  for the full transcript of a session that hit all four.
- **Judge parser failures get recorded as judge rejections.** When
  the judge LLM emits something the parser can't extract a verdict
  from (e.g. a `<think>` block with no JSON, or JSON wrapped in
  prose), the verdict row is written with `verdict='reject',
  score=0.0` — the parser's *failure default*, not the model's
  intent. The diagnostic is hidden in `reasoning` as
  `"[judge output unparseable: ...]"`. This silently inflates
  override-rate math: counting these as "rejections" makes the
  judge look miscalibrated when it was actually just a parse
  miss. Fix: add `parse_failed BOOLEAN` to `judge_verdicts`, set
  it to 1 on parser failure, and filter it out of every
  override-rate / approval-rate query in `digest.py` and
  `self_improve.py`. The fix-proposal mechanism is already in
  place via Phase 3 ("Pipeline gaps from last 7 days") — the
  parser just needs to write a `category='gap'` lesson when it
  fails, so the next proposer cycle can propose the column.
- **`apply.py` only matches three diff formats; raw markdown fails.**
  `_apply_unified_diff()` accepts (a) unified diffs (`--- a/...`),
  (b) `APPEND:<text>` for new content, (c) `REPLACE_ALL:<text>` for
  whole-file rewrites, and (d) the `<<<\nOLD\n===\nNEW\n>>>` block
  format. **Raw markdown fragments** (e.g. `## Pitfalls\n...`) hit
  the `_apply_patch` fallback, which calls the `patch` shell command,
  which rejects the input as malformed. The good news: failure is
  not silent — the apply step logs `  ✗ apply failed, restoring
  from backup` and writes a `category='gap'` lesson with the first
  200 chars of the offending diff. The bad news: the proposer
  prompt's `proposer.md` doesn't tell m3 to emit `APPEND:` etc., so
  the first time m3 proposes a `skill_patch` with a bare markdown
  diff, it fails. **Two equivalent fixes** (pick one, don't do
  both): (1) add diff-format instructions to `prompts/proposer.md`
  so m3 emits `APPEND:` for additive patches; (2) refactor
  `_apply_unified_diff` to detect "looks like markdown, not a
  diff" and treat it as `APPEND:` automatically. The first is
  cheaper but pushes complexity into the prompt; the second is
  robust against any future m3 output. **As of 2026-06-08 the
  second is in place** — heuristic fallback detects "no recognized
  markers, no `--- `, no `<<<` on first line" and APPENDs the raw
  text. Verified end-to-end with a synthetic approve→apply test.
  But the proposer prompt should still be updated to emit `APPEND:`
  explicitly (option 1) so the heuristic isn't load-bearing on
  every new patch.
- **The apply rollback used to crash on a missing target file
  (fixed 2026-06-08).** When the target file didn't exist when
  `apply_proposal()` reached the rollback step, `shutil.copy2(backup,
  target_p)` raised `FileNotFoundError` and **killed the whole apply
  run mid-loop** — any subsequent proposal in the same `run()` call
  was silently skipped. Cause: the apply step iterates all `merged`
  proposals; the first one to fail with a missing target crashed
  the iterator, and the rest never ran. Trigger: any test fixture
  (or manually-deleted skill file) that has a stale `merged`
  proposal. **Fix:** wrap the rollback in `try/except` and check
  `target_p.exists()` before copying. Now: a missing-target apply
  failure logs `! target <path> did not exist; nothing to restore`
  and the iterator continues. **Diagnostic that catches the bug
  class:** any time `apply.py` exits non-zero and reports N "applied"
  out of M total with M > N, the rollback is failing somewhere. Run
  with `data/backups/` clean and a synthetic merged proposal pointing
  at a non-existent path — the apply step should log the missing
  target and continue to the next proposal, not crash.
- **Inline-keyboard decision flow (added 2026-06-08):** the digest
  message carries an `inline_keyboard` with one row of
  `✅ Approve` / `❌ Reject` / `✏️ Modify` buttons per pending
  proposal. `callback_data` format is `sri:approve:<id>` |
  `sri:reject:<id>` | `sri:modify:<id>` (Telegram caps at 64 bytes;
  this is ~20). The `sri-decision-handler` cron polls `getUpdates`
  every minute, parses the callback, marks the proposal
  `merged`/`rejected` (writes `thomas_feedback` row), edits the
  digest message with a decision stamp, and `answerCallbackQuery`s
  with a toast. **Five rules that bit during implementation** (see
  `references/inline-keyboard-decisions-2026-06-08.md` for the full
  protocol): (1) The decider must lazy-reload `TELEGRAM_ALLOWED_USERS`
  on every callback — populating a module-level list at startup
  means an env-var change requires a process restart. (2) The polling
  offset + handled-callback-id set must be persisted to disk
  (`data/decision_state.json`) — otherwise a restart replays old
  callbacks and double-applies. (3) `Modify` is not a terminal
  state — the button just signals intent; thomas still replies with
  the note. (4) The Telegram `editMessageText` call only attaches
  `reply_markup` to the FIRST chunk of a multi-chunk digest, so
  buttons land with the pending-proposal section. (5) Network
  failures in `answerCallbackQuery` / `editMessageText` are logged
  and ignored — the DB transition has already happened, and a 404
  on a stale `callback_query_id` (e.g. server restart between the
  tap and the poll) must NOT roll back the DB. The state machine
  is: receive callback → DB write → best-effort Telegram call. Not
  the other way around.
- **The digest must diagnose before it renders (verified 2026-06-08
  morning digest, on the "sri-judge: nothing to judge" complaint).**
  When thomas files a complaint about a silent cron / "nothing to
  judge" / "0 graded" / "the loop seems stuck" symptom, the cron
  output alone is misleading. The right move is to open
  `data/loop.db` and check **all four** counts before assuming
  the complained-about step is the broken one:
  1. `SELECT status, COUNT(*) FROM proposals GROUP BY status`
     → if zero `pending` rows, the judge step is *correct* (it
     would say "nothing to judge"), and the symptom is upstream.
  2. `SELECT target_path, COUNT(*) FROM proposals WHERE status='merged'
     GROUP BY target_path ORDER BY 2 DESC LIMIT 10`
     → if the top rows are `/tmp/sri_*` or `~/.hermes/skills/_sri_test_skill_/`,
     the proposer is feeding the loop its own test fixtures and
     the real-skill improvement stream is empty. This is a
     *proposer* problem, not a *judge* problem.
  3. `SELECT outcome, COUNT(*) FROM applied_outcomes GROUP BY outcome`
     → if all rows are `unknown` and recent, the grader is just
     waiting for the 7-day neutral window. "0 graded" is a timing
     artifact, not a logic bug.
  4. `SELECT COUNT(*) FROM judge_verdicts WHERE verdict='reject'`
     → the raw judge count. If it tracks the merged count plus
     a small percentage, the judge is operating normally; the
     digest's 17-skipped-0-graded is `unknown` rows below the
     grading age threshold, not judge failures.
  The diagnostic output goes in the digest reply itself (it IS
  the most useful thing thomas can read when he files a
  "loop is broken" complaint), with a **default to no code
  change** unless the counts actually show a regression. The
  common-wrong-move is to start patching `judge.py` or
  `grade_outcomes.py` because the symptom is in those modules'
  stdout — the counts almost always exonerate both. Captured as
  a pitfall in the SKILL.md body on 2026-06-08 after the
  sri-judge morning digest.
- **Rejection is not a loop-automated action — the operator must
  do it manually, and it has a 3-table side effect.** `apply.py`
  only handles `status='merged'`. There is no `apply_rejection()`
  function. When the operator (thomas, or a wrapper script) records
  a reject on a proposal, the **same action** must also (1)
  `UPDATE proposals SET status='rejected'`, (2) `INSERT INTO
  thomas_feedback` with the correct `was_overrides_judge` value,
  AND (3) `INSERT INTO negative_patterns` so the next proposer
  cycle's avoid-list injection includes this pattern. Skipping
  step 3 is the most common mistake — the rejection lands in
  `thomas_feedback` and the override rate is computable, but the
  avoid-list never grows and m3 keeps proposing the same class of
  bad idea. **The right primitive** is a single helper
  `db.record_thomas_decision(proposal_id, verdict, note)` that
  does all three inserts in one transaction with the correct
  `was_overrides_judge` derivation. As of 2026-06-07 this helper
  does not exist; the operator must remember the 3-table dance.
  Next-time-you-reach-for-the-loop: write this helper first, or
  you'll repeat the mistake.

- **The apply path is no longer fully destructive (Phase 5 branch
  isolation, 2026-06-07).** Before branch.py, a bad `skill_patch`
  silently corrupted `~/.hermes/skills/<name>/SKILL.md` until the
  operator noticed and manually reverted. The only audit trail was
  `data/backups/`, but applying a revert meant `cp backup file`,
  not a single command. Now `apply.run()` calls
  `branch.cycle_start()` first; every cycle has its own snapshot
  directory and a `--revert <cycle_id>` CLI flag. The **apply
  side is one command away from recovery**; the **rejection side
  is still operator-driven** (see the pitfall above) because
  recording a rejection is a 3-table write that the loop doesn't
  have a helper for. Two different mechanisms, both necessary.
- **`needs_work` is a third verdict state, not a soft `reject`.**
  The judge's three verdicts are `approve` / `reject` / `needs_work`.
  `needs_work` means "I can't tell — give me more evidence or a
  tighter diff." When the operator then says `reject`, the
  `was_overrides_judge` computation is **True** (operator disagreed
  with the judge) — but the override isn't a judge-calibration
  failure in the usual sense. The judge didn't call it wrong; it
  refused to call it. **Recommended tracking** (not implemented
  2026-06-07): record the operator's verdict against each of the
  three judge states separately in the digest so the override rate
  decomposes into (a) approve→reject (real miscalibration), (b)
  needs_work→approve/reject (judge abstained, operator forced a
  call), (c) reject→approve (judge over-rejected). Phase 5's
  benchmark harness should add these as separate KPIs.
- **No thomas_feedback exists for proposal #1 until the operator
  records it — apply.py does not create one.** `apply.py` writes
  to `applied_outcomes` (for the grader) but never to
  `thomas_feedback`. The override-rate math needs the operator
  row to compare against. If you apply a proposal and skip the
  `thomas_feedback` insert, the loop has applied a change with
  no calibration signal — the override rate for that proposal is
  `NULL`, not `0`. Recorded as a pitfall here after the 2026-06-07
  session applied proposal #1 successfully and then had to be
  prompted to record the operator's approval afterward.
- **In-memory patches do not survive refactors.** When you patch
  a running process (gateway, daemon, hot-reload server) by
  editing a file at specific line numbers, the patch lives only
  in the running process's memory. Any subsequent upstream
  refactor that changes line numbers, moves the function, or
  restructures the file will (a) make the patch context
  unfindable if you try to re-apply, and (b) silently fail if
  the next restart loads the new code. The general rule:
  **process-memory patches are for emergencies, not durability.**
  The durable home is the source file on disk + a committed
  patch + a build/deploy step that puts the patched file in
  front of the next process start. For the SRI loop specifically:
  `apply.py` writes to disk, so any skill/memory change IS
  durable (good). But ad-hoc patches to long-running processes
  (gateway Telegram adapters, watchdog scripts in production)
  are a different beast — fix them with a committed patch +
  restart, never with a runtime edit against a live file.
  Verified on 2026-06-07 with the Telegram `send_clarify`
  button-label fix: the patch landed at
  `gateway/platforms/telegram.py:2814`, then the June 2
  refactor (`476d8d9cc`) moved `send_clarify` to line 2769 in
  the same file and split the platform into a separate plugin
  package. The patch context was gone; the in-process memory
  edit survived only because the running gateway was on the
  pre-refactor v0.15.2 build from the uv cache. Lesson: write
  the patch, commit it, push it, restart — and *then* verify.
  Don't rely on a running process to remember a fix.

 - **Verify the current source state before patching, even when you
 think a fix is needed.** A patch from a prior session can survive
 in process memory and *look* durable because the running process
 behaves correctly. But the source on disk may already contain the
 fix (committed upstream, in this case by asdlem on 2026-05-18 with
 the `str(idx + 1)` numeric labels) — meaning the urgent work is
 `git log -L` to find the commit, not a re-patch. Verified
 2026-06-07 on the Telegram `send_clarify` button-label problem:
 the supposed "missing" fix was already in
 `gateway/platforms/telegram.py:2821` (`str(idx + 1)`). The running
 gateway was on a pre-refactor v0.15.2 build in the uv cache that
 still had the old full-text labels, so a process-memory edit
 *appeared* to fix the problem, but the source tree was already
 correct. **General rule for long-running processes:** before
 patching, run `git log -L <func>:<file>` (or `git blame` on the
 specific line) to confirm the durable source matches the running
 process. If they diverge, the source wins — investigate why the
 process is on an old build (cached install, frozen venv, vendored
 copy) and fix the *build path*, not the function. If they agree,
 the patch isn't needed.
- **SQLite column names drift from intuition — check the
  schema, not your memory.** When writing a new query against
  the loop's DB, the column names that "feel right" are
  frequently wrong. Verified 2026-06-07 while building
  `src/checkpoint.py`: the queries below were each wrong on
  the first try and only worked after reading the actual
  `CREATE TABLE` in `db.py`. **Reference values for the v2
  schema** (don't trust memory; grep `db.py` if your query
  predates a migration):
  - `judge_verdicts.error` → actually `judge_error`
  - `judge_verdicts.created_at` → actually `judged_at`
  - `thomas_feedback.created_at` → actually `feedback_at`
  - `applied_outcomes.graded_at` → actually `outcome_detected_at`
  - `applied_outcomes.outcome` values are
    `helped`/`neutral`/`reverted`/`recorrected` (NOT `help`/`hurt`)
  The fast way to find the right column: `grep -n "CREATE TABLE" db.py`
  then read the lines below it. The slow way: ship a query that
  fails, debug the `OperationalError`, fix the name, repeat four
  times in one script. (Both happened.)
- **Judge calibration baseline is a process-memory state that The override-rate and help-ratio metrics
  derive from the rolling history in the DB, so they're
  durable. But the judge's *running context* (what it's been
  approving lately, what patterns it has internalized from
  recent feedback) lives only in whatever model call is in
  flight. Restart the judge process and you start cold. Same
  pattern as the Telegram patch above. **Shipped 2026-06-07
  in `src/checkpoint.py`:** after every real cycle (skipped
  on `--propose-only` and `--dry-run`), the loop dumps a
  small JSON to `data/judge_state.json` containing
  `override_rate_50`, `help_ratio_50`, `judge_error_rate_50`,
  `drift_score` (50-cycle short vs 200-cycle long), `cycles_total`,
  and `computed_at`. On startup, `loop.py` loads it and
  announces the prior state; if it's older than 24h, it logs
  a warning. The file is gitignored — it's a runtime artifact,
  not source. **Two non-obvious design choices that bit during
  implementation:** (a) `propose-only` and `dry-run` cycles
  MUST NOT write a checkpoint — they have no judge data, so
  the persisted state would be stale-by-construction. Only
  real cycles that ran the judge step are allowed to write.
  (b) The drift score is the *difference* between the 50-cycle
  and 200-cycle override rates, not the absolute rate. This
  lets the loop's proposer reason about "are we getting worse
  than the recent baseline" without needing a held-out test
  set, which is exactly what Phase 5's benchmark harness will
  add separately.

## When NOT to add a stage

Resist the urge to add a stage for every failure mode. The 4 stages
above cover 95% of value. Common over-engineering:

- **Reflection stage** where the loop critiques its own proposals.
  Adds latency, no measurable improvement over the avoid-list.
- **Eval harness for the proposer.** You can't eval the proposer
  without a ground truth. The override rate is the only proxy.
- **Auto-tuner for the rubric prompt.** You don't have enough data
  in week 1. Wait until override stats stabilize (~30+ proposals).
- **Branch-and-merge for parallel proposal streams.** Premature
  complexity. One proposer, one judge, sequential.

## Quick verification checklist

After any change to the loop, verify:

1. `python3 -c "import db; db.init_db()"` — schema applies cleanly
   to a fresh DB
2. `python3 src/grade_outcomes.py --dry-run` — grader runs without
   crashing on an empty DB
3. `python3 src/loop.py --skip-apply --dry-run` — full cycle
   completes (note: the judge call is a real API hit, expect ~30s)
4. `python3 src/digest.py` (without TELEGRAM_BOT_TOKEN) — prints
   the digest to stdout with the new section visible
5. **If you wrote or applied a proposal this session:** confirm
   `proposals.status` matches the outcome (`merged` / `rejected`),
   a `thomas_feedback` row exists, AND for any rejection, a
   matching `negative_patterns` row exists. The `apply.py` path
   does steps 1-2 of the apply side; step 3 (and the entire
   rejection path) is operator-driven. See the "Rejection is not
   a loop-automated action" pitfall above.
6. **If a `skill_patch` proposal's diff is bare markdown (no
   `APPEND:` / `REPLACE_ALL:` / `<<<>>>` markers), the apply
   step will fail.** Verify the diff format BEFORE setting
   `status='merged'` — running it through `apply.py` will fail
   cleanly but you've spent an apply cycle to learn what the
   proposer prompt should have told m3.
7. **If `apply.py` ran this session, `data/branches/<cycle_id>/`
   should exist with a `_meta.json` and snapshot files.** Verify:
   `python3 src/apply.py --branches | grep <cycle_id>`. Verify the
   revert path works: pick a cycle_id with `applied_rows > 0`,
   manually `cp` a target file to a scratch location, then run
   `python3 src/apply.py --revert <cycle_id>`, then `diff -q
   <scratch> <target>`. They should be identical. If the revert
   silently fails, check `data/branches/<id>/_meta.json` exists
   and the file mirror path matches the target.
8. **After running the test suite, verify the prod state wasn't
   polluted.** Audit every per-process state path the test could
   share with prod — not just the DB. The checklist:
   - `sqlite3 data/loop.db "SELECT COUNT(*) FROM proposals
     WHERE source_session_id IS NULL AND evidence = 't11'"`
     (or whatever signature your test fixtures use) → 0
   - `ls data/branches/ | wc -l` → unchanged from before
   - `ls data/backups/DONE_*` → no new marker files
   - `git status data/` → clean
   Zero across all four is the correct answer. Non-zero on any
   one means the test suite is leaking on that path — fix the
   test isolation (add the env-var override for that path) before
   trusting any "tests pass" report. See the "Test isolation
   is more than the DB path" pitfall above for the full
   per-process-path checklist.
9. **If you changed `digest.py` or the `sri-decision-handler` cron
   prompt, verify the end-to-end button flow.** A synthetic test
   recipe: (a) insert a test proposal with `status='pending'` in
   `data/loop.db` pointing at a real file path under
   `~/.hermes/skills/` or `~/.hermes/memories/`. (b) Run
   `bash -c 'set -a; source ~/.hermes/.env; set +a;
   python3 src/digest.py'` — confirm the output line includes
   "with K button row(s)". (c) Construct a fake `callback_query`
   dict (id, from, data, message) and call
   `handle_decision._process_callback()` directly with `dry_run=False`
   and a fake token — confirm the DB transitions to `merged`,
   a `thomas_feedback` row is written, and the
   `answerCallbackQuery`/`editMessageText` errors (HTTP 404 on the
   fake token) are logged but don't crash. (d) Verify
   `data/decision_state.json` is created with the polling offset
   and handled-id set. (e) Re-run `python3 src/digest.py` and
   confirm the test proposal is no longer in the button rows
   (because it's now `merged`). (f) Clean up: delete the test
   proposal, `applied_outcomes` row, and any test target file.

## Related skills

- `harness-framework` — generic test/eval harness builder; use this
  when you want to *test* the loop, not run it
- `skill-evolution` — mine Hermes sessions for lessons to feed this loop
- `memory-dreams` — consolidate memory in 4 phases; complementary
  signal source for the lessons table
- `codebase-porting` — when the loop generates a "implement this spec"
  proposal, this is the skill to load
- `policy-vs-data-decisions` — rubric updates ARE policy. TTL +
  quality gate + audit trail required.
- `cronjob-ops` — schedule the 4 cron jobs (cycle, apply, self-improve,
  digest) using this skill's silent-success and 5-Whys rules
