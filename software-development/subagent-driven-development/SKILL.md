---
name: subagent-driven-development
description: "Execute plans via delegate_task subagents (2-stage review)."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review, test-driven-development]
---

# Subagent-Driven Development

## Overview

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## When to Use

Use this skill when:
- You have an implementation plan (from writing-plans skill or user requirements)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

**vs. manual execution:**
- Fresh context per task (no confusion from accumulated state)
- Automated review process catches issues early
- Consistent quality checks across all tasks
- Subagents can ask questions before starting work

## The Process

### 1. Read and Parse Plan

Read the plan file. Extract ALL tasks with their full text and context upfront. Create a todo list:

**Important — confirm the correct workspace before dispatching:** If the plan file is in a different
directory than your primary codebase (e.g., `~/jcode/plans/` vs `~/Desktop/hermes-agent/`), verify
which project is the intended target before dispatching any subagent. A subagent dispatched with
the wrong workspace context wastes time inspecting the wrong codebase. Use `ls -t ~/` to check
recently-cloned repos if there's ambiguity about which project the user wants worked on.

```python
# Read the plan
read_file("docs/plans/feature-plan.md")

# Create todo list with all tasks
todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

**Key:** Read the plan ONCE. Extract everything. Don't make subagents read the plan file — provide the full task text directly in context.

### 2. Per-Task Workflow

For EACH task in the plan:

#### Step 1: Dispatch Implementer Subagent

Use `delegate_task` with complete context:

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

#### Step 2: Dispatch Spec Compliance Reviewer

After the implementer completes, verify against the original spec:

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

**If spec issues found:** Fix gaps, then re-run spec review. Continue only when spec-compliant.

#### Step 3: Dispatch Code Quality Reviewer

After spec compliance passes:

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] Adequate test coverage?
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

**If quality issues found:** Fix issues, re-review. Continue only when approved.

#### Step 4: Mark Complete

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

### 3. Final Review

After ALL tasks are complete, dispatch a final integration reviewer:

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

### 4. Verify and Commit

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

## Task Granularity

**Each task = 2-5 minutes of focused work.**

**Too big:**
- "Implement user authentication system"

**Right size:**
- "Create User model with email and password fields"
- "Add password hashing function"
- "Create login endpoint"
- "Add JWT token generation"
- "Create registration endpoint"

## Red Flags — Never Do These

- Start implementation without a plan
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Skip scene-setting context (subagent needs to understand where the task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance
- Skip review loops (reviewer found issues → implementer fixes → review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues

## Handling Issues

### If Subagent Asks Questions

- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

### If Reviewer Finds Issues

- Implementer subagent (or a new one) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

### If Subagent Fails a Task

- Dispatch a new fix subagent with specific instructions about what went wrong
- Don't try to fix manually in the controller session (context pollution)

## Parallel Multi-Audit Delegation

For large codebases with distinct areas (gateway/, tools/, agent/, cron/, etc.), dispatch
auditor subagents in parallel rather than sequentially. Each subagent focuses on one area
with its own scope and trigger list. Collect findings, deduplicate, then implement fixes
in priority order.

```python
# Audit a large codebase across 3 areas simultaneously
delegate_task(goal="Audit /home/thomas/Desktop/hermes-agent/gateway/ for bugs...", toolsets=['terminal', 'file'])
delegate_task(goal="Audit /home/thomas/Desktop/hermes-agent/skills/ for bugs...", toolsets=['terminal', 'file'])
delegate_task(goal="Audit /home/thomas/Desktop/hermes-agent/tools/ for bugs...", toolsets=['terminal', 'file'])
```

**Then** follow up with targeted file reads on specific findings and implement fixes.

**Key lesson from experience:** If the plan file is in a different directory than your primary
codebase (e.g., `~/jcode/plans/` vs `~/Desktop/hermes-agent/`), verify which project is the
intended target before dispatching any subagent. A subagent dispatched with the wrong workspace
context wastes time inspecting the wrong codebase.

## Long-Running Subagent Strategy

**The 1200s timeout is a hard ceiling (20min).** For tasks expected to exceed this:
- Write GOAL.md + USER_STORIES.md first (stories = done-ness definition)
- Set up a watchdog cron every 1h (`no_agent=true`, silent on no-change, delivers to Telegram)
- Dispatch with complete current state so the subagent can resume from checkpoint
- After timeout: code is on disk, watchdog fires within 60min, human relaunches with resume context

For the full pattern with resume templates, watchdog script, and story validation check, see:
- **`references/long-running-autonomous-tasks.md`** — implementation of the 3-session timeout recovery pattern
- Set `notify_on_complete=true` on the terminal call that spawns the long-running work
- OR use a cron job to poll progress at intervals (preferred for multi-hour work)
- The subagent will be interrupted at 600s — design the task so it can resume from checkpoint

**When the parent session also has a 600s budget:** If the parent turn also risks timeout before the subagent completes, the parent should:
1. Launch the subagent and set a cron job to monitor progress (`cronjob action='create'` with `no_agent=true` script checking file timestamps)
2. Exit immediately — the cron job delivers status reports on schedule
3. The cron job itself should use `notify_on_complete=true` in the terminal tool if it runs a command, or set a short-interval recurring cron for status polling

**Timeout configuration (critical):** Default per-subagent timeout is **600 seconds (10 minutes)** — too short for any non-trivial implementation work. For complex multi-phase builds, extend to 1200s in `~/.hermes/config.yaml` under `delegation.child_timeout_seconds`, then restart gateway (`systemctl --user restart hermes-gateway`). A 20-minute window is sufficient for most implementation tasks; 10 minutes causes mid-phase interruptions.

**Status cron pattern (used for multi-hour builds):**
- Create recurring cron at "every 1h" with `no_agent=true` script: `find /project -type f -newer /tmp/lastcheck 2>/dev/null | head -20 && touch /tmp/lastcheck`
- Script runs quickly (seconds), reports what files changed since last run
- Deliver to Telegram so user gets hourly progress without parent session involvement

## Pitfall: Check for Existing Ports Before Rewriting from Scratch

Before building a cross-platform rewrite of any significant application, check for existing production-quality ports first. A from-scratch rewrite of a 7,637-line macOS app produced a 3,555-line WPF port with critical gaps — while a pre-existing clicky-win (PySide6, 3,810 lines) was significantly more complete and production-ready.

**The pattern:**
1. User wants "1:1 rewrite of X for platform Y"
2. Agent starts from scratch without checking if a port already exists
3. Result: inferior to existing port in completeness, structure, and polish

**When this applies:** Any time the user says "rewrite for Windows", "port to X", "make work on Y", or asks to replicate another platform's app. The investigation phase must include a brief check for existing ports on the target platform before committing to from-scratch implementation.

**Why this matters:** Existing ports benefit from months of real-user bug reports, production hardening, and iteration. A fresh rewrite starts at zero. For example, a PySide6 clicky-win already had full CompanionManager, proper hotkey detection, streaming transcription, SSE parsing, waveform visualization, fly-to animation, multi-monitor support, and a test suite — none of which were complete in the WPF rewrite after 20 minutes of subagent time.

**The correct sequence:**
1. User says "1:1 rewrite of Clicky for Windows"
2. Spike investigation reads ALL original source files (25 Swift files, 7,637 lines)
3. **Also** check for existing Windows ports — GitHub search + clone any candidate
4. Compare: existing port vs from-scratch rewrite quality/time
5. Choose the better path, document the decision

**Investigate thoroughly first** — Thomas's bar for "done" is exhaustive, not approximate. When he says "don't make shortcuts or summarize, go deep in the investigation", treat it as a standing instruction for any codebase investigation task. This means: read every file, complete coverage is non-negotiable, map every subsystem before declaring complete. The clicky investigation confirmed 25 Swift files (7,637 lines) before writing the SPEC — that level of rigor is the standard.

**Resume-from-checkpoint pattern for timed-out subagents:**
```
# After timeout, check what exists
ls -la /target/project/

