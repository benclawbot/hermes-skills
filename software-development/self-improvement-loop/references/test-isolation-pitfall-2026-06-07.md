# Test Isolation Pitfall — 2026-06-07

The session where "47/47 passing" was a false negative.

## Symptom

Ran the recursive self-improvement loop end-to-end. Judge correctly
rejected 18 pending proposals at 0.00 each. The dummies all matched
a single signature:

```
source_session_id = NULL
evidence          = "t11"
diff              = "<<<a>>>"
rationale         = "t11a" or "t11b"
target_path       = various tmp paths
```

The 18 dummies were **test fixture rows** that had been written to
the production `data/loop.db` by `tests/test_branch_full.py` on
every test run since the branch isolation work landed.

## Why this happened

`tests/test_branch_full.py:39-40` (before the fix):

```python
# Make a real DB init — these tests will pollute loop.db
db.init_db()
```

That comment was the **honest warning the original author left**.
`db.DB_PATH` is a module-level constant hard-coded to
`Path(__file__).parent.parent / "data" / "loop.db"`. The test
imports `db`, gets the prod path, and `add_proposal()` writes
there. Every `pytest` run added 5–18 dummy rows to the prod DB
and created 1–3 junk `data/branches/<cycle_id>/` directories.

`apply.run()` was never called by the test, so the dummies sat
in the DB unprocessed. Then the cron ran, judge saw them, and
correctly rejected all 18 — which is exactly the right signal
**from the loop's side**, but the test suite was still
polluting on the **test's side** of the trust boundary.

## What "47/47" really meant

The test reported all green because the assertions passed against
the rows it had just written. The whole "test verifies the loop"
promise was hollow — the test was verifying the loop's behavior
on rows the test itself had just created. The loop's *actual*
state (the 18 dummies, the junk branch dirs) was invisible to
the test runner.

The prior turn had reported "47/47 passing" as evidence the
rename was done correctly. It was technically true and
substantively a bug. The rename was fine; the test was never
isolated, and the "all green" was a false negative on the
**trust** in the green, not the green itself.

## The fix

Three pieces. Order matters.

### 1. Env-var-overridable path constants

`src/db.py`:

```python
# Before (line 18)
DB_PATH = Path(__file__).parent.parent / "data" / "loop.db"

# After
import os as _os
_DEFAULT_DB = Path(__file__).parent.parent / "data" / "loop.db"
DB_PATH = Path(_os.environ.get("SRI_DB_PATH", str(_DEFAULT_DB)))
```

`src/branch.py`: same pattern for `BRANCHES_DIR` → `SRI_BRANCHES_DIR`.

The `_DEFAULT_*` indirection is necessary because Pyright
chokes on the simpler `or` form (mixed `Path | str` types).
A two-line split with explicit `str()` cast makes the
type checker happy.

### 2. Set env vars BEFORE import in the test file

```python
# tests/test_branch_full.py (top, after sys.path setup)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# CRITICAL: redirect prod paths to temp dirs BEFORE importing.
# db.DB_PATH and branch.BRANCHES_DIR are evaluated at import time,
# so env vars must be set first or the constants freeze to the prod paths.
_TEST_ROOT = Path(tempfile.mkdtemp(prefix="sri_test_root_"))
os.environ["SRI_DB_PATH"] = str(_TEST_ROOT / "loop.db")
os.environ["SRI_BRANCHES_DIR"] = str(_TEST_ROOT / "branches")

import db
import branch
```

The trap: a `db.DB_PATH = temp_path` monkeypatch AFTER
`import db` is a no-op for any code path that captured the
constant at import time. The env-var approach works because
the constant is evaluated when the env var IS read, which
happens at import time — and we control import time by
controlling the order of `os.environ` and `import`.

### 3. Pass env vars to subprocesses

Test 9 runs `subprocess.run(["python3", "src/apply.py", "--revert", cid], ...)`.
A subprocess gets a fresh Python interpreter that re-imports
`db` and re-reads `os.environ`. Without explicit env-passing,
the subprocess sees the prod `SRI_DB_PATH` (or no env var,
falling back to the prod default). The parent's writes go to
the temp DB; the subprocess's writes go to the prod DB.

```python
r = subprocess.run(
    ["python3", "src/apply.py", "--revert", cid],
    cwd="/home/thomas/Recursive-Self-Improvement",
    env={**os.environ,
         "SRI_DB_PATH": str(db.DB_PATH),
         "SRI_BRANCHES_DIR": str(branch.BRANCHES_DIR)},
    capture_output=True, text=True,
)
```

The `cwd=` arg is unchanged — the file system paths are
correct, only the DB / branch dirs are isolated.

### 4. Pre-test 9 cleanup

`apply.run()` reads `status='merged'` proposals. Tests 1–8
in `test_branch_full.py` intentionally leave proposals in
'merged' state to assert `list_branches` / `prune` behavior.
When test 9 then calls `apply.run()`, it sees ALL the
merged proposals from tests 1–8 and rejects most of them
for non-existent target paths. Clean the slate before
test 9:

```python
# Inside test 9, just before add_proposal()
with db.conn() as c:
    c.execute("DELETE FROM judge_verdicts")
    c.execute("DELETE FROM thomas_feedback")
    c.execute("DELETE FROM applied_outcomes")
    c.execute("DELETE FROM proposals")
```

