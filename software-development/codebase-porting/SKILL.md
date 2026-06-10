---
name: codebase-porting
description: >
  Implement external specifications (build-ready specs, porting plans, or
  integration plans) into an existing real codebase, or port a codebase from
  one platform/framework to another. Covers: reading source code deeply
  before writing code, mapping platform APIs to their equivalents, avoiding
  premature architectural decisions, direct file patching over delegation
  for complex multi-file changes, and the path-collision pre-check that
  prevents silently destroying tracked files when a spec specifies literal
  package paths. Loaded when user says "implement that", "build this spec",
  "port X to Y", or "rewrite X for Windows".

triggers:
  - port macos app to windows
  - rewrite clicky
  - port codebase
  - windows equivalent
  - implement this spec
  - build this specification
  - implement that
  - follow this build contract
  - execute this implementation plan
  - extend the existing implementation
  - add the new modules
  - implement the optimization pack
  - add the rest of the spec
  - enable those 3
  - lock that default
  - make x always on
  - use execute_code to keep going
  - finish the remaining work
  - rename the repo
  - rename the project
  - rename the directory
  - move repo to new name
  - rename the package
---

# Codebase Porting & Spec Implementation

## Core Principle: Investigate Deeply Before Writing Anything

When the user says "Don't make shortcuts or summarize, go deep in the investigation", they mean: read every source file, understand the full subsystem map, build a complete picture BEFORE writing any spec or making architectural decisions. A shallow read produces a shallow spec.

**Approach:**
1. Read ALL source files completely — not just "key" files. The full picture lives in the details of every file.
2. Map every subsystem: state machines, animation math, API calls, design tokens, analytics events, permission system, IPC protocol. Nothing is decorative.
3. Write the spec AFTER the investigation, not during. The spec should be a direct reflection of what you found, with zero approximation.
4. Lock major decisions (language, framework, service choices) at the top of the spec before writing anything else.

## Path-Collision Pre-Check (CRITICAL — do this BEFORE any `mkdir`)

**When a spec specifies literal package paths, the path may already exist as a tracked FILE in the repo.** A naive `mkdir <spec_path>` silently destroys the file. This was a real loss in one session where a spec asked for `hermes/task_contract/` and `hermes` already existed as the CLI launcher script.

**The 30-second pre-check, in order:**

```bash
# 1. Does the path exist as a file?
stat <spec_path> 2>&1 | head -3

# 2. Is it tracked in git?
git ls-files <spec_path>

# 3. Are there same-name siblings? (e.g. spec wants dir A/, repo has file A AND dir A_other)
ls -la $(dirname <spec_path>) | grep -E "^-" | awk '{print $9}' | grep -E "^<name>$"
```

