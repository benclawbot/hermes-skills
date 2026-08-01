---
name: codebase-porting
description: >
  Implement external specifications (build-ready specs, porting plans, or
  integration plans) into an existing real codebase, or port a codebase
  from one platform/framework to another. Covers: reading source code
  deeply before writing code, mapping platform APIs to their equivalents,
  avoiding premature architectural decisions, direct file patching over
  delegation for complex multi-file changes, the path-collision
  pre-check that prevents silently destroying tracked files when a spec
  specifies literal package paths, and the **location-confirmation
  checkpoint** for "implement this as a separate / generalized / own-folder"
  requests. Loaded when user says "implement that", "build this spec",
  "port X to Y", "rewrite X for Windows", "generalize this to any new
  build", "put it in its own folder", or "this is a separate requirement".

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
  - generalize this to any new build
  - put it in its own folder
  - this is a separate requirement
  - own repo on github
  - go to the <name> repo
  - mind drop
  - repo at <path>
  - implement against <repo-name>
  - switch from <vendor> to <vendor>
  - swap to <vendor>
  - use <vendor> instead
  - replace <vendor> with <vendor>
  - move from <vendor> to <vendor>
  - use <api> oauth for <vendor>
  - use my <vendor> key
  - use this design
  - use this exact design
  - match this style
  - apply this look
  - make it look like this
  - rebuild the front end
  - design only no logic
  - only change the design
  - restyle this app
---

# Codebase Porting & Spec Implementation

## Location-Confirmation Checkpoint (FIRST thing, before reading code)

**When the user asks you to build / port / generalize something, the first
question is not "what does the source look like."** It's "where does this
live?" The user has corrected this in anger at least once:

> *"Stop. You're building it inside Omni Memory where I explicitly mentioned
> it was a separate requirement I wanted to generalize to any new build.
> It should be in its own folder."*

**HIGH-INTENT phrases that mandate a confirmation question before writing
any file:**

| Phrase | What it means | Where it should NOT go |
|---|---|---|
| "I want this generalized" | Workflow is meant to be reusable across many builds | Inside any single project repo |
| "It should be in its own folder" | A sibling location, not inside the existing one | Inside the existing repo the user is currently discussing |
| "This is a separate requirement" | Distinct from whatever project is being discussed | Piggybacked on the current project |
| "Make it a public repo on [account]" | The user wants to share this as a public artifact | Buried in a private repo |
| "Generalize this to any new build" | The whole point is decoupling from the current project | Anywhere coupled to the current project |
| "Add it to [other project]" | That other project is the target | The current project |

**The rule:** if the user's framing contains *any* of the above, do not
default. Ask one question — *where should this live?* — and wait for the
answer. The cost of one question is seconds. The cost of scaffolding in
the wrong repo and being told to start over is minutes plus trust.

**"Similar plumbing exists" is not "this belongs there."** If the user is
working in Omni-Memory and the spec workflow needs Telegram bot access,
the bot is reached by API, not by editing the bot's source. Same logic
for any other shared plumbing (DB, env files, auth tokens).

## Design-Only Refactor Confirmation (the "use this design" trap)

A common variant that *looks* like the location-confirmation case but is
its own failure mode: the user uploads a mockup or screenshot and says
"use this exact design" without naming a target repo. The default move
is to apply it to whatever app is open in the conversation. The wrong
move. Three sub-questions have to be answered before writing any file:

