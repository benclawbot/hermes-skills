---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 7: Save the Plan

The save location is **workspace-dependent**. Don't assume — verify.

- **Default repo convention** (most projects): `plans/feature-name.md` at project root.
- **hermes-agent (`~/.hermes/hermes-agent/`)**: `.plans/` at project root — note the leading dot. Existing examples: `.plans/openai-api-server.md`, `.plans/streaming-support.md`, `.plans/gemini-oauth-provider.md`. Filename convention: `.plans/YYYY-MM-DD_HHMMSS-<slug>.md`. The in-repo `plan` skill (under `skills/software-development/plan/SKILL.md`) says `.hermes/plans/` — that path is wrong for hermes-agent, ignore it.
- **Per-session / per-workspace** (Docker / SSH / Modal backends): `.hermes/plans/` relative to the active workspace, written by the in-repo `plan` skill. Different convention, different directory.
- **User override**: if the user names a path, use exactly that path.

Quick verification before writing:

```bash
ls -d .plans plans docs/plans .hermes/plans 2>/dev/null
git log --oneline --all -- 'plans/*.md' '.plans/*.md' 2>/dev/null | head -5
```

Pick the directory that already has prior plans, or ask.

```bash
# hermes-agent example (most common for this user):
mkdir -p .plans
git add .plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

### Assuming the Wrong Plans Directory

**Bad:** Writing `plans/feature.md` when the repo uses `.plans/` (or vice versa). Each project has its own convention; the in-repo `plan` skill and the standalone `writing-plans` skill disagree — always `ls` for prior plans first.

**Good:** Run `ls -d .plans plans docs/plans .hermes/plans 2>/dev/null` and `git log --oneline --all -- 'plans/*.md' '.plans/*.md'` before writing. For hermes-agent, default to `.plans/YYYY-MM-DD_HHMMSS-<slug>.md`.

### Confusing the Two Planning Skills

There are two skills with overlapping names:

- `plan` (in-repo: `~/.hermes/hermes-agent/skills/software-development/plan/SKILL.md`) — generic, lightweight. Says "save to `.hermes/plans/`", "include Goal / Current context / Proposed approach / Step-by-step plan / Files likely to change / Tests / validation / Risks, tradeoffs, and open questions." No TDD-per-task shape, no exact file paths required, no code blocks. Good for quick high-level plans, bad for subagent-driven execution.
- `writing-plans` (this skill) — class-level, TDD-per-task, exact paths, copy-pasteable code, expected output per step, commit-per-task. Required input for `subagent-driven-development`.

**Use this skill (`writing-plans`) whenever the plan will be executed via `subagent-driven-development` or handed to a fresh subagent.** Use the in-repo `plan` skill only when the user explicitly says "high-level plan" or "just the shape, no code." When in doubt, ask: "Should I include copy-pasteable code blocks for each task, or a higher-level outline?" — defaults vary by user.

### Naming a Skill / Pattern by Its First Use Case Instead of Its Substrate

When a brainstorm surfaces a substrate-level pattern (something that could apply to cron, `delegate_task`, in-session flows, and so on), naming it after the *first* use case you thought of bakes in a false constraint. Observed 2026-06-26: sketched a "swarm" pattern, named it `cron-swarm` because cron was the example I led with, then realized it works just as well for `delegate_task` sweeps and in-session multi-skill runs. The user pushed back: "why is this for cron only?"

**The rule:** when naming a new skill or primitive, ask "what is this PATTERN, independent of where it runs?" Lead the brainstorm and the name with the broadest framing. Cron is a deployment mode; the pattern is multi-agent coordination without a central orchestrator.

**Self-check before naming:**
- Can I describe this pattern without naming any specific execution context (cron, subagent, batch)?
- If I strip the execution context from the name, does it still make sense?
- Would a user searching for the pattern find it under this name if they only thought of a different use case?

If any answer is no, the name is too narrow. Rename before shipping the spec, not after the user catches it.

### `patch` Tool Indentation Mismatch

The `patch` tool does fuzzy matching, but it does NOT preserve the indentation of `old_string` separately from the surrounding context. If the block you want to replace has a different indent level than the surrounding lines (e.g. a function body inside a markdown code block, where every line has 4 leading spaces but the context lines do not), and your `old_string` includes surrounding context lines for uniqueness, those context lines get inserted at the wrong indent level and your replacement block lands malformed.

**Observed 2026-06-26:** replaced a Python test function inside a markdown code block. The `old_string` included a few surrounding markdown-context lines (no indent) for uniqueness, and the test function (4-space indent). The replacement landed with the surrounding context indented at 4 spaces and the function body de-indented to the markdown context level — totally broken Python.

**The rule:** when patching inside a markdown code block, copy the ENTIRE indented block as `old_string` (no surrounding un-indented context for uniqueness) and use enough internal uniqueness (function name, signature) to make it unique within the file. Don't rely on surrounding non-indented context lines to disambiguate.

**Or:** use `write_file` for blocks inside markdown code fences when the patch gets complex. The `write_file` tool re-reads the full file first (per the cross-profile warning), which catches indentation drift.

**Recovery:** if a `patch` lands malformed, immediately read the affected range with `read_file` to see the actual state, then either (a) re-patch with a corrected `old_string` that includes the malformed lines exactly as they now appear, or (b) `write_file` the file from a known-good source if you have it.

### Spec Handoff: Open Questions Are a Discovery Flow, Not a Footnote

After saving a spec that ends with an "Open Questions" section, do NOT treat the spec as self-delivering. The user reading the plan file is not the same as the user deciding each open question. Bundle all 5 questions into a single reply that ends with "what do you think?" and the user has to read the whole plan, remember the 5 questions, and reply once. That's the discovery-flow violation `one-question-at-a-time` already covers.

**The handoff pattern** (see `one-question-at-a-time` → "Spec handoff protocol"):
1. Save the plan.
2. Reply: "Plan saved at `<path>`. 5 open questions — I'll ask one at a time."
3. Call `clarify(question="...", choices=[...])` for question 1 only.
4. After each answer, capture the decision, then `clarify()` for the next one.
5. After the last answer, update the spec file with the locked-in decisions.
6. Offer execution handoff.

Default values may be stated up front so the user can say "defaults" once, but the questions still go one at a time via `clarify()` so the user can override any single one.

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**

## Reference Examples

- `references/hermes-agent-spec-example.md` — concrete example of a 6-task
  hermes-agent spec using this skill's shape (frontmatter scope, fitness
  tracker, skill slimming, cron swarm, memory TTL, subagent budgets). Use as
  a template when writing your own spec for the hermes-agent repo.
