# Spec Implementation Playbook

Detailed workflow and lessons learned for implementing a build-ready external specification into an existing real codebase. Companion to the main `codebase-porting` SKILL.md.

## When to use this reference

Use when the user hands you a build-ready spec document — numbered build steps, schemas, exact file paths, acceptance criteria — and says "implement that", "build this", or "execute this plan". Examples in this repo: the Task Contract Layer spec (`Hermes Task Contract Layer Specification.docx`), a porting spec, a plugin integration spec.

## The 7-phase workflow

### Phase 1: Read the spec end-to-end ONCE

Don't start coding mid-read. Read the whole spec. Note:
- Every literal file path mentioned
- Every schema (Pydantic model, interface, etc.)
- Every public function with its exact signature
- The numbered build order
- The acceptance checklist at the end (this is your final test)

Use `read_file` with the docx/PDF or whatever the spec lives in. If it's a .docx, unzip and parse `word/document.xml` (one-liner: `python3 -c "import xml.etree.ElementTree as ET; ..."`).

### Phase 2: Build the spec-vs-reality delta table

For each literal path in the spec, determine reality. This is the most important artifact you'll produce:

| Spec says | Reality | Action |
|---|---|---|
| `hermes/task_contract/` (new dir) | `hermes` is a tracked launcher FILE | Pick sibling: `hermes_cli/task_contract/`. Log the deviation. |
| `agent/prompt_builder.py` (modify) | Exists, has `_build_system_prompt` | Read first; check for clean hook point |
| `tests/task_contract/test_schema.py` (new) | Doesn't exist | Safe to create |
| `examples/task_contract/.hermes/task_contract.yaml` (new) | Doesn't exist | Safe to create |

**Run this pre-check on every path:**

```bash
# Does the path exist as a file?
stat <spec_path> 2>&1 | head -3

# Is it tracked in git?
git ls-files <spec_path>

# Sibling name conflicts?
ls -la $(dirname <spec_path>) | head
```

**The `mkdir` collision trap.** If a spec says `mkdir hermes/task_contract` and `hermes` is a tracked file in git, what happens depends on the shell:
- `mkdir -p hermes/task_contract` in bash → may succeed by creating the parent as a directory (silently clobbering the file)
- `mkdir hermes/task_contract` (without -p) → fails with "Not a directory"

**Only the explicit pre-check is reliable.** Run it for every new directory the spec creates. If a collision exists, the right answer is almost never "delete the existing file" — it's "pick a non-colliding location and document the deviation."

### Phase 3: Identify integration points

Before writing a single line, read the existing code at every integration point the spec mentions. For each one, capture the answer to "where does the new code hook into existing code?":

- **CLI registration**: where subcommands are wired (e.g. `hermes_cli/main.py` — look for `subparsers.add_parser` calls)
- **Config loading**: what style (YAML, TOML, pydantic), where paths resolve from (`get_hermes_home()`)
- **Schema conventions**: Pydantic v1 vs v2 (`ConfigDict` vs `Config`), dataclass, TypedDict
- **Test framework**: pytest with `tmp_path`, hermetic conftest.py
- **Prompt assembly**: where the system prompt is built, whether there's a clean hook for `extra_ephemeral_context` injection
- **Tool/file/command execution wrappers**: any existing `governed_*` context managers, audit trails, etc.

Read 1-2 representative files at each integration point. Skim more if the codebase is large.

### Phase 4: Follow the spec's numbered build order

Build-ready specs almost always include a numbered build order section. Follow it literally. The order is designed so each step depends only on previous steps.

