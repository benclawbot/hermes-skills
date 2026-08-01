---
name: plan-and-execute-workflow
description: "Plan-then-execute workflow for multi-step implementation work — write a TDD-per-task, exact-path, copy-pasteable-code plan (writing-plans), then execute it via fresh-context subagents with two-stage review (subagent-driven-development). Use when the user has a multi-step feature/fix that needs a plan and a controlled execution loop with quality gates. Covers task granularity (2-5 min each), TDD-per-task, exact file paths and commands with expected output, two-stage review (spec compliance THEN code quality), fresh subagent per task, the gate taxonomy (pre-flight / revision / escalation / abort), context-budget discipline, long-running-task recovery, and codebase audit. Replaces two formerly separate skills (writing-plans + subagent-driven-development) — they were two halves of the same workflow and the cross-references made the pair discoverability-costly."
version: 1.0.0
author: Hermes Agent (consolidated from obra/superpowers + gsd-build + Thomas)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, delegation, subagent, parallel, tdd, review]
    related_skills: [build-spec-workflow, self-improvement-loop, systematic-debugging]
---

# Plan-and-Execute Workflow

The full loop for taking a multi-step implementation request and shipping it
with controlled quality. **Two halves**: (1) write the plan, (2) execute it
via fresh subagents with two-stage review. The plan is the contract; the
execution loop enforces it.

```
plan (writing-plans)
   │
   │  plan file: bite-sized tasks, exact paths, copy-pasteable code,
   │  TDD per task, expected output per command
   │
   ▼
execute (subagent-driven-development)
   │
   │  for each task:
   │    implementer subagent → spec-compliance review → code-quality review
   │    (each review is itself a fresh subagent; loop until both pass)
   │
   ▼
final integration review + full test suite + commit
```

When to use the full workflow:
- Multi-step feature or refactor (3+ tasks)
- The user expects code-quality gates (TDD, two-stage review)
- The plan will be executed by subagents (or a fresh human implementer)
- The work touches multiple files / subsystems

When NOT to use:
- Single-file quick fix → just do it
- Pure research / spec generation → `build-spec-workflow`
- Reading an existing codebase for patterns → `oss-pattern-mining`
- Ad-hoc delegation to one subagent → `delegate_task` directly

---

## Subsection: writing-plans (formerly standalone)

> Write implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

### When to use
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

### Bite-Sized Task Granularity
**Each task = 2-5 minutes of focused work.**

### Plan Document Structure
Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]

---

### Task N: [Descriptive Name]
**Objective:** [one sentence]

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing_file.py:45-67`
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**
[code block]

**Step 2: Run test to verify failure**
Run: `pytest tests/path/test.py::test_X -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**
[code block]

**Step 4: Run test to verify pass**
Expected: PASS