# Dispatch fresh subagent with exact context of what exists
goal="Continue implementation — phases 1-4 already exist. Resume from Phase 5..."
context="Existing files: [list], what's done: [what timeout report said], remaining: [remaining phases]"
```

**Status cron pattern (used for multi-hour builds):**
- Create recurring cron at "every 1h" with `no_agent=true` script: `find /project -type f -newer /tmp/lastcheck 2>/dev/null | head -20 && touch /tmp/lastcheck`
- Script runs quickly (seconds), reports what files changed since last run
- Deliver to Telegram so user gets hourly progress without parent session involvement

## Handling Repository Inaccessibility

**When browser_navigate to a GitHub repo times out:**
1. Check memory for prior context about the repo (session_search or memory read)
2. If the repo was already cloned or analyzed in a previous session, use that context directly
3. If the repo is new, retry once — transient timeouts are common
4. If retry fails, note the inaccessibility and work from what can be determined externally

**GitHub repo deep-dive without cloning:**
- `gh repo clone owner/repo` via terminal as first approach (faster, more reliable than browser)
- Then `find . -name "*.swift" -o -name "*.py" | head -50` to inventory
- `wc -l **/*.swift` for line counts
- `read_file` all key files directly from the local clone

**Never spend a tool call retrying browser_navigate on a GitHub repo that timed out once** — use `gh clone` or `wget` instead.
- Parallel: code review / bug audit across multiple distinct directories or modules
- Sequential: tasks that depend on each other's output (implementation plans)

**Why fresh subagent per task:**
- Prevents context pollution from accumulated state
- Each subagent gets clean, focused context
- No confusion from prior tasks' code or reasoning

**Why two-stage review:**
- Spec review catches under/over-building early
- Quality review ensures the implementation is well-built
- Catches issues before they compound across tasks

**Cost trade-off:**
- More subagent invocations (implementer + 2 reviewers per task)
- But catches issues early (cheaper than debugging compounded problems later)

## Integration with Other Skills

### With writing-plans

This skill EXECUTES plans created by the writing-plans skill:
1. User requirements → writing-plans → implementation plan
2. Implementation plan → subagent-driven-development → working code

### With test-driven-development

Implementer subagents should follow TDD:
1. Write failing test first
2. Implement minimal code
3. Verify test passes
4. Commit

Include TDD instructions in every implementer context.

### With requesting-code-review

The two-stage review process IS the code review. For final integration review, use the requesting-code-review skill's review dimensions.

### With systematic-debugging

If a subagent encounters bugs during implementation:
1. Follow systematic-debugging process
2. Find root cause before fixing
3. Write regression test
4. Resume implementation

## Example Workflow

```
[Read plan: docs/plans/auth-feature.md]
[Create todo list with 5 tasks]

--- Task 1: Create User model ---
[Dispatch implementer subagent]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, 3/3 tests passing, committed.

[Dispatch spec reviewer]
  Spec reviewer: ✅ PASS — all requirements met

[Dispatch quality reviewer]
  Quality reviewer: ✅ APPROVED — clean code, good tests

[Mark Task 1 complete]

--- Task 2: Password hashing ---
[Dispatch implementer subagent]
  Implementer: No questions, implemented, 5/5 tests passing.

[Dispatch spec reviewer]
  Spec reviewer: ❌ Missing: password strength validation (spec says "min 8 chars")

[Implementer fixes]
  Implementer: Added validation, 7/7 tests passing.

[Dispatch spec reviewer again]
  Spec reviewer: ✅ PASS

[Dispatch quality reviewer]
  Quality reviewer: Important: Magic number 8, extract to constant
  Implementer: Extracted MIN_PASSWORD_LENGTH constant
  Quality reviewer: ✅ APPROVED

[Mark Task 2 complete]

... (continue for all tasks)

[After all tasks: dispatch final integration reviewer]
[Run full test suite: all passing]
[Done!]
```

## Remember

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Quality is not an accident. It's the result of systematic process.**

## Further reading (load when relevant)

When the orchestration involves significant context usage, long review loops, or complex validation checkpoints, load these references for the specific discipline:

- **`references/context-budget-discipline.md`** — Four-tier context degradation model (PEAK / GOOD / DEGRADING / POOR), read-depth rules that scale with context window size, and early warning signs of silent degradation. Load when a run will clearly consume significant context (multi-phase plans, many subagents, large artifacts).
- **`references/gates-taxonomy.md`** — The four canonical gate types (Pre-flight, Revision, Escalation, Abort) with behavior, recovery, and examples. Load when designing or reviewing any workflow that has validation checkpoints — use the vocabulary explicitly so each gate has defined entry, failure behavior, and resumption rules.

Both references adapted from gsd-build/get-shit-done (MIT © 2025 Lex Christopherson).

### Codebase Audit Reference

When auditing a codebase for bugs and improvements, load:
- **`references/codebase-audit-pattern.md`** — Audit trigger taxonomy, findings table of real fixes applied to hermes-agent, testing strategy, and known-non-bugs list.

### Pitfall: Check for Existing Ports Before Rewriting from Scratch

Before building a cross-platform rewrite of any significant application, check for existing production-quality ports first. A from-scratch rewrite of a 7,637-line macOS app produced a 3,555-line WPF port with critical gaps — while a pre-existing clicky-win (PySide6, 3,810 lines) was significantly more complete and production-ready.

**The pattern:**
1. User wants "1:1 rewrite of X for platform Y"
2. Agent starts from scratch without checking if a port already exists
3. Result: inferior to existing port in completeness, structure, and polish

**When this applies:** Any time the user says "rewrite for Windows", "port to X", "make work on Y", or asks to replicate another platform's app. The investigation phase must include a brief check for existing ports on the target platform before committing to from-scratch implementation.

**Why this matters:** Existing ports benefit from months of real-user bug reports, production hardening, and iteration. A fresh rewrite starts at zero. For example, a PySide6 clicky-win already had full CompanionManager, proper hotkey detection, streaming transcription, SSE parsing, waveform visualization, fly-to animation, multi-monitor support, and a test suite — none of which were complete in the WPF rewrite after 20 minutes of subagent time.

**The correct sequence:**
1. User says "1:1 rewrite of Clicky for Windows"
2. Spike investigation reads ALL original source files (25 Swift files, 7,637 lines)
3. **Also** check for existing Windows ports — GitHub search + clone any candidate
4. Compare: existing port vs from-scratch rewrite quality/time
5. Choose the better path, document the decision

**Investigate thoroughly first** — Thomas's bar for "done" is exhaustive, not approximate. When he says "don't make shortcuts or summarize, go deep in the investigation", treat it as a standing instruction for any codebase investigation task. This means: read every file, complete coverage is non-negotiable, map every subsystem before declaring complete. The clicky investigation confirmed 25 Swift files (7,637 lines) before writing the SPEC — that level of rigor is the standard.
