---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.2.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [plan-and-execute-workflow]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### 6. Check the Live Store, Not Just the Snapshot Files

**WHEN the symptom is "missing data" in a file-based pipeline:**

The files are a *projection* of the application's live state, not the truth. When the projection is wrong or incomplete, look for the live store before debugging the projection layer.

- **Hermes** → `~/.hermes/state.db` (SQLite) has every message ever processed
- **Crash dumps** → `request_dump_*.json` files have the full request body that was about to be sent
- **General pattern** → look for the application's primary DB, log buffer, or in-memory store

See `references/two-tier-source-of-truth.md` for the full diagnostic sequence, the "trust the session_id not the timestamp" rule, and the recovery-script pattern.

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Live store checked if data is missing from snapshot files
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

## Pitfalls

### Always Check Display State Before GUI Troubleshooting

**When the user is already in a GUI session and asks about desktop configuration (themes, GNOME settings, UI changes):**

**Don't assume headless.** The user can see a desktop. If you assume no GUI and explain what will happen "when you log in", you're wrong and will be corrected.

**Check first:**
```bash
echo $DISPLAY
ps aux | grep -i gnome | grep -v grep
ps aux | grep -i gdm | grep -v grep
```
- `$DISPLAY` set + `gnome-shell` running = active GUI session
- When GUI is present, apply `gsettings` changes immediately — they take effect on next shell reload (Alt+F2, r) or relogin

**When running gsettings fails with "invalid schema/key" errors:**
- Check if key exists first: `gsettings list-recursively | grep -i '<key>'`
- The `org.gnome.desktop.shell.extensions.user-theme` key may not exist in all GNOME configurations
- `org.gnome.desktop.interface gtk-theme` and `org.gnome.desktop.interface icon-theme` are the reliable ones
- Run one `gsettings` command per terminal call when diagnosing — don't chain with `&&` if you need to isolate which call fails

**Why this matters:** `gsettings` modifies the user's GNOME dconf database. It succeeds silently. If the wrong theme is set (or an invalid key is silently ignored), the user sees no change and assumes it didn't work. Verify the key was set: `gsettings get org.gnome.desktop.interface gtk-theme`.

### API Endpoint URL Verification

**When debugging API connectivity, authentication, or "invalid API key" errors:**

1. **Verify the API base URL first.** A wrong endpoint URL will produce the exact same error as a bad key — a 401/403. Don't assume the configured URL is correct.
2. **Test the endpoint directly with curl** — don't trust the application's error message alone. Pass the same key and a minimal request body.
3. **Check for URL variants.** Some providers have multiple valid endpoints:
   - `api.minimax.io` vs `api.minimaxi.com` (both may exist, only one works)
   - `/anthropic/v1` vs `/v1` path differences
   - Regional vs global endpoints
4. **Compare against working configurations.** Search other configs in the same project (e.g., Hermes config uses `api.minimax.io` correctly — use it as reference).
5. **Fix the URL in the application config**, then re-test. Don't waste time rotating keys when the URL is wrong.

### API Key Propagation (Complementary to URL Verification)

**When `api_key client option must be set` or `OPENAI_API_KEY` errors appear** in an application that uses an OpenAI-compatible client with a third-party provider (MiniMax, Azure, etc.):

1. **The error is accurate** — the application's client wasn't instantiated with the key. But the fix isn't always "set the env var in your shell."
2. **Map where the application reads credentials:**
   - Gateway services (Hermes, etc.) often read from their OWN env files, not the shell's env
   - Check `~/.hermes/.env` — this is where Hermes gateway reads `MINIMAX_API_KEY`, not `$HOME/.bashrc` or shell dotfiles
   - Check systemd service files: `Environment="VAR=value"` lines in the `[Service]` block
   - Check `~/.config/environment.d/*.conf` for user-level env vars
3. **Verify what's actually running:** `systemctl --user show hermes-gateway | grep Environment` — shows the exact env the service sees
4. **Test the key directly** with curl against the provider's endpoint — don't trust the app's error message alone
5. **Journalctl is your friend** — `journalctl --user -u hermes-gateway | grep -i "api.key\|error\|traceback"` reveals auth failures the terminal session won't show

