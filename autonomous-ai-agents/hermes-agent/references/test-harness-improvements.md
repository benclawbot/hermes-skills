# Test Harness Improvements — Ranked by Impact

## 1. Parallel Test Execution (pytest-xdist)
**Impact: 3–8x on multi-core**

Already in hermes-agent: `pytest -n auto` in addopts. xdist distributes tests across CPU cores.

```toml
# pyproject.toml [dev] deps already has:
pytest-xdist==3.8.0

# addopts:
addopts = "-m 'not integration' -n auto"
```

## 2. testmon — Change-Driven Test Selection
**Impact: 70–90% CI reduction on subsequent runs (small PRs)**

Only runs tests whose dependent source files changed since last run. First run builds baseline; subsequent runs on same PR skip unaffected tests.

```toml
# Already added to [dev] deps:
pytest-testmon==2.1.0
```

```bash
# First run (baseline):
pytest tests/ --ignore=tests/integration --ignore=tests/e2e -n auto -W ignore::pytest.TestmonWarning
# → .testmon.json created

# Second run (same PR, 5 files changed):
# testmon auto-skips tests whose deps haven't changed
```

CI integration (GitHub Actions):
```yaml
- name: Download test history
  uses: actions/download-artifact@v4
  with:
    name: .testmon.json
  continue-on-error: true

- name: Run tests
  run: pytest tests/ ... -W ignore::pytest.TestmonWarning

- name: Upload test history
  uses: actions/upload-artifact@v4
  with:
    name: .testmon.json
    path: .testmon.json
    retention-days: 7
```

**Not safe for real-time use** — shared artifact means state can be stale across PRs.

## 3. CI Sharding with pytest-split
**Impact: ~4x (4-way split)**

Split suite across N parallel CI runners. hermes-agent now uses 4-way split with duration-based algorithm.

```toml
# Already in [dev] deps:
pytest-split==0.11.0
```

```yaml
# .github/workflows/tests.yml — 4 parallel jobs
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - run: pytest tests/ --splits=4 --group=${{ matrix.shard }} --splitting-algorithm=least_duration
```

`least_duration` algorithm: pytest-split uses historical durations to balance shards so all finish at the same time (fastest shard doesn't wait for slowest).

## 4. --durations=10
**Impact: Visibility into slow tests (no speed gain, but surfaces optimization targets)**

Added to `addopts`. Shows top-10 slowest tests after each run:

```
Slowest durations (10/106 tests):
  0.42s     test_hermes_state_wal_fallback
  0.31s     test_cron_scheduler
  0.28s     test_skill_loading
  ...
```

## 5. pytest-benchmark
**Impact: Quantify performance of specific code paths**

In `[dev]` deps. Use for performance-sensitive operations (WAL, trajectory compression, skill parsing).

```python
def test_wal_write_performance(benchmark):
    result = benchmark(wal.write, entries)
    assert result is not None
```

Run: `pytest --benchmark-only`

## 6. AWS IMDS Disable (Already Done)
**Impact: ~2s per test that calls has_aws_credentials() or resolve_aws_auth_env_var()**

Already in conftest:
```python
monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
monkeypatch.setenv("AWS_METADATA_SERVICE_TIMEOUT", "1")
monkeypatch.setenv("AWS_METADATA_SERVICE_NUM_ATTEMPTS", "1")
```

## 7. Module-Level State Reset (Already Done)
**Impact: Eliminates "passes alone, fails in CI" flakes**

Already in conftest's `_reset_module_state()`. Clears: approval state, interrupt flags, session_context ContextVars, terminal_tool environments, credential_files ContextVars, auxiliary_client runtime, file_tools read tracker.

## Common Pitfalls
- **testmon + xdist**: testmon tracks dependencies per-test; with `-n auto` (parallel workers), ensure `--dist loadscope` is set so tests within same module class run together (reduces dependency tracking noise)
- **pytest-split first-run**: `least_duration` needs historical data — first run is round-robin; subsequent runs are balanced
- **testmon on main branch**: On main branch (no prior artifact), testmon runs full suite — expected behavior
- **Artifact naming**: testmon artifact must be named exactly `.testmon.json` (no path prefix) for download-artifact to find it

## Key Commands

```bash
# Local: run with testmon, see durations
pytest tests/ -n auto --durations=10 -W ignore::pytest.TestmonWarning

# Local: run specific shard
pytest tests/ --splits=4 --group=1 --ignore=tests/integration --ignore=tests/e2e

# Force full run (no testmon):
pytest tests/ --ignore=tests/integration --ignore=tests/e2e -n auto --tmux-disable

# Benchmark a specific test
pytest tests/test_hermes_state_wal_fallback.py --benchmark-only
```