FK OFF not needed here because we're wiping everything
(judge_verdicts first to break the FK chain).

### 5. Marker files and backup dirs are shared state too

Round 2 of the same bug, discovered when test 9 started
failing AFTER the env-var fix above. The first fix only
covered `DB_PATH` and `BRANCHES_DIR`. The third per-process
state — `apply.py`'s `BACKUP_DIR` (where it writes
`DONE_<proposal_id>_<path>` idempotency markers) — was
still hard-coded to the prod path. Result: the test
successfully ran `apply.run()` once, wrote a `DONE_#N_...`
marker to the prod `data/backups/`, then on the next
test run (with a fresh temp DB, new proposal IDs starting
at 1, but the SAME `DONE_#1_...` marker still in the prod
backup dir), `apply_proposal()` skipped the proposal
because the marker said "already done." `apply.run()`
returned 0 silently. Test 9 saw 0 applied, failed.

Fix is the same pattern as #1: `SRI_BACKUP_DIR` env var,
default to the prod path. Same `_DEFAULT_BACKUP_DIR` +
`str()` cast indirection to keep Pyright happy.

**General rule:** audit every per-process state path the
loop writes to. The pattern isn't just "DB" — it's "any
path the test could share with prod." The checklist:

| Path type            | Example                | Test-pollution risk |
|----------------------|------------------------|---------------------|
| Database             | `data/loop.db`         | high (FK chains, auto-increment collisions) |
| Snapshot dirs        | `data/branches/`       | high (cycle_id collisions, junk dirs) |
| Backup / marker dirs | `data/backups/`        | high (marker-file idempotency leaks across runs) |
| Log files            | `logs/apply.log`       | low (append-only, not load-bearing) |
| Per-cycle state      | `data/judge_state.json` | high (file-level lock) |

If it's not in the env-var-override list, the test
isolation is incomplete.

### 6. Import-time assert that the env-var override actually took effect

After setting `SRI_DB_PATH` etc. and importing `db` and
`branch`, the test should assert the constants point at the
temp dir:

```python
import db
import branch

assert str(db.DB_PATH).startswith("/tmp/"), \
    f"DB_PATH not redirected! Got: {db.DB_PATH}"
assert str(branch.BRANCHES_DIR).startswith("/tmp/"), \
    f"BRANCHES_DIR not redirected! Got: {branch.BRANCHES_DIR}"
```

This converts a silent test-pollution bug into a hard
crash. Without the assert, an accidental reordering of
`os.environ` and `import` statements (or a future refactor
that captures the constant at import time in a way the
env-var override doesn't cover) would silently start
writing to prod again. The assert is what makes the
fix durable across future edits.

The assert costs nothing at runtime and runs in <1ms.
The diagnostic it produces is the difference between
"tests pass" and "tests pass AND we know they're testing
the right thing."

## The diagnostic that catches this whole class

After every test run:

```bash
sqlite3 data/loop.db \
  "SELECT COUNT(*) FROM proposals WHERE source_session_id IS NULL AND evidence = 't11'"
```

Zero is the answer. Non-zero means the test is leaking. The
`source_session_id IS NULL AND evidence = 't11'` is the
specific signature for this test suite; for other test
suites, use whatever marker string the test fixtures use
(e.g. `rationale LIKE 'test_%'` or `target_path LIKE '/tmp/%'`).

The cleanup query (FK OFF, because `judge_verdicts` references
`proposals`):

```sql
PRAGMA foreign_keys = OFF;
DELETE FROM judge_verdicts WHERE proposal_id IN
  (SELECT id FROM proposals WHERE source_session_id IS NULL AND evidence = 't11');
DELETE FROM proposals WHERE source_session_id IS NULL AND evidence = 't11';
PRAGMA foreign_keys = ON;
```

For the 2026-06-07 session this removed 18 verdicts + 18
dummy proposals. Prod state returned to:
- 31 merged (real changes)
- 1 rejected (the legitimate reject from earlier this morning)
- 0 pending dummies

## General rule

A test suite for a self-modifying system is part of the trust
boundary, not outside it. If the test can write to the prod
store, a passing test is a write-vulnerability disguised as
a safety net.

The env-var-overridable-path pattern (sections 1-3 above) is
the worked fix. Apply it to any system where tests and prod
share a database, a config file, or a skill directory.

## Verification

After applying the fix, re-run the test suite. Then:

```bash
# 1. Tests pass against the temp DB
PYTHONPATH=src python3 tests/test_branch_full.py
# → 47/47 green

# 2. Prod DB unchanged
sqlite3 data/loop.db \
  "SELECT COUNT(*) FROM proposals WHERE source_session_id IS NULL"
# → 0

# 3. No junk branch dirs created
ls data/branches/ | wc -l
# → unchanged from before the test run
```

All three were confirmed working on 2026-06-07. Note that
test 9 itself still had a downstream `_apply_unified_diff`
edge case (the test 9 proposal's `<<<...===...>>>` diff
format hit a silent rejection in apply_proposal that needed
a separate trace) — that's a different bug, in `apply.py`
rather than test isolation, and was caught because the test
isolation fix made test 9's failure visible. **The test
isolation fix doesn't just stop pollution; it makes the
test suite's pass/fail signal actually trustworthy.**
