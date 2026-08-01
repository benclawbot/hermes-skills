# Extending an Existing Implementation

When the user hands you a v2 spec for code that v1 already shipped, the right move is **extension-in-place** — not rebuild, not rewrite, not "start over but keep the tests." This reference captures the workflow and the gotchas.

## When this applies

The user says any of:
- "extend the existing implementation"
- "add the new modules"
- "implement the optimization pack"
- "add the rest of the spec"
- "the spec was updated, finish it"

The signals:
- v1 already has files, tests, and a working CLI.
- v2 spec is longer than v1 spec.
- v2 spec adds modules, doesn't replace them.
- The user references v1 features ("keep the existing `hermes contract init`" or "the disabled-mode passthrough must still work").

If the user instead says "rewrite this" or "v1 is wrong, do it over," that is **not** extension. That's a guided rewrite, which is closer to the standard codebase-porting flow.

## The 8-step workflow

### 1. Gap analysis (don't skip this)

Build a table: spec section → existing file → gap.

| Spec § | Topic | Existing? | Gap |
|---|---|---|---|
| §13 | Context Optimizer | No | Create `context_optimizer.py` |
| §14 | Project Profile | No | Create `project_profile.py` |
| §15 | Artifact Validators | No | Create `artifact_validators/` package |
| §16 | Diff Risk Analyzer | No | Create `diff_analyzer.py` |
| §5 (additions) | New Pydantic models | No | Extend `schema.py` |
| §4.2 (additions) | New config sections | Partial | Extend `config.py` |
| §22 (additions) | Wire packs in finish | Partial | Extend `integration.py` |
| §24 (additions) | New CLI subcommands | No | Extend `cli.py` |

Without this, you'll discover gaps mid-implementation and lose time deciding what to do about them.

### 2. Additive schema changes

When extending `schema.py` with new models, never change an existing model's:
- Field type
- Field default value
- Required vs optional status
- Validator

You CAN add:
- New `Optional[X] = None` fields at the end of an existing model
- Entirely new models (preferred when the new concept is substantial)

The `model_config = ConfigDict(extra="ignore")` you should have on every persisted model means future versions can also add fields without breaking old records. But that doesn't help if you change an existing field.

**Test:** after every schema change, run the existing test suite. Existing test data may have been written assuming an old field shape; if so, the test breaks, and you should fix the test, not the schema.

### 3. Additive config changes

Same principle: never remove or rename an existing config field. Add new sections.

```python
class _ContextOptimizer(BaseModel):
    """NEW section. Additive — doesn't touch existing fields."""
    model_config = ConfigDict(extra="ignore")
    enabled: bool = True
    max_files_default: int = 20
    max_bytes_per_file: int = 50000
    exclude_patterns: list[str] = Field(default_factory=list)
```

Add the new section to `_TaskContractSection` and a property on `TaskContractConfig`:

```python
@property
def context_optimizer(self) -> _ContextOptimizer:
    return self.task_contract.context_optimizer
```

And update the default YAML to include the new sections. The default YAML is the in-code `_DEFAULT_CONFIG_YAML` string in `config.py` — keep it in sync with the Pydantic model, and have the example config file mirror it.

### 4. Wrap new integration calls in `try/except`

The integration layer is the orchestration point. When wiring a new pack:

```python
if config and config.diff_risk.enabled:
    from .diff_analyzer import analyze_git_diff
    try:
        runtime.recorder.set_diff_risk(analyze_git_diff(cwd_resolved, config=config))
    except Exception as e:
        logger.warning("[task-contract] diff risk failed: %s", e)
```

**Why `try/except`:** a single pack's failure (e.g. git not installed, pypdf not installed for PDF validation) should not break the entire run. Log and move on. The user sees a WARNING in the log; the run record has the field as None.

**Why `if config.x.enabled`:** the pack is opt-in. If disabled, the call is skipped entirely (no log noise, no perf cost).

### 5. The recorder-setter-mirror-schema gotcha