**Step 5: Commit**
```bash
git add tests/ src/ && git commit -m "feat: ..."
```
```

### Principles

**DRY:** Extract validation/utility logic; never copy-paste across files.
**YAGNI:** Implement only what's needed NOW; no "future flexibility" slots.
**TDD:** Every code task = write failing test → run to verify → implement → run to verify → commit.
**Frequent commits:** One commit per task minimum.

### Save location
**Workspace-dependent.** Verify before writing.

```bash
ls -d .plans plans docs/plans .hermes/plans 2>/dev/null
git log --oneline --all -- 'plans/*.md' '.plans/*.md' 2>/dev/null | head -5
```

- **hermes-agent repo** (`~/.hermes/hermes-agent/`): `.plans/YYYY-MM-DD_HHMMSS-<slug>.md`
- **Most other repos**: `plans/feature-name.md`
- **Per-session workspaces**: `.hermes/plans/`

If unsure, ask.

### Pitfalls

- **Vague tasks** — "Add authentication" is too big; split into model, hashing util, login endpoint, JWT, register endpoint.
- **Incomplete code** — paste the actual code, not "add validation."
- **Missing verification** — every command must include expected output.
- **Missing file paths** — use exact paths, not "the config file."
- **Wrong plans directory** — each project has its own convention; `ls` for prior plans first.
- **The two planning skills confusion** — `plan` (in-repo, lightweight) vs `writing-plans` (this skill, TDD-per-task). Use `writing-plans` whenever the plan will be executed via `subagent-driven-development`. Use `plan` only when the user explicitly says "high-level plan" or "just the shape, no code."

### Spec handoff: open questions are a discovery flow
After saving a plan that ends with "Open Questions," do NOT treat the spec as self-delivering. Use `one-question-at-a-time`:

1. Save the plan.
2. Reply: "Plan saved at `<path>`. N open questions — I'll ask one at a time."
3. `clarify(question=..., choices=[...])` for question 1 ONLY.
4. After each answer, capture the decision, then `clarify()` for the next.
5. After the last answer, update the spec file with the locked-in decisions.
6. Offer execution handoff.

Defaults are fine to state up front, but questions still go one at a time.

### Naming a Skill / Pattern by Its First Use Case Instead of Its Substrate

When brainstorming a substrate-level pattern (could apply to cron, `delegate_task`, in-session flows, etc.), naming it after the *first* use case bakes in a false constraint. Example: sketched a "swarm" pattern, named it `cron-swarm` because cron was the example, then realized it works for `delegate_task` sweeps too. User pushed back: "why is this for cron only?"

**Rule:** before naming, ask "what is this PATTERN, independent of where it runs?" Cron is a deployment mode; the pattern is multi-agent coordination without a central orchestrator.

### `patch` Tool Indentation Mismatch (in markdown code blocks)
The `patch` tool does fuzzy matching but does NOT preserve indentation of `old_string` separately from the surrounding context. When patching inside a markdown code block, copy the ENTIRE indented block as `old_string` and use enough internal uniqueness (function name, signature) to make it unique within the file. Don't rely on surrounding non-indented context lines to disambiguate.

Recovery: if a `patch` lands malformed, immediately `read_file` the affected range, then either re-patch with corrected `old_string` or `write_file` from a known-good source.

---

## Subsection: subagent-driven-development (formerly standalone)

> Execute plans via fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

### When to use
- You have an implementation plan (from `writing-plans` or user requirements)
- Tasks are mostly independent
- Quality and spec compliance matter
- You want automated review between tasks

### Per-Task Workflow

For EACH task in the plan:

**Step 1: Dispatch Implementer Subagent** with complete context (full task text, project context, TDD instructions). Implementer does TDD: write failing test → run to verify failure → implement → run to verify pass → full-suite regression → commit.

**Step 2: Dispatch Spec Compliance Reviewer.** Pass the original task spec. Output: PASS or list of specific spec gaps. Fix gaps → re-review → continue only when spec-compliant.

**Step 3: Dispatch Code Quality Reviewer.** Pass file paths. Check: project conventions, error handling, naming, test coverage, no obvious bugs, no security issues. Verdict: APPROVED or REQUEST_CHANGES. Fix → re-review → continue only when approved.

**Step 4: Mark Complete.** `todo([{"id": task-N, "status": "completed"}], merge=True)`.

### Final Review

After all tasks: dispatch a final integration reviewer covering cross-component consistency, integration issues, all tests passing, ready-to-merge.

### Verification and Commit

```bash
pytest tests/ -q           # full test suite
git diff --stat            # review all changes
git add -A && git commit -m "feat: complete [feature name]"  # final commit if needed
```

### Task Granularity
**Each task = 2-5 minutes of focused work.**

### Red Flags — Never Do These
- Start implementation without a plan
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Skip scene-setting context (subagent needs to understand where the task fits)
- Ignore subagent questions
- Accept "close enough" on spec compliance
- Skip review loops
- Let implementer self-review replace actual review
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues

### Handling Issues

**If subagent asks questions** — answer clearly and completely.

**If subagent hits iteration cap mid-task** (typically ~50 iterations). Files usually on disk and tests may already pass. Always do this recovery in the parent BEFORE dispatching a fresh subagent:

```bash
git status --porcelain     # untracked + modified
git diff --stat            # modifications
pytest <new_test_file> -v  # confirm tests pass
```

Three outcomes:
1. **All committed, tests pass** → mark complete, move on
2. **Files exist, untracked/modified, tests pass, no commit yet** → run `git add` + `git commit` yourself (most common: subagent writes files + tests pass but runs out before the commit step)
3. **Files exist but tests fail or incomplete** → dispatch a fresh fix subagent with explicit resume context

Don't waste a fresh subagent dispatch redoing work that's already on disk and passing.

**If reviewer finds issues** — dispatch a fresh fix subagent (don't re-invoke the original implementer — may also be near cap). Pass: the specific issues, exact file paths/line refs, required test additions, the commit message. Reviewer reviews again. Repeat until approved.

**If subagent fails a task** — dispatch a new fix subagent with specific instructions. Don't try to fix manually in the controller session.

### Parallel Multi-Audit Delegation
For large codebases with distinct areas, dispatch auditor subagents in parallel rather than sequentially. Each subagent focuses on one area with its own scope and trigger list.

**Key lesson:** If the plan file is in a different directory than your primary codebase, verify which project is the intended target before dispatching. A subagent dispatched with the wrong workspace context wastes time inspecting the wrong codebase.

### Long-Running Subagent Strategy

**The 1200s timeout is a hard ceiling (20 min).** For tasks expected to exceed this:
- Write GOAL.md + USER_STORIES.md first (stories = done-ness definition)
- Set up a watchdog cron every 1h (`no_agent=true`, silent on no-change, delivers to Telegram)
- Dispatch with complete current state so the subagent can resume from checkpoint
- After timeout: code is on disk, watchdog fires within 60min, human relaunches with resume context

**Timeout configuration:** Default per-subagent timeout is **600 seconds (10 min)** — too short for non-trivial implementation. Extend to 1200s in `~/.hermes/config.yaml` under `delegation.child_timeout_seconds`, then restart gateway.

**Status cron pattern (used for multi-hour builds):**
- Create recurring cron at "every 1h" with `no_agent=true` script checking file timestamps
- Script runs in seconds, reports what changed since last run
- Deliver to Telegram so user gets hourly progress without parent session involvement

### Pitfall: Subagents inherit parent's tools — they can't hallucinate tools the model doesn't expose
Subagents get the parent's toolset. If the active model provider doesn't expose `web_search` (e.g. MiniMax M2/M3), the parent can still run `curl` + `terminal` + `execute_code` to do web research manually — but a delegated subagent given a research task may fabricate `web_search` invocations because the prompt framed them as having it.

**Detection rule:** if a subagent returns a "starting research / planning to do X" summary longer than ~200 chars without any file write, terminal command, or verifiable handle, it's a hallucination. Kill the dispatch and pivot.

**Correct delegation contract for research tasks when the model lacks web tools:**
- Don't ask subagents to "research the web". Tell them the parent's working directory, the list of URLs/files to pull, and the exact `curl` pattern to use.
- OR: do the research in the parent session yourself with `curl` + `execute_code` for HTML extraction.
- OR: load a skill like `notebooklm-research` that has its own CLI for source gathering.

**Rule of thumb:** if you have to research X to even know what subtask to delegate, do the research in the parent session first.

### Pitfall: Atomic-Write Files Need Both flock AND threading.Lock

Linux `flock(2)` locks the **open file description** (a per-process kernel data structure), not the inode. Two `open()` calls in the *same process* get distinct open file descriptions, so `flock(fd1)` and `flock(fd2)` on the same file do NOT serialize each other. Use both:

```python
import fcntl, threading

