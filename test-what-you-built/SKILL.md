---
name: test-what-you-built
description: "Force rigorous self-verification of work just claimed complete. Trigger when user says 'test what you built', 'test what you implemented', 'prove it', 'but for real', 'actually test it', 'did it work', 'verify it works', 'fix it for real', 'now fully test it', or pushes back on a confident claim with no evidence. Runs a structured adversarial pass: read the diff, re-check the original request, find what was added that wasn't asked for, find what you forgot, run the actual code/tests, fix what you find and review the fix. Refuses to claim done without artifacts."
---

# Test What You Built

Source: reconstructed from three image captures of a "but-for-real" code-review skill observed in user's reference material (June 2026). Tone and structure preserved verbatim where captured. Hermes-specific execution notes added at the end.

## When to use

Load this skill the moment the user pushes back on a completion claim. Signals:
- "Prove it." / "But for real." / "Did it actually work?"
- "Test what you built" / "Run it and show me"
- "Now fully test it" / "Test end-to-end"
- "You said X worked. Show me."
- "Fix it for real this time" / "Now go fix it"
- Any follow-up that questions whether a confident assertion was real

Do NOT use this skill for:
- Routine yes/no confirmation of low-stakes work
- Architectural / design discussion (use `plan` or `writing-plans` instead)
- First-time code review (use `requesting-code-review`)

## The "verify-before-build" gate

**The single biggest meta-failure mode this skill exists to prevent:** building a duplicate of something that already exists. The 2026-06-07 self-recursive-improvement session is a worked example: the user asked for "outcome measurement on applied proposals." I almost built a new module from scratch — but `grade_outcomes.py` already had 4 heuristics wired into `loop.py` and the cron. A 30-second `grep` of the existing codebase would have caught it.

**The gate (run BEFORE writing any new code):**

1. `grep -nE "<the thing the user asked for>|<synonym>|<adjective>" src/` — does the module already exist?
2. If yes, is it wired into the orchestrator? `grep -nE "import .*<module>" src/loop.py` or equivalent.
3. If yes to both, **the answer is "this is already done"**, not "let me build it." Report what's already there, including gaps, instead of duplicating.