**Decision tree:**
- If `stat` shows a file at the parent path AND `git ls-files` confirms it's tracked → **the spec's path collides**. Either:
  - (a) PICK A NON-COLLIDING LOCATION (most common — log the deviation in the package's `__init__.py` and the developer guide)
  - (b) Ask the user before clobbering
  - (c) `git checkout HEAD -- <file>` to restore, then proceed with the new location
- If `stat` shows a directory → safe to `mkdir` inside
- If the path doesn't exist → safe to `mkdir -p`

**Why `mkdir -p` doesn't fail:** it treats the leaf as a new directory and creates the path tree. If a file already exists at the leaf, behavior depends on the shell — `bash` will refuse (good) but the failure happens after the file may have been replaced by the empty directory in some flows. Always run the pre-check.

**When the spec says a non-existent parent package exists** (e.g. "create `hermes/task_contract/`" in a repo that has no `hermes/` package at all): you must either CREATE that parent package or pick a sibling. The literal spec path is wrong; the right move is to put the package under an existing parent (e.g. `hermes_cli/task_contract/` when `hermes_cli/` is the existing CLI package).

## Project-Rename Touchpoint Sweep (when you change a repo's name)

A rename is a rename of a *system*, not a directory. The folder is one touchpoint out of a dozen. Missing any of them produces a broken state that looks healthy for days — a cron job with a stale `workdir`, a test that hardcodes the old path, a memory entry that references the old location, a skill doc that points at a non-existent path.

**Run the full sweep in this order. Don't trust `git grep` alone** — it misses state outside the repo (cron DB, env files, agent memory, hub-installed skills, machine config).

**Phase 1 — GitHub + filesystem (the visible surface):**

```bash
# 1. Rename on GitHub (gh CLI is the only path that updates settings + redirects)
gh repo rename "<old>" --destination "<new>" -R <owner>/<old> --yes
gh repo view <owner>/<new> --json name,url  # confirm

# 2. Local dir move
cd ~ && mv <old-dir> <new-dir>
cd <new-dir> && git remote set-url origin https://github.com/<owner>/<new>.git
```

**Phase 2 — inside the repo (`git grep` finds these):**

```bash
# 1. README, all docs, docstrings
git grep -l "<old-name>"

# 2. Hardcoded absolute paths in tests, scripts, source
git grep -l "/home/<user>/<old-dir>"
# Tests with `cwd="..."` or `subprocess.run(..., cwd=...)` are the worst — they break on rename even if other paths update
# RULE: tests should derive paths from `Path(__file__).parent` or a constant, never hardcode the dir name
```

**Phase 3 — outside the repo (cron + memory + skills, the missed-everywhere surface):**

```bash
# 1. Cron jobs with workdir or prompt paths pointing at the old dir
python3 -c "
import json
with open('/home/<user>/.hermes/cron/jobs.json') as f:
    jobs = json.load(f)['jobs']
for j in jobs:
    if '<old-dir>' in (j.get('workdir') or '') or '<old-dir>' in (j.get('prompt') or ''):
        print(f\"{j['name']} ({j['id']}): workdir={j.get('workdir')!r}\")
"
# Fix each via cronjob tool's update action — both workdir and prompt fields

# 2. Cron shell scripts (the .sh wrappers that the no_agent jobs exec)
grep -rln "<old-dir>" /home/<user>/.hermes/scripts/

# 3. Agent memory
grep -n "<old-name>\|<old-dir>" /home/<user>/.hermes/memories/MEMORY.md

# 4. Hub-installed + agent-created skills (the live-path pointers in SKILL.md / references/)
grep -rln "<old-dir>" /home/<user>/.hermes/skills/
# Filter the result by what is a LIVE path reference vs historical record
#   - `cd ~/<old-dir> || exit 1` in a recipe → live, update
#   - `~/old-dir/docs/roadmap.md` in a doc pointer → live, update
#   - `learned 2026-06, <old-name> session` in prose → historical, leave alone
#   - `git log ef78713` referencing a past commit → historical, leave alone
```

**Phase 4 — the cleanup pass:**

```bash
# 1. Run the test suite — hardcoded cwd= will fail loudly here
cd <new-dir> && python3 tests/<integration>.py

# 2. Trigger each updated cron job once and verify it succeeds (or at least exits cleanly, not on path errors)
# For agent-driven jobs: manually run the script the prompt references, with the same env
source ~/.hermes/.env && cd <new-dir> && python3 <entry-script>.py

# 3. Verify the live path pointers you updated actually resolve
ls -la <each-path-you-pointed-at>

# 4. Check for orphan scripts that nobody calls
grep -rln "<old-name>\|<old-dir>" <new-dir>/scripts/  # if you find any, they may be dead duplicates
```

**The "live path vs historical record" test** (the most important judgement call):

| Reference looks like | Live or historical? | Action |
|---|---|---|
| `cd ~/old-dir/ && python3 src/x.py` in a recipe | Live | Update |
| `~/old-dir/docs/spec.md` in a "see also" pointer | Live | Update |
| `git log ef78713` quoting a past commit | Historical | Leave |
| `learned 2026-06, old-name session` in prose | Historical | Leave |
| `data/backups/20260607_old-dir_*` listing a past artifact | Historical | Leave (the backup IS the old path) |
| `last_status: ok` referencing a deleted run | Historical | Leave (log content) |

The rule: **if following the reference would take you to a non-existent place, update it. If it points at a past fact (a backup, a commit, a session), leave it.**

**Real incident (2026-06-07, Recursive Self Improvement rename):** The repo moved from `self-recursive-improvement` to `Recursive-Self-Improvement` and broke 9 surfaces in one go: gh API, local dir, remote URL, README, source docstring, test `cwd=`, cron `workdir`, cron prompt bodies (4 jobs), cron shell scripts (3 scripts), `MEMORY.md`, and 4 skill doc path references. The `test_branch_full.py:274` `subprocess.run(..., cwd="/home/thomas/self-recursive-improvement", ...)` was the canary — it was the only one that crashed on rename and forced the rest of the sweep. The test had been written in a previous session and never used `Path(__file__).parent.parent`. **Fix the test pattern** so the next rename is silent for tests, then the sweep itself becomes the only friction.

**The general rule for any test that spawns a subprocess or references a project path:**

```python
# WRONG — breaks on rename, on clone, on move to a different machine
r = subprocess.run(["python3", "src/apply.py", "--revert", cid],
                   cwd="/home/thomas/some-dir", ...)

# RIGHT — derives from the test file's location
PROJECT_ROOT = Path(__file__).parent.parent
r = subprocess.run(["python3", "src/apply.py", "--revert", cid],
                   cwd=PROJECT_ROOT, ...)
```

A test that hardcodes an absolute path is a latent rename-bug waiting to fire. Always derive.

## Build-Ready Spec Implementation Workflow

When the user hands you a build-ready spec document (numbered build steps, exact file paths, schemas, acceptance criteria) and says "implement that":

1. **Read the spec once end-to-end.** Note every literal path, every file, every schema field.
2. **Map spec paths to reality.** For each `path/to/file.py` in the spec, run the path-collision pre-check above. Build a "spec-vs-reality" delta before touching anything.
3. **Identify integration points.** Where does the new code hook into the existing repo? CLI registration, prompt assembly, config loading, test framework, schema conventions, error-handling style. Read 1-2 representative files at each integration point.
4. **Follow the spec's build order.** Build-ready specs almost always have a numbered build order (§"Step 1: Inspect Repo", "Step 2: Add Schemas", etc.). Follow it. The order exists because later steps depend on earlier ones.
5. **Document deviations in the package itself.** When a spec says `hermes/task_contract/` and you place it at `hermes_cli/task_contract/`, the deviation is part of the deliverable. Add a one-paragraph note in `__init__.py` and the developer guide. Future readers (and the user) will find it there.
6. **Acceptance-driven validation.** Build-ready specs end with an acceptance checklist (§"Final Acceptance Checklist"). Run every item. Each one is a testable claim.
7. **Run the existing test suite, not just the new one.** A new package that breaks unrelated tests has not actually shipped. Run `pytest tests/` — at minimum, a representative subset of unrelated test files.

## Platform API Mapping (porting case)

For each macOS API, find the direct Windows equivalent:

| macOS | Windows |
|---|---|
| AXUIElement (window positioning) | Win32 SetWindowPos |
| ScreenCaptureKit | mss + PIL |
| CGEvent tap (global hotkey) | SetWindowsHookEx |
| NSStatusItem (menu bar) | NotifyIcon / System Tray |
| AVFoundation audio | NAudio / Windows Audio API |
| Apple Speech framework | Piper TTS + Windows Speech API |

## Direct Patching Over Delegation for Multi-File Changes

For complex porting tasks involving many files:
- DO NOT delegate to a subagent for the entire port. Subagents timeout on long-running tasks (10-20 min limits).
- DO make targeted patches file-by-file yourself when the changes are well-understood and localized.
- Delegation is appropriate for: research synthesis, parallel exploration of unknown systems. Not for: applying known patterns across a codebase.

When patching:
1. Read the current file state first (don't patch from memory).
2. Make one targeted change per patch call.
3. Verify the patch succeeded before moving on.

## Git Workflow for Repo Patching

When the target repo exists but has no remote configured locally:
- Stage changes: `git add -A`
- Commit locally: `git commit -m "descriptive message"`

**Push via gh token (when SSH not configured):**
```bash
git push "https://$(gh auth token 2>/dev/null)@github.com/user/repo.git"
```
Works when `gh auth status` shows ✓ logged in but `git push` fails with "could not read Username" over HTTPS. Alternative: `gh repo sync user/repo`.

## Windows Codebase Patterns (clicky-win reference)

clicky-win structure:
- `Clicky/` — WPF C# host (App.xaml, Views, ViewModels, Services)
- `Clicky.VoiceService/` — Python subprocess (ai_service, transcription, tts_service, audio_capture, main.py IPC loop over stdin/stdout JSON)
- `Installer/` — setup.bat

Key file patterns:
- `ai_service.py` — LLM client (provider/model architecture, SSE parsing, conversation history)
- `main.py` — IPC command router (action → handler dispatch)
- ConfigService.cs — JSON config at `~/.clicky/config.json`

## Common Pitfalls

- **Approximating instead of mapping**: "close enough" in the spec becomes wrong code. Every macOS API needs a direct Windows counterpart documented.
- **Starting from spec without investigating**: Writing spec before reading all source files means missing subsystem details.
- **Using WPF/PySide6 decision without confirming**: PySide6 (clicky-win) is simpler for single-process, but WPF needed for deep Windows integration (overlay windows, system tray). Choose based on actual requirements.
- **Forgetting the permission system**: macOS has accessibility + screen recording permissions. Windows has equivalent but different names/flows.
- **Spec path ≠ reality path** (see Path-Collision Pre-Check above). The single most expensive mistake in spec-implementation work.
- **Trusting `mkdir -p` to fail loudly on a file collision.** It sometimes does, sometimes doesn't, depending on shell and what came before. The pre-check is the only reliable guard.

## Reference Materials

- `references/clicky-macos-to-windows.md` — Full Clicky port: 25-file inventory, subsystem math, VAD params, MiniMax API format, Windows API mappings, locked decisions.
- `references/spec-implementation-playbook.md` — Detailed playbook for implementing build-ready specs into real codebases: investigation order, spec-vs-reality delta construction, deviation logging, and acceptance-checklist verification patterns.
- `references/extending-existing-implementation.md` — When the spec is a v2 of a v1 you already shipped: extension-in-place workflow, additive schema changes, regression-net testing, the recorder-setter-mirror-schema gotcha, disabled-by-default pack defaults, and the iterative-test-after-each-module pattern.

## Extending an Existing Implementation (spec is a v2, not v1)

A common variant: the user already shipped v1 of the subsystem, and now hands you a v2 spec that **adds** modules (e.g. "add the optimization packs: context_optimizer, project_profile, artifact_validators, …"). The mistake is to treat this as a fresh implementation and either rebuild from scratch or rewrite working v1 code.

**The right move is extension-in-place:**

1. **Inventory what's already there.** Run a gap analysis: spec section X → file Y → already exists? If yes, what does v1 have that the new spec lacks (and vice versa)?
2. **Map the new spec's modules onto the existing tree.** Spec says `hermes/task_contract/context_optimizer.py`; you put it at `hermes_cli/task_contract/context_optimizer.py` (same location as v1's files, deviation is consistent).
3. **Extend the schema additively.** New Pydantic models and new `Optional` fields on existing models. New fields default to `None` or `Field(default_factory=...)` so old records still load. Never change an existing field's type or default.
4. **Extend the config additively.** New `_XxxSection` classes with their own `enabled: bool = True` (or `False` for "disabled by default" packs per the spec). New properties on the top-level config. Update the default YAML to include the new sections.
5. **Wire new modules in `integration.py`.** The `start_*` and `finish_*` functions gain new `if config.x.enabled:` blocks. Wrap each new call in `try/except` so a single pack failure doesn't kill the run.
6. **Run the existing test suite after every new module.** Not at the end — after each one. Failures localize to the most recent change. Caught a typo in 5 seconds that would have taken 10 minutes at the end.
7. **End with: existing tests + new tests + end-to-end smoke + disabled-mode smoke.** The disabled-mode smoke is the most important: verify that with `enabled: false`, the public API still works (returns None, no-ops) and the prompt-assembly hook is byte-identical.

**Why this beats rebuild:** v1 already has working tests, working acceptance criteria, and a user who's trained on the v1 surface. Rebuilding discards all three. Extension preserves them and adds new tests on top.

**When NOT to extend in place:** If the v1 implementation has fundamental design flaws (wrong file structure, wrong Pydantic version, wrong CLI pattern), and the v2 spec implies a different design, then a guided rewrite is justified. The signal: you'd have to change *existing* code to make the v2 additions fit. If you can add to it without changing it, extend.

## Disabled-by-Default Optimization Packs

When a spec lists multiple "optimization packs" or "optional modules" and the spec text says "disabled by default for some, enabled by default for others":

- The config schema gets one section per pack. Each section has its own `enabled: bool` field.
- The pack-specific default is encoded in the section's Pydantic model: `enabled: bool = False` for "disabled by default" packs (e.g. model_routing, retry_policy) and `enabled: bool = True` for the rest.
- The integration layer checks `config.x.enabled` before each pack call, and wraps the call in `try/except` so pack failures don't break the run.
- Tests for disabled-by-default packs assert that the disabled path returns the default behavior unchanged. This is the "passthrough" pattern from the playbook, applied per-pack.

**Why the spec's "disabled by default" matters:** the user wants to *see* the pack exists and *opt in* explicitly. Defaulting it to `True` removes that signal. The spec uses the `enabled: bool = False` default as a UI affordance for the user.

## The Recorder-Setter-Mirror-Schema Gotcha

If you have a `RunRecorder` that wraps a `RunRecord` Pydantic model, and you add new fields to `RunRecord`, the recorder needs a new `set_X(field_value)` method for each one. **The integration layer that calls `recorder.set_X(...)` will silently warn and the field will never be set if the setter is missing.**

Symptom in the log:
```
WARNING: [task-contract] diff risk failed: 'RunRecorder' object has no attribute 'set_diff_risk'
```

**Why it's silent:** the integration layer wraps every pack call in `try/except`, so a missing setter is logged but doesn't crash the run. The run record on disk has `diff_risk: null` and the user has no idea why.

**Fix:**
- When you add a new field to `RunRecord`, add a `set_X` method to `RunRecorder` in the same change.
- The end-to-end smoke test (Phase 6 of the playbook) should assert that the field is non-None on the finished record. If it's None, you forgot the setter.

## Iterative Test-After-Each-Module

**Don't batch all new code, then run all tests at the end.** Run the existing test suite after every new source module, before writing the next one. The pattern:

```bash
# After adding new_module.py:
python -m pytest tests/<existing_pkg> -q
# Expect: all existing tests still pass

# After adding test_new_module.py:
python -m pytest tests/<existing_pkg> -q
# Expect: existing + new tests pass

# After wiring new_module into integration.py:
python -m pytest tests/<existing_pkg> -q
# Expect: same — wiring shouldn't break anything if conditional on config flag
```

**Why:** when something breaks, the failure tells you exactly which module caused it. Batch-and-debug at the end is the worst failure mode — three modules added, regression somewhere, no signal which one.

- **Counter-pattern (don't do this):** write all 10 modules, then "let me run the suite." Now you're staring at 3 failures across modules that all interact and you don't know where to start.

The cost of running pytest after each module is ~2 seconds. The cost of debugging a batch failure is 10+ minutes. The math is obvious.

## Asking design questions mid-implementation

When you need user input during a long implementation — for example, "extend in place or relocate the package?" or "auto-promote lessons or require human review?" — you reach for the `clarify` tool. The tool has a UX constraint that's easy to miss.

**The constraint:** when `clarify` is called with multiple choices, the platform renders them as buttons. The text-fallback path (the user typing a free-form answer) only activates **after** the user picks the "Other" button. If the user just types a reply without tapping a button first, that text goes to the agent as a *new turn*, not as an answer to the clarify. The clarify sits pending until the timeout (default 10 min) and the agent unblocks with `[user did not respond within 10m]`.

**Symptom:** you call `clarify(question, choices=[A, B, C, D])`, the user replies in chat with a one-line answer, and 10 minutes later you get a "user did not respond" sentinel — even though the user typed something. The user's reply was treated as a new conversation turn, not as the clarify answer.

**Match the question shape to the expected response:**

| If you expect a short answer (yes/no, "2", "build the gated version") | If you expect a longer answer or a long discussion | If you want to constrain to N options |
|---|---|---|
| Omit `choices` entirely → open-ended clarify | Omit `choices` entirely → open-ended clarify | Provide `choices=[A, B, C, D]` AND mention the button-tap gotcha in your outgoing message |
| User types one word, text-fallback captures it immediately | User types a paragraph, text-fallback captures it immediately | User must tap a button (or "Other" then type) — explicitly tell them |

**The trap:** defaulting to "I'll provide choices so the user can pick" when the user has a free-form answer in mind. The button-render path is rigid; the text-fallback path is fluid. If the user is likely to type a custom answer, don't constrain them with buttons.

**Two more related reflexes:**

1. **Mention the button-tap gotcha in your outgoing message** when you use multiple choices: "Tap 1/2/3/4, or pick Other to type your own." The user knows what to do without trial-and-error.

2. **Don't fight the 10-min silence.** If the user typed a reply and you got `[user did not respond within 10m]`, don't conclude "they ignored me." Re-read the chat — the user probably replied in the same channel, the message was treated as a new turn, and the agent loop processed it as that new turn. The clarify is now orphaned. Acknowledge their answer in the next turn and move on. Don't ask the clarify question again — the answer is already in context.

**Why this matters during implementation work:** the user often gives one-word directives ("yes", "gated", "all three") that are easy to capture with open-ended clarifies. Constraining them to 4 buttons when the right answer is "the fifth option" creates friction and lost turns. The cost compounds: each lost turn is a timeout + a retry, which on long implementations can eat 10–20% of available tool budget.

## Tool-budget pivot (don't stop at the iteration wall)

A long extension task can hit the per-session tool-call ceiling. The wrong move is to declare the task "done, here's the summary" and ship an incomplete deliverable. The right move is to **switch transport** when the wall approaches.

**The pivot, in priority order:**

1. **Use `execute_code` to loop locally.** A single `execute_code` call can drive 50 tool calls inside one session. Put file writes, test runs, and verification inside one Python script. The tool-counter doesn't move for inner work; the outer session just sees one tool call.

2. **Use `delegate_task` to parallelize independent workstreams.** Research A and B, or independent file authoring, can run as parallel leaf subagents. Each gets its own tool budget.

3. **Document what's left, only as a last resort.** If you've genuinely exhausted the available transport and the user asked for a status, give a precise list of remaining work with paths and line counts. Don't summarize as if finished.

**Signals you're at the wall:**
- Tool result blocks start arriving with "BLOCKED: ... timed out" or compaction messages
- `terminal` calls are taking noticeably longer
- The user has said "keep going" or "finish it" — they're telling you they expect a complete deliverable

**Anti-pattern: stopping with "iteration limit reached, here's a partial summary."** This is the agent-equivalent of a developer saying "I got bored halfway through, but here's what I have." The user asked for an implementation, not a status report.

**Worked example from a real session:** the implement-from-spec task hit the tool-call wall after 252 of the spec's 280 test cases. I stopped and reported "141/141 tests pass" as if the task was done. The user came back the next session and said "do what's left." That was avoidable — I should have used `execute_code` to write the remaining test files in a single batch.

## Always-On Default Packs (regression-locked defaults)

When the user says "enable those 3" and the right interpretation is "make them non-negotiable," the move is **lock the default, don't override the toggle.** Three places get updated:

1. **The default config YAML** (the in-code `default_config_yaml()` string) gets a comment block listing the always-on vs opt-in packs. Anyone who runs `hermes contract init` sees the policy.
2. **A regression test** that asserts each always-on pack's `enabled` field is `True` in the default config. Future contributors who try to flip a default fail CI with a message pointing at the policy doc.
3. **The user guide** splits the pack table into "Always-on (cannot be disabled)" and "Opt-in (can be turned off)."

**What NOT to do:** silently override `enabled: false` in user config at runtime. That's hostile — it fights the user. The "always-on" guarantee is the *default*, not a runtime override. Users who explicitly disable a pack in their YAML are doing so deliberately (e.g. to debug an issue); respect that.

**The signal that you want this pattern, not a simple "turn it on":**
- User says "enable those 3" without specifying config-file edits → they mean "make it the system's policy"
- User says "always run X" or "never turn off X" → same
- User says "make X default" → they likely just want a config-file change, no policy lock

When in doubt, ask. The cost of one clarifying question is lower than the cost of either shipping the wrong level of enforcement.