When a step says "implement these schemas", implement them. When a step says "run schema tests", write those tests first, watch them fail, then implement. (Optional TDD: the spec may not require it, but it's faster than implementing then testing.)

### Phase 5: Deviations are part of the deliverable

When reality forces a deviation from the spec (e.g. the path collision above), do all of:

1. **Log the deviation in the package's `__init__.py`** as a one-paragraph note in the module docstring. This is the first file any future reader opens.
2. **Log it in the developer guide** under "Implementation notes" or "Known deviations".
3. **Reference both from the PR description** (if there is a PR).

Future readers will find the deviation within 30 seconds of opening the package. If they don't, they'll waste time wondering why the path doesn't match the spec.

### Phase 6: Acceptance-checklist driven validation

Build-ready specs end with an acceptance checklist. Each item is a testable claim. Run every item, in order, and record the result. The acceptance check is the source of truth for "done."

```bash
# Example from one session — every item must PASS
[OK] hermes_cli/task_contract/ package exists.                  # 11 modules
[OK] Config file can be generated with `hermes contract init`.  # verified
[OK] Config loading works with project/global/default precedence.  # test_config: 4 tests
[OK] Task classification works deterministically.               # test_classifier: 9 tests
...
```

Don't ship until every box is checked. If a box can't be checked, that's a bug to fix, not a "best effort" item.

### Phase 7: Run the existing test suite

A new package that breaks unrelated tests has not shipped. Run at least a representative subset of unrelated test files:

```bash
# Sanity: pick 2-3 unrelated test files and run them
python3 -m pytest tests/test_atomic_replace_symlinks.py tests/test_bitwarden_secrets.py -q
```

If any of them fails, the new code is touching something it shouldn't.

## Architectural patterns from this class of work

### Pattern 1: Disabled-mode-is-noop

For any optional subsystem, the public API must work identically whether the subsystem is enabled or disabled. This is the spec's "no behavior change when disabled" acceptance item.

```python
def public_function(runtime=None, **kwargs):
    if runtime is None or not runtime.enabled:
        return  # no-op
    # ... normal logic
```

This means:
- Every public function takes a runtime handle (or None)
- Every public function checks the handle first
- `start_*` returns None when disabled (not a "disabled runtime" — literally None)
- The CLI/UI surface doesn't need to know whether the subsystem is on

Why this matters: integration code can sprinkle `record_*` calls without conditionals, and they become inert when the user opts out. No `if enabled:` checks at the call site.

### Pattern 2: Pydantic v2 records with ConfigDict(extra="ignore")

For persisted records, use Pydantic v2 BaseModel with `model_config = ConfigDict(extra="ignore")`:

```python
class RunRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    run_id: str
    # ... required fields
    optional_field: list[X] = Field(default_factory=list)
```

`extra="ignore"` is critical for forward-compatibility: if a future version adds a field, old records still load. If you used `extra="forbid"`, a single old record would crash the new code.

For required numeric fields with non-negative semantics, add a validator:

```python
@field_validator("*")
@classmethod
def _non_negative(cls, v: int) -> int:
    if v < 0:
        raise ValueError("budget values must be >= 0")
    return v
```

### Pattern 3: BudgetManager raises BEFORE exceeding the limit

For any "limit N, then no more" enforcement, raise on the N+1th attempt, not the Nth. The semantic: "this would push us past the cap" is a different error than "we're already over."

```python
def _check_and_increment(self, kind: str) -> None:
    current = getattr(self.state, counter_attr)
    maximum = getattr(self.budget, max_attr)
    if current >= maximum:
        # DO NOT increment; raise before exceeding
        raise BudgetExceededError(kind, current, maximum)
    setattr(self.state, counter_attr, current + 1)
```

With `max=2`:
- 1st call: current=0, allowed, becomes 1
- 2nd call: current=1, allowed, becomes 2
- 3rd call: current=2, REJECTED. We never reach 3.

### Pattern 4: CLI subcommand dispatcher accepts both Namespace and argv

When wiring a subcommand into a parent CLI that uses argparse subparsers, the parent will pass a parsed `Namespace` to your handler. But for standalone use (e.g. `python -m mymodule.cli <args>`), the handler needs to accept raw argv. Build the handler to handle both:

```python
def contract_cmd(args=None) -> int:
    if isinstance(args, list) or args is None:
        # Standalone: build parser, parse argv
        parser = build_parser()
        parsed = parser.parse_args(args)
        return int(parsed.func(parsed))
    # Called from parent CLI: route on namespace attribute
    sub = getattr(args, "contract_command", None)
    if sub == "init":
        return cmd_init(args)
    # ...
```

Why this matters: the same code can be tested standalone (`contract_cmd(["init"])`) AND invoked from the parent CLI (`contract_cmd(args_namespace)`) without separate dispatchers.

### Pattern 5: Context-manager tool-call wrapper

For governed tool calls (recording + budget + error capture), use a context manager that yields the in-flight record so callers can annotate it:

```python
@contextmanager
def governed_tool_call(runtime, name, purpose=None):
    record = ToolCallRecord(name=name, purpose=purpose, started_at=utcnow_iso())
    if runtime is None or not runtime.enabled:
        yield record  # inert
        return
    runtime.budget_manager.check_tool_call()  # may raise
    try:
        yield record
        if record.success is None:
            record.success = True
    except Exception as e:
        record.error = str(e)
        record.success = False
        raise
    finally:
        record.ended_at = utcnow_iso()
        runtime.recorder.record_tool_call(record)
```

The caller does:

```python
with governed_tool_call(runtime, "shell", "Run tests") as rec:
    result = subprocess.run(...)
    rec.success = (result.returncode == 0)
```

The wrapper handles start/end timestamps, success defaulting, error capture, and budget enforcement — none of which the caller has to remember.

### Pattern 6: Lessons generation from run record (no LLM)

Deterministic, rule-based lessons extraction is more useful than LLM-generated ones for v1. The rules are simple, the output is testable, and there's no latency:

```python
def _generate_lessons(record: RunRecord) -> List[str]:
    lessons = []
    if record.verification and not record.verification.passed:
        lessons.append("Verification failed; future similar tasks should run or explicitly skip required checks before finalizing.")
    if record.contract.mode == DOCS and not record.file_operations:
        lessons.append("Documentation tasks should inspect source/config files before making project capability claims.")
    # ... 2-3 more rules
    return lessons
```

Write them into the record, don't auto-inject into memory. Lesson injection is a v2 feature.

## Common mid-implementation bugs (and fixes)

These are bugs that cost real time in one session. The fixes are durable.

### Bug: Multi-word keyword needs word-boundary matching with intervening words

**Symptom:** "Generate a PDF" doesn't match the keyword "generate pdf" because of the intervening "a".

**Wrong fix:** strict substring `if "generate pdf" in text`.

**Right fix:** in-order token regex.

```python
def _contains_any(text: str, keywords: Set[str]) -> bool:
    for kw in keywords:
        if " " in kw or "-" in kw:
            tokens = [t for t in re.split(r"[\s-]+", kw) if t]
            pattern = r"\b" + r"\b.*?\b".join(re.escape(t) for t in tokens) + r"\b"
            if re.search(pattern, text):
                return True
        else:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True
    return False
```

`"generate a pdf"` → `["generate", "pdf"]` → pattern matches with `.*?` allowing "a" between them.

### Bug: Min-length filter silently drops short constraints

**Symptom:** `extract_constraints("Avoid SQL.")` returns `[]` instead of `["SQL"]`.

**Cause:** cleanup function has `if len(c) < 4: return None` — too aggressive for short keywords.

**Fix:** lower the min to 2 (or 1) for constraint-like artifacts. Validate the spec's example set: if the spec says "Avoid SQL" is a valid constraint, the min must accept "SQL".

### Bug: Test expects substring that doesn't fit the truncation

**Symptom:** markdown record truncates commands at 120 chars; test asserts `"echo " + "x" * 120` (125 chars) is in the output — fails.

**Fix:** match the test to the actual behavior. Either:
- Test the prefix that's actually present: `"echo " + "x" * 115` (= 120 chars total)
- Test the absence of over-length content: `"x" * 200 not in md`

Pick the latter when the truncation is a feature, not a bug.

### Bug: Parent-CLI dispatcher passes Namespace, not argv

**Symptom:** `argparse.Namespace object is not iterable` when running the wired subcommand.

**Cause:** the parent CLI's `args.func(args)` passes a parsed Namespace, but the dispatcher tries to feed it to `parser.parse_args`.

**Fix:** build the dispatcher to accept both shapes (Pattern 4 above).

### Bug: Missing `RunRecorder.set_X` method silently drops new fields

**Symptom:** integration layer logs `WARNING: [task-contract] diff risk failed: 'RunRecorder' object has no attribute 'set_diff_risk'`. The on-disk record has `diff_risk: null`. No exception is raised.

**Cause:** you added a new field to `RunRecord` (e.g. `diff_risk: Optional[DiffRisk] = None`) but forgot to add a `set_X` method to `RunRecorder`. The integration layer wraps the call in `try/except` (intentional, so pack failures don't break the run), which catches the `AttributeError` and logs it as a warning.

**Fix:** when you add a new field to `RunRecord`, add the matching `set_X` method in the same change. The end-to-end smoke test should assert that the field is non-None on a finished record. See `extending-existing-implementation.md` step 5 for the full pattern.

### Bug: New config section not in `_DEFAULT_CONFIG_YAML`

**Symptom:** the in-code default config has all 15 sections, but `hermes contract init` writes a config with only the original 6. Users running `init` get a config missing the new optimization packs.

**Cause:** `_DEFAULT_CONFIG_YAML` is a hardcoded string in `config.py` that must be kept in sync with the Pydantic model. When you add a new config section, you must also add the corresponding YAML block to the string.

**Fix:** after adding a new `_XxxSection` class, immediately add the matching YAML to `_DEFAULT_CONFIG_YAML`. Then update `examples/<pkg>/.hermes/<pkg>.yaml` to match. There is no automated check for this drift — the smoke test of `hermes contract init` is the manual guard.

## Acceptance run-through template

```bash
# 1. Run the new test suite
python3 -m pytest tests/<new_package> -q

# 2. Sanity-check unrelated tests
python3 -m pytest tests/<one_unrelated_file> tests/<another_unrelated_file> -q

# 3. CLI smoke test (disabled mode = no config)
hermes <subcommand> status           # should print "disabled"

# 4. CLI smoke test (enabled mode = default config)
mkdir /tmp/smoke && cd /tmp/smoke
hermes <subcommand> init --force
hermes <subcommand> status           # should print "enabled"
hermes <subcommand> list             # should print "No runs found"

# 5. End-to-end programmatic smoke (in a clean tempdir)
python3 -c "
import sys
sys.path.insert(0, '<repo_root>')
from hermes_cli.<pkg>.config import write_default_config
write_default_config('.hermes/<pkg>.yaml')
from hermes_cli.<pkg> import start_..., finish_..., record_..., FinalStatus
runtime = start_...('test request')
record_...(runtime, '/path', purpose='test')
finish_...(runtime, 'done', status=FinalStatus.SUCCESS)
from hermes_cli.<pkg>.recorder import find_run
rec = find_run('.hermes/runs', runtime.contract.run_id)
assert rec is not None
assert rec.final_status == FinalStatus.SUCCESS
print('OK: end-to-end pass')
"

# 6. Verify the validation script
bash scripts/validate_<pkg>.sh
```

When all 6 pass, the package is done. Don't ship without running the script.

## When to NOT use this playbook

- **Trivial single-file changes** that don't need a spec — just do them.
- **Vague requirements** ("make the agent more reliable") — go to `writing-plans` first to author a spec, then come back here.
- **The spec is wrong about the goal itself** (not just paths) — escalate to the user before implementing.