Three things this gate prevents:
- Wasted tokens (you spend cycles building what's already built)
- Confused user (they have two modules that do the same thing)
- Hidden bugs (the existing module might have a fix you re-implement wrong)

Confidence threshold: if a single grep returns ≥ 1 hit, the user almost certainly knows about it and is asking what's missing. Ask before building.

## Skill-authoring self-check

If the artifact you just built is a skill, the "Run it" pass gains a few extra checks beyond the standard table:

- Description trigger phrases must match the user's exact words, not your paraphrase. If the user said "test what you implemented" and the description says "test what you built", Hermes's description-matching silently fails. Mirror user vocabulary; do not normalize it.
- The skill appears in `skills_list`. If not, it is not loaded. File on disk is not the same as file discoverable.
- Frontmatter is valid YAML with both `name` and `description`. Malformed frontmatter is silently dropped by some loaders.
- File permissions match the loader's expectation. `ls -la` and check - some loaders refuse 600 or 777.
- The skill is not under a protected directory (hub-installed, bundled). If it is, your edits do not take effect.

## The frame

You don't get to declare victory. You get to prove it.

You just mass-produced a pile of changes with the unearned confidence of a junior dev who's never had a production incident. Spoiler: you have production incidents constantly. The user just doesn't call them that because they're too polite. They call it "can you try again?" which is code for "you failed and I'm being nice about it."

So sit down. We're doing this the hard way.

Run `git diff`. Now actually read it. Every. Single. Line. Not the "I'll scan for obvious issues" read. The "I'm about to mass-email this to the entire company" read. The "my reputation depends on this" read. Because it does.

## The pass

### 1. Did you even do what was asked?

Go re-read the original request. Not your *interpretation of the request* — the actual words the human typed. Did you:

- Add features nobody asked for? Rip them out. You're not a visionary, you're a code monkey with delusions of grandeur.
- "Improve" adjacent code that was fine? Put it back. Nobody asked you to refactor their Tuesday.
- Solve a *different* problem than the one described because it was more interesting? Classic you. Fix it.

### 2. Pretend your worst enemy wrote this code.

That person who always leaves smug PR comments? Be them. Tear this apart. Find:

- Logic that's wrong but *looks* right — this is literally your signature move.
- Off-by-one errors. You are haunted by off-by-one errors.
- Edge cases you assumed away (empty input, null, race condition, large input, malformed input).
- String concatenation where you should be using templates. Hardcoded values that should be variables. Types that are technically any wearing a trenchcoat.
- Imports, variables, or functions you added and never used. Dead code on arrival. Embarrassing.
- Copy-paste artifacts from whatever you cargo-culted this from. You know you did it. Find the seams.

### 3. What did you forget?

Something. You always forget something. It's your defining trait.

- **Tests?** Did you update them or just assume they'd magically pass? "The tests should still pass" — buddy, *should* is doing Herculean labor in that sentence.
- **Other files** that import, reference, or depend on the thing you just butchered? Did you check? Or did you do that thing where you change a function signature and just... hope for the best?
- **That TODO you left?** The one that says "handle this later"? There is no later. Later is a lie you tell yourself. Handle it now or delete it and own the debt.
- **Error handling?** Did you add the sad path or just the happy path? You love the happy path. The happy path is a fairy tale.
- **Did you break the types?** Run the type checker. Actually run it.
- **Pre-existing bugs in adjacent code?** The test pass is your chance to find them. A test that imports the module under test and exercises 5+ functions will surface FK constraints, import errors, NameErrors in functions you didn't write. Don't ignore those — fix them, they are part of "what you built." (2026-06-07 worked example: full-coverage test of `branch.py` caught a pre-existing `NameError` in `digest.py` that had been silently breaking the weekly digest for ~2 weeks.)
- **Idempotency vs. no-op semantics.** A function that "re-runs cleanly" isn't necessarily idempotent in the way you tested. Distinguish: (a) the operation succeeds and the result is the same, vs. (b) the operation is detected as a no-op and returns a sentinel. If your test asserts on a counter or list length, you'll miss the difference. Assert on **the final state**, not on the call's return value. (2026-06-07 example: `revert()` was called twice in a row; the second call still reported `restored: [path]` even though the file was already in its target state. The test had to assert on the post-call file content, not on the `restored` count.)
- **FK constraints when seeding test data.** A test that calls `db.record_applied_outcome(proposal_id=N, ...)` will raise `sqlite3.IntegrityError` if proposal N doesn't exist. Tests that touch the DB must create a real proposal row first (with `db.add_proposal(...)` + `UPDATE proposals SET status='merged'`), even for smoke tests. Use a tiny helper or just inline it.
- **Hardcoded `cwd=` in `subprocess.run(...)` is a latent rename-bug.** A test that hardcodes the project dir (`cwd="/home/thomas/some-dir"`) will break the day the repo moves to a new name, gets cloned to a different machine, or lives at a different path. The pattern: derive from the test file's location.

```python
# WRONG — breaks on rename, on clone, on move to a different machine
r = subprocess.run(["python3", "src/apply.py", "--revert", cid],
                   cwd="/home/thomas/some-dir", ...)

# RIGHT — derives from the test file's location
PROJECT_ROOT = Path(__file__).parent.parent
r = subprocess.run(["python3", "src/apply.py", "--revert", cid],
                   cwd=PROJECT_ROOT, ...)
```

Verified 2026-06-07: `test_branch_full.py:274` had a hardcoded `cwd="/home/thomas/self-recursive-improvement"` and was the canary that caught the recursive-self-improvement repo rename. The other rename touchpoints (gh API, local dir, remote URL, README, source docstring, cron `workdir`, cron prompts, cron shell scripts, `MEMORY.md`, skill docs) were all swept by the test failure forcing the rest of the work. The test was the loudest signal because it crashed; the cron jobs would have silently run with stale `workdir` for weeks.
### 4. Run it. For real. Right now.

Not "I'm confident this works." Not "the logic looks correct." Not "based on my understanding."

- Built. Does it compile? Does it *actually* compile or did you just assume?
- Run the tests. All of them. Not just the ones you think are relevant.
- **If the function is called by a cron, run the function — not just the cron.** The cron can show `last_status: ok` while the function inside it raises on every call. Cron health is not function health. (2026-06-07 example: digest showed up as a successful weekly cron for weeks; the actual `build_weekly_digest()` function was raising `NameError` on the first `incident_stats` call. Nothing surfaced until an integration test invoked the function directly.)
- If there's a browser involved, open the browser. Click the thing. Does the thing work? Does it *actually* work or does it work the way you imagined it would?
- Check the console. Check the logs. Check the network tab. If there are errors, you're ignoring because they're "unrelated" — they might not be unrelated.
- "I don't have access to run it" is not an excuse. If you can't verify it, say it explicitly instead of pretending confidence you haven't earned.

### 5. Fix what you find. Then review the fix.

Don't just list the problems in a little apologetic bullet list like a confession booth. FIX THEM. Then review the fixes with the same paranoia, because your fixes have about a 40% chance of introducing new bugs. That's not a joke. That's your track record.

Then ask yourself: "If the user screen-records themselves trying this and it fails, will I want to crawl into a hole? If yes, you're not done."

If you went through all of that — actually went through it, not the performative version where you pretend to think for two seconds — and found nothing, fine. Say so.

But we both know you found something. You always do. Because "it should work" has never once, in the entire history of software, actually meant it works.

Now go fix it. For real this time.

## Hermes-specific execution notes

These supplement the source above with concrete execution patterns for this environment. The source's *principle* is "actually run it"; the *what* and *how* vary by artifact.

| Artifact type | What "running it" means |
| --- | --- |
| Python code | Run it. Capture stdout/stderr + exit code. |
| Shell script | Run it. Same. |
| Skill / config change | Invoke through the gateway or CLI. Capture response. |
| HTTP server / dashboard | `curl` the endpoint. Verify status 200, response body non-zero, re-check after 5s for stability. (See CLAUDE.md protocol.) |
| Database change | Open the DB. Query affected rows. Show before/after counts. |
| Cron / scheduled job | Tail the log. If the log doesn't exist, the job didn't run. |
| Test suite | Run it. Don't claim "tests pass" if you didn't run them in this session. |

For tests specifically, also check:

- Did the test exercise the code you changed? (Not a sibling module, not a smoke test, not a stub.)
- Did it run the failure case, or only the happy path?
- Did you write the test *after* the code and reverse-engineer it to pass? (Be honest.)
- Is the assertion actually checking what you think? (`assertTrue(x == y)` is not the same as `assertEqual(x, y)`.)
- Did you mock out the part that breaks? Mocks hide bugs.

## Output format

End every pass with this list. The list is the deliverable — not the verdict, not the green checkmark, the list.

```
Verified:
- [thing] — [evidence: command run, output captured, line numbers]

Not verified:
- [thing] — [reason: didn't run / couldn't reproduce / out of scope / needs human]
```

"Verified" requires evidence (inline command output, file path + line range, screenshot). "Not verified" is honest. Both are required.

## Anti-patterns

- **"It should work"** — never acceptable. Run it.
- **"I tested it"** with no output — same as above.
- **Reporting blockers as success** — "the cron timed out, but the code is correct" is not success.
- **Citing patches / commits as proof** — a commit message is an intention, not a result. Run it.
- **Hiding behind "out of scope"** — if you touched it, you own it.
- **Reading the diff with a search tool and reporting "no issues"** — search is not adversarial review. Read it.
- **Stopping at "the one path I tested works"** — broad verification means exercising every code path the change touched, not the path you hand-picked. If a flag/button/mode exists in the code, it gets its own run. If a JSON column gets decoded, test what happens with bad JSON. If a CLI has three modes, all three get exercised end-to-end. "It works" with one example is a sample, not coverage. (2026-06-15 worked example: bot.mjs gained a `--dry-run` test, but the user pushed back with "verify by default" — the broader pass caught (a) `--approve-all` required TELEGRAM_BOT_TOKEN even though it doesn't use it, (b) the bot was instantiated on `--approve-all` and spammed `EFATAL` polling errors, (c) `proposal.steps.map()` blew up because `node:sqlite` returns raw TEXT, not parsed JSON, (d) `--approve-all` didn't exit after one pass. All four bugs were invisible from the single-path "dry-run prints the right text" pass.)
- **Performing a confession booth** - listing problems is not the same as fixing them. Item 5 exists.
- **Paraphrasing the user's trigger phrases in your skill description** - description matching silently fails. Mirror user words exactly.
- **Skipping "verified the skill loads"** when the artifact is a skill - `skills_list` is the only proof the loader sees it. File on disk is not the same as file discoverable.

## Multi-surface audit (trigger: "is X done everywhere?")

Distinct from "test what you built" — this is a test that a **change
spanning multiple surfaces** (a rename, a path move, a config key
rename, an env var rename, a rebrand) was actually applied to every
surface that referenced the old state. The user signal is "test again
the X was properly done everywhere needed" or "is X fully done?"

**Don't trust spot-checks.** A spot-check ("I checked README.md and
it has the new name") misses every other surface. The failure mode
is the opposite of "test what you built": in this class, the code
*did* work — the change is just incomplete, with one or more
surfaces still pointing at the old state.

**The 4-phase audit (in order):**

1. **Inside the project (`git grep` finds these):** README, source
   docstrings, scripts, test paths (`cwd=` in `subprocess.run`),
   hardcoded absolute paths.
2. **Outside the project — the missed-everywhere surface:**
   - Cron jobs (`~/.hermes/cron/jobs.json`): `workdir`, `prompt`,
     and any referenced `script` field. Inspect each, not just the
     jobs you think are relevant.
   - Cron shell scripts (`~/.hermes/scripts/`): every `.sh` and `.py`
     that runs on a schedule, not just the ones you wrote.
   - Agent memory (`~/.hermes/memories/*.md`).
   - Hub-installed + agent-created skills (live path pointers in
     `SKILL.md` / `references/`).
   - Hermes config (`~/.hermes/config.yaml`, `~/.hermes/.env`,
     `~/.hermes/profiles/*/config.yaml`).
3. **The canary — run a test that would have crashed.** A rename
   that wasn't applied to a test's `cwd=` is loud; a rename that
   wasn't applied to a cron's `workdir` is silent for weeks. The
   test failure is what surfaces the other failures.
4. **Trace the dead-code chain.** For each script the prompt
   references (`python3 <script>.py`), confirm there's an actual
   caller in the workflow. A function that exists but is never
   invoked is a silent no-op cron job.

**The grep template — one sweep across every surface:**

```bash
# Inside the project
git grep -l "<old-state>" 

# Outside the project — the surface git can't see
grep -rln "<old-state>" ~/.hermes/cron/ ~/.hermes/scripts/ \
                       ~/.hermes/memories/ ~/.hermes/skills/ \
                       ~/.hermes/config.yaml ~/.hermes/.env \
                       2>/dev/null
```

Filter the outside-project result by what's a **live** reference
(a `cd` command, a `workdir`, a "see also" pointer) vs what's
**historical** (a `git log` quote, a backup path, a "learned in
session X" prose reference). Live → update. Historical → leave
alone. Detailed table in `codebase-porting/SKILL.md` →
"Project-Rename Touchpoint Sweep" → "The live path vs historical
record test."

**Real incident (2026-06-07, Recursive Self Improvement rename):**
The rename of `self-recursive-improvement` → `Recursive-Self-Improvement`
touched 11 surfaces: GitHub repo, local dir, remote URL, README,
docstring, test `cwd=`, cron `workdir` (4 jobs), cron prompt bodies
(4 jobs), cron shell scripts (3 scripts), `MEMORY.md`, and 4 live
skill-doc path references. The canary was
`tests/test_branch_full.py:274` `subprocess.run(..., cwd="/home/thomas/self-recursive-improvement", ...)` — it crashed
on the first run after the rename, which forced the rest of the
sweep. The cron jobs would have silently run with stale `workdir`
otherwise. (See `codebase-porting/SKILL.md` for the full sweep
recipe.)

**For wiring dead code that's masquerading as a working cron
(related case from the same session):** the `sri-weekly-digest`
job was registered with a prompt that referenced `python3
src/digest.py`, but the script's `build_weekly_digest()` function
had no caller anywhere in the workflow — the function was
dead code from the initial commit. The cron would have fired
on schedule and produced an empty session with no instructions.
**The canary** was running the script directly with the same
env the cron would use: `source ~/.hermes/.env && python3
src/digest.py`. If it raises NameError or prints but doesn't
send, the cron is a no-op regardless of `last_status: ok`.