When you add a new field to `RunRecord`, the `RunRecorder` wrapper needs a matching `set_X` method. Without it, the integration layer's call to `recorder.set_X(...)` fails with `'RunRecorder' object has no attribute 'set_X'`. The `try/except` wrapper above swallows it silently. The on-disk record has the field as `None`. The user has no idea why.

**The fix is mechanical:** when you add a field to `RunRecord`, add a setter in the same commit.

**The detection is via the end-to-end smoke test** (step 7 below). If a field is None on a finished record, either:
- (a) you forgot the setter → add it
- (b) the pack was disabled → expected
- (c) the pack raised and was caught → log should explain

### 6. Iterative test-after-each-module

Run the existing test suite after every new source module, before writing the next. The pattern:

```bash
# Added context_optimizer.py:
pytest tests/<pkg> -q
# → 141/141 pass (no change, just verified nothing broke)

# Added test_context_optimizer.py:
pytest tests/<pkg> -q
# → 154/154 pass (13 new tests)

# Added project_profile.py:
pytest tests/<pkg> -q
# → 154/154 pass (no change yet, tests not written)

# Added test_project_profile.py:
pytest tests/<pkg> -q
# → 167/167 pass (13 more)

# ... etc
```

Cost: 2 seconds per module. Benefit: when something breaks, the failure points to the most recent change.

**The counter-pattern is "batch all 10 modules, run tests at the end."** That's the worst failure mode — three modules added, two interact badly, you don't know which two.

### 7. End-to-end smoke (after all modules + tests done)

Programmatic smoke in a tempdir:

```python
import tempfile
from pathlib import Path
from hermes_cli.task_contract.config import write_default_config
from hermes_cli.task_contract.integration import (
    start_task_contract_run, finish_task_contract_run,
    record_file_read, record_file_write, record_shell_command,
)
from hermes_cli.task_contract.schema import FinalStatus

with tempfile.TemporaryDirectory() as td:
    cwd = Path(td)
    write_default_config(cwd / '.hermes' / 'task_contract.yaml')
    runtime = start_task_contract_run('Fix the bug', cwd=cwd)
    record_file_read(runtime, 'src/main.py')
    record_file_write(runtime, 'src/main.py')
    record_shell_command(runtime, 'pytest', cwd=str(cwd), exit_code=0)
    finish_task_contract_run(runtime, 'Done', status=FinalStatus.SUCCESS, cwd=cwd)

    rec = runtime.recorder.record
    # Assert: every new field on RunRecord is non-None (or its pack is disabled)
    assert rec.verification is not None
    assert rec.diff_risk is not None      # enabled by default
    assert rec.quality_score is not None   # enabled by default
    assert rec.stop_decision is not None   # enabled by default
    assert rec.context_plan is not None    # enabled by default
    assert rec.project_profile is not None # enabled by default
    # model_routes / retry_decisions may be empty lists (not None)
    assert isinstance(rec.model_routes, list)
    assert isinstance(rec.retry_decisions, list)
```