**API errors checklist (add to above):**
- [ ] Confirm key is in the application's env source (not just shell)
- [ ] Check systemd service Environment lines
- [ ] Test key directly with curl against provider endpoint
- [ ] Check journalctl for gateway-level auth errors

**Checklist for API errors:**
- [ ] Confirm API base URL is correct by testing with curl
- [ ] Try alternative URL variants if direct test works
- [ ] Compare against known-working configs in the same environment
- [ ] Fix URL before rotating/regenerating API keys

### Target Ambiguity in Review Tasks

**When asked to "review the codebase and identify/implement fixes":**

Before spending time inspecting, confirm which codebase is the target. This prevents wasted investigation on the wrong repo.

**Failure mode:** User has multiple repos cloned (e.g., `~/jcode` + `~/Desktop/hermes-agent`). "Look at your codebase" is read as "hermes-agent" but the agent spends 7 minutes inspecting `~/jcode` (a different project) before realizing the mismatch.

**Checklist before starting a codebase review:**
1. User said "your codebase" — but which project? Check `~/` for recently cloned repos
2. If multiple candidates exist, ask: "Which codebase — [repo1] or [repo2]?"
3. If the user just installed/cloned something new in this session, that context may indicate intent

**Self-initiated reviews (agent starts without being asked):** Even when YOU initiate the review
(e.g., "look at your codebase and identify fixes"), check the working directory first. If you are
in a directory that has a recently-cloned repo different from your primary codebase, confirm intent
before spending time inspecting. The user may have just installed something new as a separate
project. Example: `ls -t ~/` (most recently modified dirs) can reveal what the user is currently
working on.

This applies when "your codebase" could mean multiple things. When only one candidate exists
(e.g., `hermes-agent` is clearly the only project the agent operates from), proceed normally.

### Codebase Audit Pattern: Verify Before Declaring Broken

When doing a repository audit ("any ideas for fixes?", "what's broken?", "find issues"), the instinct is to look for gaps — but many things are already implemented in ways not immediately obvious. Before flagging something as missing, verify:

**Always check source before claiming broken:**
```bash
# Search for existing implementation before declaring absent
grep -rn "pattern_name\|function_name\|endpoint" src/ --include="*.rs"
```

**Common audit traps:**
- Tool module exists in `src/tool/` → check if it's wired into `Registry::new()` in `tool/mod.rs` before assuming dead code
- HTTP endpoint "missing" → check `gateway.rs` for existing routes; WebSocket paths often have HTTP counterparts
- "Stub" file with few lines → compare to platform equivalent; Unix transport may be 19 lines vs Windows 421 lines because Unix has native primitives that Windows lacks — the small file is correct, not broken
- Library not used → check `Cargo.toml` workspace deps and `mod.rs` exports; integration may be via dependency, not direct import