1. **Which repo is the target?** If the conversation was in project A and
   the user said "use this design" without naming a project, *ask*. They
   may have meant project B (a related but separate app) or project C
   (a clone of A that doesn't even exist locally yet). Cloning from
   GitHub and working in a clean checkout is cheap; rewriting the wrong
   project and reverting costs minutes plus trust.
2. **Logic or only visuals?** "Use this design" is ambiguous between
   "rebuild the front end, keep the backend" and "match this style,
   touch nothing else." Both are valid interpretations. The right move
   is to state the assumption in one sentence ("I'll keep all the
   handlers/state/AI calls untouched and only swap the visual layer —
   tell me if you want logic changes too") and wait for the green light.
   Don't ship a logic change under a design ask.
3. **Which components get the new skin?** The reference may show one
   screen (e.g. an upload widget), but the target app has five screens.
   Default to applying the visual rules (palette, radius, shadow,
   typography) to the whole UI, not just the screen the user showed.
   Then call that out so the user can scope it down.

**Real incident (2026-06-25, MeetingMind design → wrong project):** The
user uploaded a Stripe-style "MeetingMind" mockup. The active project
was MindDrop. I applied the design to `MeetingStudio.tsx` in MindDrop,
built, committed, and pushed. The user replied "stop!!!!! revert all
the changes as they are not being applied to the right project. it
needs to be applied to the video meeting minutes manager, not
minddrop." I `git checkout`ed the file, cloned the actual target repo
(`Video-Meeting-Minutes-Manager`), and only then started. Then I
shipped a full rewrite — until the user clarified "it's only a design
change, no change in the logic, just new fonts/ buttons, layout. all
functionalities on that page will remain the same." I had to
re-examine the second repo's `App.tsx` and rebuild the visual layer
*without touching any handler or state*. Two full rebuilds instead of
zero, because the location + scope + scope-of-scope questions were
never asked.

**The reflex:** when the user shows a mockup and says "use this," your
first three messages should be:

```
1. Confirm the target repo: "I'll apply this to <repo> — confirm?"
2. Confirm the scope:     "Design only, no logic changes — confirm?"
3. Confirm the breadth:   "Apply the visual rules app-wide, or just
                           the screen you showed?"
```

A 3-message confirm costs 30 seconds. A two-build revert costs 10+
minutes plus the user's patience.

**For the spec-driven-build case specifically** (the live case that
surfaced this lesson): see the `spec-driven-build` skill — it has a
dedicated pre-flight check section that operationalizes this rule.

## Core Principle: Investigate Deeply Before Writing Anything

When the user says "Don't make shortcuts or summarize, go deep in the investigation", they mean: read every source file, understand the full subsystem map, build a complete picture BEFORE writing any spec or making architectural decisions. A shallow read produces a shallow spec.

**Approach:**
1. Read ALL source files completely — not just "key" files. The full picture lives in the details of every file.
2. Map every subsystem: state machines, animation math, API calls, design tokens, analytics events, permission system, IPC protocol. Nothing is decorative.
3. Write the spec AFTER the investigation, not during. The spec should be a direct reflection of what you found, with zero approximation.
4. Lock major decisions (language, framework, service choices) at the top of the spec before writing anything else.

## Path-Collision Pre-Check (CRITICAL — do this BEFORE any `mkdir` or `write_file`)

**When a spec specifies literal package paths, the path may already exist as a tracked FILE in the repo.** A naive `mkdir <spec_path>` silently destroys the file. This was a real loss in one session where a spec asked for `hermes/task_contract/` and `hermes` already existed as the CLI launcher script.

**Before any of mkdir, write_file, or patch on the target path, run a 4-step identity check. Skipping this when the user's framing is casual ("go to the MindDrop repo", "implement this spec") is how you clobber unrelated state.**

**The 30-second pre-check, in order:**

```bash
# 1. Does ANY directory match the spec name? (case-insensitive — Linux/macOS are case-sensitive filesystems
#    so a spec written as "MindDrop" won't match a folder named "minddrop" without -i)
find ~ -maxdepth 5 -type d -iname "<spec-folder-name>" 2>/dev/null

# 2. For each candidate, is the git remote consistent with the spec's repo?
#    A folder named "X" with a remote pointing to "obsidian-vault-backup" is NOT the X repo.
#    It's almost certainly an unrelated workspace mislabeled, OR a vault backup folder.
cd <candidate> && git remote -v && git log --oneline -3
# If the remote doesn't match the spec, REFUSE TO WRITE. Ask the user which one is correct.

# 3. Does the path exist as a file?
stat <spec_path> 2>&1 | head -3

# 4. Is it tracked in git?
git ls-files <spec_path>

# 5. Are there same-name siblings? (e.g. spec wants dir A/, repo has file A AND dir A_other)
ls -la $(dirname <spec_path>) | grep -E "^-" | awk '{print $9}' | grep -E "^<name>$"
```

**Decision tree:**
- If multiple candidates match by name (case-insensitive) → **case-mismatch trap**. The folder with the right *case* is usually the real one; the other is often a vault backup, sibling project, or temp workspace. Verify via git remote.
- If `stat` shows a file at the parent path AND `git ls-files` confirms it's tracked → **the spec's path collides**. Either:
  - (a) PICK A NON-COLLIDING LOCATION (most common — log the deviation in the package's `__init__.py` and the developer guide)
  - (b) Ask the user before clobbering
  - (c) `git checkout HEAD -- <file>` to restore, then proceed with the new location
- If `stat` shows a directory → safe to `mkdir` inside
- If the path doesn't exist → safe to `mkdir -p`

**Real incident (2026-06-24, MindDrop auth bypass):** Spec referenced `benclawbot/MindDrop2-Opencode` (capital M). Local `find -iname` found two folders: `MindDrop2-Opencode/` (the real repo) AND `minddrop2-opencode/` (lowercase m, git remote was `obsidian-vault-backup`, contained 27+ modified vault conversation files). A naive `cd` to the first lowercase match would have clobbered a vault backup. A case-sensitive search would have missed the real repo. **Both behaviors are wrong.** The correct move is case-insensitive discovery + git-remote verification on every candidate.

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
- **`git status` lies when `core.fileMode` is unset.** `chmod +x` on an existing tracked file makes git report it as "modified" even though the content is identical. Run `git config core.fileMode false` before any perms audit, or diff `--stat` will show false-positive "M" everywhere. New scripts you add should be chmod +x'd, but existing scripts should not be touched (their perms are intentionally what's tracked).
- **The "two script versions + README only documents one" trap.** When a repo has parallel scripts (`run-hub.sh` and `hub-pull.sh`, `setup.sh` and `install.sh`, etc.), the README often only documents the canonical one. The undocumented one is usually legacy code that hardcodes an old path. Find it with `search_files` against README references — if it's never mentioned, either update it to match the README's path scheme or delete it. Carrying dead scripts in the repo is worse than deleting them.
- **Install scripts that block on no-TTY.** `read -p "var: " val` hangs forever in `bash script.sh` from a non-interactive context (CI, cron, piped). `curl` without `--max-time` hangs on bad DNS. From day 1 of writing an install/bootstrap script: (a) gate `read` calls behind an `INTERACTIVE` check (env var, `[ -t 0 ]` for fd 0 being a tty, or both); (b) put `--max-time 5` (or whatever) on every network call; (c) default to non-interactive-friendly behavior so CI doesn't need a special flag.
- **Local `git clone` made before `gh auth login` has no git creds wired.** Symptom: `gh auth status` is ✓, but `git push origin master` fails with `fatal: could not read Username for 'https://github.com'`. Fix: `gh auth setup-git` wires the gh token into git's credential store globally. Re-push works immediately. Alternative: `git push "https://$(gh auth token)@github.com/owner/repo.git"` for a one-shot.
- **`nohup` + `&` + `> /tmp/x.log` inside a foreground `terminal()` call is rejected.** Hermes tracks background processes via `background=true`; the shell-level wrappers (`nohup`, `disown`, `setsid`, trailing `&`) are blocked from foreground calls because they break lifecycle tracking. For dev servers / watchers: use `terminal(background=true)` (no `notify_on_complete` for long-lived processes that never exit). For one-shot: just foreground, foreground timeout is generous.
- **LSP errors inside `/* ... */` blocks ≠ `tsc` errors.** The in-process LSP flags `Cannot find name 'Foo'` even when `Foo` is inside a JSDoc-style block comment. The real `tsc --noEmit` (and the build's `tsc` step) treats `/* */` as a comment and skips it. When typecheck fails with names-from-comments errors, the *real* cause is usually missing types in `node_modules`, not the commented imports. Verify by `git stash` → re-run typecheck → compare counts. Pre vs post must be identical for a clean implementation.
- **A half-installed `node_modules` produces phantom typecheck errors that vanish after a clean reinstall.** Symptom: `tsc --noEmit` reports 20+ `Cannot find module 'X'` errors for modules that ARE in `package.json` dependencies. First fix attempt is `npm install` — which fails with `ENOTEMPTY: directory not empty, rename '.../node_modules/acorn' -> '.../node_modules/.acorn-XXXXX'`. The only reliable recovery: `rm -rf node_modules package-lock.json && npm install`. Then re-run typecheck — errors drop to zero. Always clean-reinstall before assuming a real typecheck failure.

## README-Driven Install Implementation (variant: spec lives in the README)

A common variant: the user points at a repo's README and says "implement what's needed for [target] and check it works locally." There is no external spec doc — the README is the spec. Same workflow discipline applies, but the source-of-truth reads differently.

**Phase 0: Confirm the README is fetchable and is the canonical spec.** A private repo is the most common friction: `gh auth status` will be X until the token is re-authed, then `gh api /repos/owner/repo` returns metadata (default branch, language, size, pushed_at). `gh api /repos/owner/repo/contents/README.md` returns the file as base64 — decode it. If the repo is 404, it's a typo or the repo doesn't exist; check the user's other repos with `gh api /users/<owner>/repos --jq '.[].name'` and ask which one they meant.

**Phase 1: Audit the README against the actual tree.** The README describes the world as it should be; the tree shows the world as it is. Walk both, and produce a gap table:

| README claim | Reality | Gap |
|---|---|---|
| `cd ~/Omni-Memory/hub && npm install` | `hub-pull.sh` hardcodes `$HOME/memory-hub` | Script contradicts README. Fix or delete. |
| Exports are `Omni-Memory/exports/{device}/` | Collector writes `~/.memory/exports/manifest_{device}_{ts}.json` (flat) | Two different layouts; hub scanner only reads one |
| Manifests have `file:` paths | Hub reads those paths verbatim | Cross-machine paths break on hub. Fix hub, not collector. |
| Hub ingest handles 0 events | `merge-events.mjs` throws `Fatal: ENOENT` when exports dir missing | Make the missing-dir case a clean skip, not a fatal exit. |
| Troubleshooting: `cat .../exports/*/manifest.json` | Files are named `manifest_*.json` | Wrong glob. README bug. |

**Phase 2: Verify with REAL synthetic data, not just "the script exits 0."** `bash install.sh` returning exit 0 is not proof. Proof is: seed a minimal real-shape export → run each pipeline stage → assert the rows landed in the destination. Specifically:
- After `node merge-events.mjs`, query the destination table: `SELECT COUNT(*), source FROM events GROUP BY source` — assert ≥ 1 row per expected source.
- Re-run the same command — assert `ingested=0 skipped=N` (dedup works via `event_hash`).
- If a Telegram bot is part of the pipeline, start it with a fake token and confirm it returns 401 cleanly (proves the network + auth wiring works, just with bad creds).
- Capture every command's exit code AND the log tail. "Script ran" is not the same as "script did the thing."

**Phase 3: Ship the install path the user actually asked for.** A README that says "clone, then run 7 steps manually" is a spec for an installer. Build the one-shot `install-<target>.sh` that:
- Checks prereqs (with explicit `command -v` + version checks, not assumptions)
- Idempotent: re-runs without breaking existing state (don't blow away a populated env file; skip already-set vars)
- Supports `INTERACTIVE=0` / `NONINTERACTIVE=1` env var for CI
- Has `--max-time` on every network call (default 5s)
- Verifies the install worked before claiming success (run the pipeline once, check log, exit non-zero on first failure)
- Logs to `~/Library/Logs/<app>/` (macOS convention) or `~/.local/share/<app>/logs/` (Linux convention), NOT just stderr

**Phase 4: Update the README in the same commit.** Every code change that closes a gap should also update the README to:
- Reference the new script (`bash install-mac.sh` in the install section)
- Document any non-obvious fix (the ENOENT recovery, the recursive walker behavior)
- Fix factual errors in the README itself (wrong globs, outdated paths)
- Tick the "what works" checkboxes that are now true

**Phase 5: Commit + push.** Auth check first: `gh auth status`. If git push fails with "could not read Username" even though gh is authed, run `gh auth setup-git` to wire git to the gh token, then retry. Verify the push landed: `gh api /repos/owner/repo/commits --jq '.[0] | {sha, message: .commit.message[0:80]}'`. Then summarize the commit (sha + files changed + what was verified) in the final message — that's the only thing the user has to verify before moving on.

## Reference Materials

- `references/clicky-macos-to-windows.md` — Full Clicky port: 25-file inventory, subsystem math, VAD params, MiniMax API format, Windows API mappings, locked decisions.
- `references/spec-implementation-playbook.md` — Detailed playbook for implementing build-ready specs into real codebases: investigation order, spec-vs-reality delta construction, deviation logging, and acceptance-checklist verification patterns.
- `references/extending-existing-implementation.md` — When the spec is a v2 of a v1 you already shipped: extension-in-place workflow, additive schema changes, regression-net testing, the recorder-setter-mirror-schema gotcha, disabled-by-default pack defaults, and the iterative-test-after-each-module pattern.
- `references/readme-driven-install.md` — README-as-spec workflow: audit table format, real-data verification recipes, the install-script noninteractive + max-time pattern, and the gh-auth-setup-git gotcha for HTTPS pushes.
- `references/vendor-swap-in-spa.md` — When the user says "switch from X to Y" for an AI provider, auth, or storage in a deployed frontend. Feature parity audit (which old features have no new-vendor equivalent), service rewrite with shape-preserving signatures, pushback reflex for technically-wrong vendor choices (ChatGPT OAuth, Firebase Auth for local-first). Worked example: 2026-06-24 MindDrop Gemini+Firebase → M2.7+localStorage (76% bundle reduction).
- `references/design-only-rewrite.md` — When the user shows a mockup and says "use this design" against an existing app. The five-step recipe (palette → surfaces → CTA → status panel → verify), the Tailwind v4 + global-CSS fight (when `index.css` overrides `[type="submit"]`), the "no logic changes" feature audit, and the visual atoms to swap (dropzone, status panel, language toggle, gradient direction).

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

**Why:** when something breaks, the failure tells you exactly which module caused it. Batch-and-debug at the end is the worst failure mode — three modules added, regression somewhere, no signal where to start.

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

When the user says "enable those 3" and the right interpretation is "make it non-negotiable," the move is **lock the default, don't override the toggle.** Three places get updated:

1. **The default config YAML** (the in-code `default_config_yaml()` string) gets a comment block listing the always-on vs opt-in packs. Anyone who runs `hermes contract init` sees the policy.
2. **A regression test** that asserts each always-on pack's `enabled` field is `True` in the default config. Future contributors who try to flip a default fail CI with a message pointing at the policy doc.
3. **The user guide** splits the pack table into "Always-on (cannot be disabled)" and "Opt-in (can be turned off)."

**What NOT to do:** silently override `enabled: false` in user config at runtime. That's hostile — it fights the user. The "always-on" guarantee is the *default*, not a runtime override. Users who explicitly disable a pack in their YAML are doing so deliberately (e.g. to debug an issue); respect that.

**The signal that you want this pattern, not a simple "turn it on":**
- User says "enable those 3" without specifying config-file edits → they mean "make it the system's policy"
- User says "always run X" or "never turn off X" → same
- User says "make X default" → they likely just want a config-file change, no policy lock

When in doubt, ask. The cost of one clarifying question is lower than the cost of either shipping the wrong level of enforcement.