_path_locks: dict[str, threading.Lock] = {}
_path_locks_guard = threading.Lock()

def _get_path_lock(path: str) -> threading.Lock:
    with _path_locks_guard:
        lock = _path_locks.get(path)
        if lock is None:
            lock = threading.Lock()
            _path_locks[path] = lock
        return lock

def atomic_json_write(path: str, data: dict) -> None:
    lock = _get_path_lock(path)
    with lock:  # intra-process serialization
        with open(path, "r+") as fp:
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX)  # cross-process
            try:
                ...  # read-modify-write
            finally:
                fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
```

**How to catch:** if the helper is called concurrently from multiple threads, check whether `flock` alone preserves all writes. A test that spawns N threads each writing to a distinct key, then reads back N entries, is the cleanest detector.

### Pitfall: Check for Existing Ports Before Rewriting from Scratch

Before building a cross-platform rewrite of any significant application, check for existing production-quality ports first. A from-scratch rewrite of a 7,637-line macOS app produced a 3,555-line WPF port with critical gaps — while a pre-existing clicky-win (PySide6, 3,810 lines) was significantly more complete and production-ready.

**The correct sequence:**
1. User says "1:1 rewrite of Clicky for Windows"
2. Spike investigation reads ALL original source files
3. **Also** check for existing Windows ports — GitHub search + clone any candidate
4. Compare: existing port vs from-scratch rewrite quality/time
5. Choose the better path, document the decision

Thomas's bar for "done" is exhaustive, not approximate. When he says "don't make shortcuts or summarize, go deep in the investigation," treat it as a standing instruction for any codebase investigation task.

### Handling Repository Inaccessibility

**When browser_navigate to a GitHub repo times out:**
1. Check memory for prior context about the repo (session_search or memory read)
2. If the repo was already cloned or analyzed, use that context directly
3. If new, retry once — transient timeouts are common
4. If retry fails, note inaccessibility and work from what can be determined externally

**Never spend a tool call retrying browser_navigate to a GitHub repo that timed out once** — use `gh clone` or `wget` instead.

### Examples

**Reduces to writing-plans** when:
- Plan file is the deliverable
- Human implementer will execute
- No subagent dispatch planned

**Reduces to subagent-driven-development** when:
- Plan already exists (e.g. from `build-spec-workflow`)
- Tasks are well-scoped and independent
- Two-stage review adds value

**Use the full umbrella** when:
- Plan needs to be generated AND executed with quality gates
- Multi-step feature touching multiple files
- User expects controlled execution with checkpoints

### Verification

After any plan-execute cycle:
- `git log --oneline` shows per-task commits
- `pytest tests/ -q` passes (full suite, not just new tests)
- Spec-compliance reviewer returned PASS for every task
- Code-quality reviewer returned APPROVED for every task
- Final integration reviewer approved

---

## Companion references (in `references/`)

- `writing-plans--hermes-agent-spec-example.md` — concrete 6-task hermes-agent spec using writing-plans shape
- `subagent-driven-development--codebase-audit-pattern.md` — audit trigger taxonomy, real-findings table, known-non-bugs
- `subagent-driven-development--context-budget-discipline.md` — 4-tier context degradation model (PEAK/GOOD/DEGRADING/POOR)
- `subagent-driven-development--gates-taxonomy.md` — Pre-flight / Revision / Escalation / Abort gate types
- `subagent-driven-development--long-running-autonomous-tasks.md` — 3-session timeout recovery pattern + GOAL.md template

## Related skills

- `build-spec-workflow` — produces the spec/plan that this workflow consumes
- `self-improvement-loop` — closed-loop evaluation of changes made via this workflow
- `systematic-debugging` — when a subagent encounters bugs mid-implementation