**Audit checklist before declaring a gap:**
1. ✅ Search source for existing implementation (don't grep from memory)
2. ✅ Compare platform variants (Unix vs Windows, macOS vs Linux) — different line counts ≠ broken
3. ✅ Check registry/module wiring (a module exists but may be registered differently)
4. ✅ Check git log / recent commits for recently completed work
5. ✅ Verify the definition of "wired" — may be registered in a different layer than expected

**Output format for audits:**
```
### Verified (already implemented)
- [item] → already exists at [path:line], confirm this is what was asked for
- [item] → looks incomplete but is correct for platform reasons: [explanation]

### Actually missing / needs work
- [item] → not found, confirmed absent
- [item] → partially implemented, gap is [specific]
```

### Bug Report Triage: Real Bugs vs. False Alarms

**The pattern:** User asks "any bug fixes?" or submits a bug list. Some items are real bugs. Others are: security working as designed, validators catching pre-corruption, agent mistakes logged as errors, or stale log entries from already-fixed issues. Fixing the false alarms is wasted work; ignoring the real ones is negligent. The audit must distinguish them.

**Output format (use this verbatim):**
```
BUGS FIXED: [N] ([one-line description of each])
FALSE ALARMS INVESTIGATED: [N] ([one-line: e.g. "security working", "validator saving us from corruption", "agent hallucination", "stale log entry"])
```

**How to triage each item:**

1. **Security blocks (CSL policy, hardline blocklist, redaction):** Working as designed. The "error" is the system succeeding. Never "fix" these — log them as false alarms.
2. **Pre-validation rejections** (e.g. "Patch would break SKILL.md structure: YAML frontmatter parse error"): The validator saved a corrupt write. Not a bug — the validator is the fix. Verify by reading the validator code (`grep -rn "Patch would break" --include="*.py"`) and confirming it rolls back on failure.
3. **Stale log entries:** Check the timestamp. If the log entry is from a session that already fixed the issue, the "bug" was the user's pain at the time but is resolved.
4. **Agent mistakes logged as errors:** "old_string not found", "BLOCKED recursive delete", "Foreground backgrounding" — these are agents misusing tools. Not code bugs.
5. **Hallucinated identifiers:** When an error says "Skill X not found" or "Module Y doesn't exist" and `grep` finds no reference to X or Y in the codebase, the agent that emitted the error invented the name. Check the audit log to find the actual session and confirm.

**Time budget:** Spend 60 seconds on each candidate bug. Read the validator/handler code, check git log, grep the codebase. If you can't find evidence it's a real bug within 60 seconds, it's a false alarm — move on.

**Reference file:** `references/bug-report-triage-patterns.md` for the catalog of common false-alarm patterns (security blocks, pre-validation rejections, stale logs, agent mistakes).

### Pitfall: "Implement All" — Batch-Execute With todos, Not Sequentially

**When the user says "implement all", "do all of them", "fix everything", or lists 3+ items to address:**

The temptation is to execute them one by one without tracking. This drops items, hides progress, and produces no audit trail.

**Rule:**
1. **First turn after the list:** `todo` with one item per `id`, status `pending` for all, mark the first as `in_progress`. This is the audit trail.
2. **Each completion:** mark item `completed` immediately. If something fails, `cancelled` + add a revised item — don't silently skip.
3. **Final turn:** summary in the format above (`BUGS FIXED: N / FALSE ALARMS INVESTIGATED: N`). The user gets a one-glance verdict.

**Anti-pattern:** Doing 3+ items, then summarizing at the end without todo tracking. Items get dropped, the user can't see progress, and the "summary" becomes a status report instead of a verified result.

**When this doesn't apply:** Single-item tasks. A todo list of one item is overhead.

### Pitfall: "Cron Shows Active and OK but Nothing is Happening"

**The pattern:** A cron job's `[active]` and `last_status: ok` are signals about the *cron layer*, not the *script layer*. The cron can be perfectly healthy while the script it invokes is silently misconfigured, pointing at the wrong path, swallowing errors, or matching zero of the files it should.

**Real example (June 2026):** A `session-to-obsidian watchdog` cron was `[active] last_status: ok` every 15 minutes. But `~/.hermes/sessions/` was full of `.jsonl` files the watcher's glob patterns didn't match (it only knew `.json`). 63 sessions silently fell through. The state file's newest entry was 5 days older than the newest source file — a clear "pipeline is broken" signal that the cron-ok check missed.

**Rule:** For each cron with a state file, **cross-check the state file's newest mtime against the source dir's newest file mtime.** If state < source, the watcher has been silently dropping data. See `references/two-tier-source-of-truth.md` (for the data-recovery side) and `hermes-housekeeping/references/cron-silent-failure.md` (for the full 4-pattern debugging recipe).

**When this DOESN'T apply:** Cron jobs that don't have a state file (one-shot scripts, simple periodic tasks) — those are self-evidently working from the exit code alone.

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does this make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

### 5 Whys Analysis

*Absorbed from `5-whys-analysis` — see that skill's full content for the complete diagnosis + fix workflow.*

### The Two Phases

1. **Diagnose** — 5 Whys iteration until root cause is reached
2. **Fix** — apply targeted fixes for each identified cause, in dependency order

### 5 Whys Iteration

For each "why", write:
- The question
- The answer (observable fact, not speculation)
- The next "why" triggered

Stop when:
- A concrete root cause is reached (no further "why" applies)
- Something outside your control to fix

### Fix by Cause Type

| Cause type | Fix approach |
|---|---|
| Code bug | Patch the file directly |
| Missing file | Create it with correct content |
| Wrong config | Patch the config |
| Permission/ownership | `sudo chown` or `chmod` via terminal |
| Missing dependency | Install or document installation |
| Data corruption | Overwrite with corrected data |
| Environment issue | Export env var or patch shell config |
| External service bug | Document + suggest workaround |

**Critical rule:** Fix causes in dependency order. If cause B exists because cause A exists, fix A first.

### Output Format

```
## 5 Whys Analysis

### Why 1
**Q:** Why [symptom]?
**A:** [Observable fact]

### Why 2
**Q:** Why [answer from Why 1]?
**A:** [Observable fact]

### Root Cause
[Final root cause]

## Fixes Applied

| # | Cause | Fix | Verified |
|---|---|---|---|
| 1 | [cause] | [what was done] | ✅/❌ |

## Residual Issues
[Any causes outside scope to flag to Thomas]
```

### Auto-Fix Wrapper for no_agent Cron Scripts

For `no_agent=true` cron jobs, the script should carry embedded 5-whys auto-fix logic:

```bash
#!/bin/bash
FAIL_FILE="/tmp/$(basename $0).fail"
PYTHON="/home/thomas/Desktop/hermes-agent/.venv/bin/python3"

output=$($PYTHON /path/to/scenario.json 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    rm -f "$FAIL_FILE"
    [ -n "$output" ] && echo "$output"
    exit 0
fi

# 5-whys auto-fix: common deterministic failures
# ModuleNotFoundError → install dep and retry
if echo "$output" | grep -q "ModuleNotFoundError"; then
    MODULE=$(echo "$output" | grep -oP "No module named '\K[^']+")
    if [ -n "$MODULE" ]; then
        uv pip install --python "$PYTHON" "$MODULE" 2>/dev/null
        output=$($PYTHON /path/to/scenario.json 2>&1)
        exit_code=$?
        [ $exit_code -eq 0 ] && rm -f "$FAIL_FILE" && echo "$output" && exit 0
    fi
fi

# Retry didn't work — write fail file for agent diagnosis
echo "$output" > "$FAIL_FILE"
exit $exit_code
```

**Always use the explicit venv Python path**, never bare `python3`.

### Embedded Auto-Fix in Sandy Scenarios

See `scripts/sandy-auto-fix-wrapper.sh` for the reusable wrapper. See `5-whys-analysis` skill for the full auto-fix script.

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Non-Code Investigation (Patterns, Ciphers, Unknown Signals)

The 4-phase approach applies to ANY investigation where root cause is unknown:

- **Phase 1:** Gather evidence (measure angles, radii, pixel values, frequencies)
- **Phase 2:** Identify patterns (uniform spacing, repeating structures, anomalies)
- **Phase 3:** Form hypothesis (this pattern suggests encoding method X)
- **Phase 4:** Test all decoding schemes methodically

### Standard Cipher Decoding Reference

When decoding unknown patterns, test these in order:

| Method | What it does | When to use |
|--------|--------------|-------------|
| Caesar shift | Letter substitution with fixed offset | Pattern looks like gibberish but simple letter frequency |
| Atbash | Reverse alphabet (A↔Z, B↔Y) | Pattern has symmetry |
| Vigenere | Polyalphabetic with repeating key | Pattern longer than ~20 chars with repeated fragments |
| Rail fence | Zigzag read through | Short patterns with repeating structure |
| Base-N conversion | Numbers as base-N → letters | Numbers 0-360 from angles/radii |
| Binary→ASCII | Bits grouped into bytes | Geometric data (circles, lines) that could be bits |
| Musical notes | Letter positions mapped to scale notes | Harmonic/cyclical data |
| GPS coordinates | Letter sums → lat/lon | Patterns with 30+ elements |

### Known Plaintext Testing

If the pattern is FROM a known source with a claimed solution:
1. Apply the decoded output against the claimed plaintext
2. If match → cipher identified
3. If no match → try different key on same cipher

### Stopping Rules

- If 5+ encoding methods produce no meaningful pattern → document the attempts in `references/crop-circle-decode-attempts.md` and conclude "non-standard encoding or no embedded message"
- Always note what WAS tried so future sessions don't repeat failed approaches
- For Hermes codebase reviews: `references/hermes-agent-findings.md` has verified findings — use it before generating findings from scratch

### Perl Module Installation Workaround

When a Perl module's `Makefile.PL && make install` fails with man-page permission errors and all `PREFIX`/`INSTALLMAN*DIR` workarounds still hit hardcoded paths, bypass the Makefile entirely. Use `ExtUtils::Install` directly to copy `blib/lib` to a user-writable directory:

```bash
perl -I. -MExtUtils::Install -e 'install({ "blib/lib" => "$HOME/perl5/lib" })'
```

See `references/perl-module-install.md` for the full step-by-step and why Makefile approaches fail.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**
- **"I already know the answer — no need to re-load the skill"** (you don't know, load it)
- **"This is a different task, the skill's pitfalls don't apply"** (they probably do)

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Pitfalls

### The Skill Library Already Has the Answer — Load It First

**The meta-trap:** When the user (or a prior session, or a compaction summary) describes a problem and your context says "this is the kind of thing skill X covers," it is tempting to start reasoning from scratch instead of `skill_view(name=X)` first. The compaction summary pattern from 2026-06-03 and the re-derivation of fork-staleness from 2026-06-03 are the same failure: treating context as authoritative instead of treating the skill library as authoritative.

**Symptoms you're falling into this:**
- A skill name is mentioned in conversation ("cronjob-ops handles this") and you proceed without `skill_view`-ing it
- You are about to write a long explanation of "how this works" but you have not loaded the skill that already documents it
- You feel like you're "re-discovering" something the user already established earlier
- A prior session or a compaction summary described work as "done per skill X" and you trust the description instead of loading skill X to verify

**Rule:** When a relevant skill is named, **load it first** (`skill_view(name=X)`), read the frontmatter description, scan the pitfalls section, then act. This is faster than re-deriving and prevents you from rediscovering the same traps the skill is designed to prevent.

**Real cost of skipping this step (June 2026):** In a single session, the agent (1) re-derived the fork-staleness detection pattern from scratch (the `cronjob-ops` skill already had it as a documented pitfall with full recipe), (2) re-derived the PR-branch-rebase-after-fork-sync property (`github-pr-workflow/references/pr-branch-rebase-after-fork-sync.md` already documents the byte-identical-after-rebase observation), (3) re-derived the "verify REPOS path actually points at the canonical clone" rule. All three were skills the agent had access to. Loading them at session start would have saved ~15 minutes of redundant investigation and produced a more accurate audit.

**Anti-pattern:** "The skill is referenced in memory, I don't need to re-read it" — WRONG. Skills are versioned, the frontmatter description, trigger conditions, and pitfalls section are the operative parts. Re-reading takes 5–10 seconds and is cheaper than rediscovering.

**When this DOESN'T apply:** If the task is genuinely novel, no existing skill covers it, or you have already loaded the relevant skill in this session and read the pitfalls section. Don't load skills reflexively just to load them — load when the skill name has been mentioned or the territory is suspect.

### Pitfall: "Residual Cascade After Root-Cause Fix"

**The pattern:** You identify the root cause, apply the fix, and verify it. But the root cause was *also* a dependency for N other things that now silently break in cascade.

**Symptom signature:**
- You fixed X. X was working when it depended on Y. Y is now gone/moved/wrong.
- A wave of follow-on failures (cron jobs, scripts, hooks, tests) report the same root error: "X is broken" — but they were each broken differently because they each consumed a different facet of Y.
- You can grep for the old state and find a list of consumers.

**Real example (June 2026):** Removed the `~/Desktop/hermes-agent` clone (a stale dev checkout). This was the right root-cause move — the watchdog had been auto-committing to the wrong clone. But 11 `*_sandy.sh` cron wrapper scripts (and `google_calendar_login.py`'s shebang) had hardcoded paths to `~/Desktop/hermes-agent/.venv/bin/python3`. They all broke silently — the cron sandboxed environment swallowed the bash `python3: No such file or directory` errors, and the user only saw one notification at a time.

**Rule:** After applying a root-cause fix that **removes or relocates a resource** (a file, a path, a binary, a service, a config key), sweep the filesystem for *consumers* of the old state before declaring done:

```bash
# Example: removed /home/thomas/Desktop/hermes-agent (a clone the cron pointed at)
grep -rln "Desktop/hermes-agent" ~/.hermes/scripts/ ~/.hermes/skill-assets/ ~/.hermes/sandy/ ~/.hermes/cron/ 2>/dev/null

# Generalize: replace the literal with the path/config that just changed
grep -rln "<removed-resource>" <places-that-could-reference-it>
```

**Why this is its own pitfall (not just "be thorough"):** The root-cause fix can succeed *and* leave residual damage that's silent until later. The watchdog cron ran every 30 minutes and only the most recent failure is escalated to the user; the older 10 broken scripts would have surfaced one-by-one over the next 10 cron ticks if not caught. Sweep and batch-fix.

**Companion action:** After sweeping, do a `cronjob action='list'` and check the `last_status` field of every job. The freshly-fixed jobs will show `last_status: "error"` from the run that happened *before* the fix; the dry-run returns 0; the next scheduled run will confirm clean. Don't conclude success from "my dry-run worked" alone — confirm via the next scheduled run, or at minimum check that the *current* run produces the expected output (not a previous run's cached error).

## Common Rationalizations

| Excuse | Reality |
|--------|--------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix that" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Language-Specific Debuggers

*Absorbed: `python-debugpy`, `node-inspect-debugger`, `debugging-hermes-tui-commands` — see reference files for full content.*

### Python Debugging

Quick reference — for full guide see `references/python-debugpy.md`:

| Tool | When |
|------|-------|
| `breakpoint()` + pdb | Local, interactive, simplest |
| `python -m pdb` | No source edits needed |
| `debugpy` | Remote / headless / attach to running process |

```bash
# Add breakpoint() in source, run normally
python path/to/script.py
```

### Node.js Debugging

Quick reference — for full guide see `references/node-inspect-debugger.md`:

```bash
# Inspect paused on first line
node inspect path/to/script.js

# Attach to running process
kill -SIGUSR1 <pid>
node inspect -p <pid>

# CDP programmatic (for automation)
kill -p $pid
node /tmp/cdp-debug.js
```

### Hermes TUI Debugging

For full guide see `references/debugging-hermes-tui-commands.md`.

Key: Hermes slash commands span Python backend → TUI gateway → Ink frontend. When autocomplete works but the command doesn't fire, one layer is out of sync.

```bash
# Check if command is in the TUI frontend
search_files --pattern "commandname" --file_glob "*.ts" --path ui-tui/

# Check Python backend
search_files --pattern "commandname" --path hermes_cli/commands.py
```

### Hermes-Specific Process Debug Reference

| Process | Debug tool |
|---------|------------|
| `_SlashWorker` subprocess | `python-debugpy` (Python) |
| `tui_gateway` subprocess | `python-debugpy` (Python) |
| ui-tui (Ink/React) | `node-inspect-debugger` |
| Gateway (`gateway/run.py`) | `python-debugpy` + `remote-pdb` |
| Tests | `python-debugpy` with `-p no:xdist` |

**"Windows too small" TUI freeze:** The TUI uses Rich for rendering. Wide content exceeds terminal buffer → blocks. Kill the process and resize. Prevent with `textwrap.wrap()` or `Constraint.FILL` on wide tables.

## Quick Reference

|| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
|| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow, check live store if data is missing | Understand WHAT and WHY |
|| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
|| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
|| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run single commands; one tool call per command
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### execute_code for Multi-Step Tool Sequences

When debugging requires 3+ tool calls with conditional logic between them (filter, branch, loop), use `execute_code` instead of terminal. It runs a Python script that calls Hermes tools directly with retry logic and conditional branching — all in one LLM call rather than 4-5 separate terminal calls.

```python
# Example: find files modified today, filter to .py, check test coverage, report
execute_code(code="""
from hermes_tools import terminal, search_files
import os
# ... full logic with loops, conditionals, retries built in
""")
```

**Rule:** terminal() for single commands, execute_code for 3+ steps with processing logic.

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression
