---
name: loop-test-isolation
description: Prevent tests from silently polluting production state when modules hardcode paths/constants at import time. Triggers when writing or debugging tests for any system that uses hardcoded DB paths, file directories, or marker files shared with prod.
---

# Loop Test Isolation

## When to use

Writing or debugging tests for any system where a module reads a path/dir at **import time** (not call time) and the test could end up sharing that state with prod. Hallmarks:

- `DB_PATH = Path(__file__).parent / "data" / "loop.db"` at module top
- `BACKUP_DIR = Path(__file__).parent / "data" / "backups"` at module top
- Any module-level constant that points at a shared filesystem location
- Tests that import the module → use it → share prod state

If you see `tests passing 100%` and `prod DB suddenly has weird rows`, this is the bug.

## The failure pattern

1. Test imports a module. Module reads `Path("data/loop.db")` at import time → `DB_PATH = /path/to/repo/data/loop.db`.
2. Test calls `db.add_proposal(...)` → writes to **prod DB** (no temp dir involved).
3. Test calls `db.add_proposal(...)` again with a different fixture → another row in prod.
4. Test cleanup runs in temp dir or asserts on temp results, but the writes are already in prod.
5. Loop's judge sees the test fixtures, scores them, applies them if above threshold, mutates prod.
6. You "fix" the test by adding temp dirs, but `apply.py` re-reads the same hardcoded path on its own import.

The marker file variant is worse: tests write `DONE_#N_...` markers to a shared `BACKUP_DIR`. Next test run, a different proposal hits the same `id` (auto-incremented fresh DB) → marker says "already done" → silent skip → test fails for confusing reasons.

## The fix (3 layers, all 3 required)

### Layer 1: env-var override in the production module

```python
# src/db.py
import os
from pathlib import Path

DB_PATH = Path(os.environ.get("SRI_DB_PATH") or Path(__file__).parent.parent / "data" / "loop.db")
```

Apply to **every** module-level path constant, not just the obvious ones. The obscure one (e.g. `BACKUP_DIR`, `LOG_DIR`, `MARKER_DIR`) is the one that bites you.

### Layer 2: env vars BEFORE imports in the test

```python
# tests/test_foo.py
import os, tempfile, shutil
TMP = tempfile.mkdtemp(prefix="sri_test_")
os.environ["SRI_DB_PATH"] = f"{TMP}/loop.db"
os.environ["SRI_BRANCHES_DIR"] = f"{TMP}/branches"
os.environ["SRI_BACKUP_DIR"] = f"{TMP}/backups"

# NOW import the modules — they'll read the env vars at import time
import db, branch, apply
```

Critical: env vars must be set **before** the imports. Python caches imports, so setting env after `import db` won't change `db.DB_PATH`.

### Layer 3: import-time assert (the load-bearing piece)

```python
# tests/test_foo.py
import db
assert str(db.DB_PATH).startswith(TMP), f"DB_PATH escaped test sandbox: {db.DB_PATH}"
assert "test" in str(db.DB_PATH) or TMP in str(db.DB_PATH)
```

Without the assert, env vars can silently fail to apply (typo in var name, env not exported, module imported via different path) and the test happily writes to prod. The assert converts silent corruption into a hard fail.

## Subprocess gotcha

If the test spawns a subprocess (e.g. `subprocess.run(["python", "apply.py", "--revert"])`), **pass env vars explicitly**:

```python
env = {**os.environ, "SRI_DB_PATH": f"{TMP}/loop.db", ...}
subprocess.run(..., env=env)
```

Otherwise the subprocess inherits only `os.environ` which may not include test-only vars if the test setup uses `monkeypatch` or pytest fixtures that don't propagate.

## Audit checklist when fixing this bug

Run a single test. Then immediately check prod:

```bash
sqlite3 ~/repo/data/loop.db "SELECT COUNT(*) FROM proposals WHERE source_session_id IS NULL AND evidence LIKE 't%'"
```

If that number went up, the test is still polluting prod. Don't trust a green test suite — verify state hasn't drifted.

## Pitfalls

- **Auto-increment IDs reset on fresh DBs.** A test fixture that asserts `id=1` works the first time, then on the second run the prod DB has a leftover `DONE_#1_...` marker file → next test's proposal with `id=1` gets skipped.
- **Bare `except OperationalError: pass` in migrations.** This silently swallows the "no such column" error and the test passes with a corrupt schema. Fix by putting the column in `CREATE TABLE` so fresh DBs work, keep the migration as a backstop.
- **Hardcoded `Path("data/...")` in tests** bypasses the module constant. Always use the constant (`branch.BRANCHES_DIR`) so the env-var override works.
- **Test cleanup that runs AFTER the test body** can't undo writes to prod. Cleanup has to be in setup, or better, isolate the writes so cleanup is unnecessary.
- **Don't trust "47/47 passing"** as proof of test isolation. Verify prod state hasn't drifted.

## Related patterns

- [systematic-debugging] — 4-phase root cause: understand bug before fixing.
- [test-driven-development] — RED-GREEN-REFACTOR. This is a RED phase that was missed.
