# One-Shot Review: Common Findings

Reference for the kinds of issues this skill should catch in ~30 seconds. Not exhaustive — add patterns as you find them.

## Likely Bugs (catch these first)

- **Unused imports** — imported but never referenced; easy to miss in skimming
- **Wrong variable in scope** — e.g., using `result` when the actual variable is `response`
- **Off-by-one in loops** — `range(n)` vs `range(n+1)`, slice `[n:]` vs `[:n]`
- **Missing None/null check before attribute access** — `x.y` where `x` can be None
- **Swallowed exceptions** — `except: pass` or `except Exception: ...` without re-raise
- **Bare `os.remove(path)` without try/except** — fails with FileNotFoundError if path doesn't exist; use `try: os.remove(path) except OSError: pass`
- **Race condition in cached computation** — computing value outside lock then storing inside lock (window where concurrent callers duplicate work); compute-and-store must both be inside the lock
- **Wrong default argument** — mutable default `def foo(x=[])` is a classic Python footgun
- **Function returns on some paths, None implicitly on others** — especially in error handlers

## Security Risks (flag immediately)

- **Hardcoded credentials** — API keys, tokens, passwords in source
- **SQL injection** — f-string or % formatting in queries instead of parameterized
- **Unsanitized input to shell** — `os.system(user_input)`, `subprocess.run(shell=True)` with user data
- **Secrets in error messages** — logging or error responses that expose internals

## Code Smell (flag only if obviously wrong)

- **Copy-paste duplication** — identical or near-identical blocks within 20 lines
- **Commentless business logic** — a block with no comment that does something non-obvious
- **Inconsistent naming** — `get_user()` in one place, `fetchUser()` in another in the same file
- **God function** — a single function that does 10+ things across 100+ lines without section headers

## What to SKIP (don't flag)

- Style / formatting preferences
- Naming opinions unless genuinely confusing (e.g., `l` as a variable name)
- Trivial one-liners
- Anything you'd need a linter to confirm (this skill is judgment, not enforcement)
- Anything requiring deep context from other files to understand

## Speed Check

If you've spent 20 seconds and haven't spotted anything, don't dig deeper. Say "looked clean." The value is in the skim, not the deep audit.