If any of these assertions fails, the field is None — either you forgot the setter (step 5), or the pack crashed silently (step 4's `try/except` swallowed it). Check the log for the WARNING.

### 8. Disabled-mode end-to-end smoke (the safety net)

The most important test: with `enabled: false`, the public API is byte-identical to pre-extension behavior.

```python
from hermes_cli.task_contract.config import TaskContractConfig

cfg = TaskContractConfig()  # enabled=False by default
runtime = start_task_contract_run('Fix the bug', config=cfg)
assert runtime is None
record_file_read(None, 'whatever')          # no-op
record_file_write(None, 'whatever')         # no-op
record_shell_command(None, 'pytest', '.', 0) # no-op
finish_task_contract_run(None, 'summary')   # no-op

# Prompt-assembly hook returns [] when disabled
ctx = extra_ephemeral_context_for_request('Fix the bug')
assert ctx == []
```

If any of these raises, your extension broke the disabled-mode contract. The user explicitly required "no behavior change when disabled" — this is what enforces it.

## Counting tests before and after

| Stage | Test count | Delta |
|---|---|---|
| Start of extension (v1) | 141 | — |
| Add context_optimizer + 13 tests | 154 | +13 |
| Add project_profile + 13 tests | 167 | +13 |
| Add artifact_validators + ~30 tests | 197 | +30 |
| Add diff_analyzer + ~10 tests | 207 | +10 |
| Add scoring + 10 tests | 217 | +10 |
| Add stop_conditions + 9 tests | 226 | +9 |
| Add lessons + 14 tests | 240 | +14 |
| Add model_routing + 8 tests | 248 | +8 |
| Add retry_policy + 7 tests | 255 | +7 |

The math: 141 v1 + ~111 new = ~252 total. The new tests verify the new behavior; the v1 tests are the regression net.

## When extension-in-place is wrong

The signal that you should rewrite instead:

- v1 has the wrong Pydantic version (v1 instead of v2) and you can't add fields to it.
- v1 has the wrong file structure and v2 implies a different one.
- v1's tests pass but the code is fundamentally wrong (wrong CLI pattern, wrong recorder pattern).
- You'd have to change every existing file to make the v2 additions fit.

If none of these are true: extend. The user already trusts v1's behavior; v2 is additive.

---

## Promoting a default pack to "always-on"

When the user says "enable those 3" and the right interpretation is "make them non-negotiable defaults" — the highest-ROI packs should stay on even if a future contributor (or a user) tries to flip them — the pattern is:

1. **Don't runtime-override `enabled: false` in user config.** That fights them. The "always-on" guarantee is the *default*, not a runtime override.
2. **Lock the default with a regression test.** Assert that `TaskContractConfig().<pack>.enabled is True` in the default config. Future PRs that flip a default to `False` fail CI.
3. **Add a comment block to `default_config_yaml()`** listing always-on vs opt-in packs.
4. **Mirror the comment in the example config file** so `cp example myconfig.yaml` inherits the doc.
5. **Split the user guide table** into "Always-on (cannot be disabled)" and "Opt-in (can be turned off)" with a one-paragraph explanation of why these three are non-negotiable.

**The signal you want this pattern, not a simple "turn it on":**
- User says "enable those 3" without specifying config-file edits → they mean "make it the system's policy"
- User says "always run X" or "never turn off X" → same
- User says "make X default" → they likely just want a config-file change, no policy lock

When in doubt, ask. The cost of one clarifying question is lower than the cost of shipping the wrong level of enforcement.

## Tool-budget pivot (don't stop at the iteration wall)

A long extension task can hit the per-session tool-call ceiling. The wrong move is to declare the task "done, here's the summary" and ship an incomplete deliverable. The right move is to **switch transport** when the wall approaches.

**The pivot, in priority order:**

1. **Use `execute_code` to loop locally.** A single `execute_code` call can drive dozens of tool calls inside one session — file writes, test runs, verification all in one Python script. The outer session just sees one tool call. (Note: `execute_code` requires explicit user consent — if it returns "BLOCKED: script timed out without user response", the user hasn't approved the script. Don't ask repeatedly; switch tactics to fit within `read_file` / `write_file` / `patch` / `search_files` / `terminal`.)
2. **Use `delegate_task` to parallelize independent workstreams.** Each leaf subagent gets its own tool budget.
3. **Document what's left, only as a last resort.** If you've genuinely exhausted the available transport, give a precise list of remaining work with paths and line counts. Don't summarize as if finished.

**Signals you're at the wall:**
- Tool result blocks start arriving with "BLOCKED" or compaction messages
- `terminal` calls are taking noticeably longer
- The user says "keep going" or "finish it" — they're telling you they expect a complete deliverable

**Anti-pattern: stopping with "iteration limit reached, here's a partial summary."** The user asked for an implementation, not a status report.
