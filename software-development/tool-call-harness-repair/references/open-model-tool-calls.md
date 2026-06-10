# Open-model tool-call failure catalogue

Source: Ahmad Awais (@MrAhmadAwais), X post `2050956678502420612` (June 2026).
"how did we make deepseek outperform opus 4.7?" — two days of analysis on
billions of tokens in @CommandCodeAI (open-source AI CLI).

The four failure modes and the validate-then-repair pattern are reproduced
here verbatim for use as a reference when designing or debugging a
JSON-schema tool harness. The umbrella SKILL.md carries the design
lessons; this file is the raw catalogue and the worked example.

---

## The four failure modes

Across DeepSeek-flash, DeepSeek V4 Pro, GLM, Qwen, the same four mistakes
repeat almost exactly:

### 1. `null` for optional field

Model emits `{"tag": null}` where the schema means "omit if absent".
The model has learned `null` as a generic "absent" marker; the schema
treats it as a present-but-empty value. Tools then validate against
`None` and fail because the type doesn't match.

**Repair**: strip `None` from the args dict when the field is not
required and the schema doesn't explicitly allow null.

### 2. JSON string instead of native array

Model emits `{"items": "[\"a\",\"b\"]"}` where the schema wants
`{"items": ["a","b"]}`. This happens most often on complex oneOf or
discriminated-union schemas where the model loses track of which
"shape" of argument it was trying to emit.

**Repair**: try `json.loads` on string values for array/object-typed
fields. If it parses to the right Python type, use it. **Run before**
mode #4 or the wrap-singleton path will turn `'["a","b"]'` into
`['["a","b"]']`.

### 3. Empty-dict placeholder for array

Model emits `{"items": {}}` where the schema wants a list. The empty
object is a degenerate "placeholder" pattern; downstream tools don't
expect `[{}]` and break on iteration.

**Repair**: substitute `[]` when the value is literally `{}` on an
array-typed field. Only check `value == {}` — non-empty dicts are
intentional single-element arrays and should be wrapped as
`[{"a": 1}]` (mode #4 behavior).

### 4. Bare scalar for array field

Model emits `{"urls": "https://a.com"}` where the schema wants
`{"urls": ["https://a.com"]}`. The model remembered the *content* but
not the container.

**Repair**: wrap in a single-element list. Apply AFTER modes #2 and
#3 (otherwise you double-wrap parsed JSON, or wrap a `{}` placeholder
that should have been `[]`).

---

## Ordered repair chain

The order matters. From the post:

> four repairs, ~30–100 lines each, ordered carefully
> (json-array-parse must run before bare-string-wrap or
> `'["a","b"]'` becomes `['["a","b"]']`).

The full chain as implemented in `model_tools.coerce_tool_args`:

```
1. strip_null_for_optional(value, field_schema, required_set)
2. empty_dict_to_list(value, field_schema)        # only if value == {}
3. parse_json_string(value, field_schema)         # if string and schema is array/object
4. wrap_singleton(value, field_schema)            # only if value is not None and not list
```

Each repair returns the transformed value; if a repair doesn't apply
it returns the original and the next one tries.

---

## The validate-then-repair pattern (worked example)

```python
def dispatch(tool_name: str, args: dict) -> str:
    # 1. Try the strict path first — fast for well-formed calls.
    try:
        validated = tool_schema(tool_name).validate(args)
        return invoke(tool_name, validated)
    except ValidationError as first_error:
        pass

    # 2. Walk the validator's issue list. Each issue points to a
    #    specific field path; only spend repair budget there.
    repaired = dict(args)
    for issue in first_error.issues:
        field = issue.path
        if field not in repaired:
            continue
        for repair in REPAIR_CHAIN:
            new_value = repair(repaired[field], issue, tool_schema(tool_name), field)
            if new_value is not repaired[field]:
                log.info("tool_input_repaired", tool=tool_name, field=field, repair=repair.__name__)
                repaired[field] = new_value
                break

    # 3. Re-validate. If it still fails, surface a model-readable error.
    try:
        validated = tool_schema(tool_name).validate(repaired)
        return invoke(tool_name, validated)
    except ValidationError as e:
        log.warning("tool_input_invalid", tool=tool_name, args=repaired, errors=str(e))
        return model_readable_retry_message(repaired, e)
```

The key insight:

> When you preprocess, you encode a prior about what's broken.
> When you let the validator complain first, the schema is the prior,
> and you only spend repair budget at the exact paths the schema
> actually disagreed at.

This gives you per-tool telemetry for free. Watch repair rates per
`(model, tool)` and notice when a model regresses on a specific
contract before users do.

---

## The funny case (mode #5, deferred)

DeepSeek-flash, when asked to edit or write a file, sometimes emits
the path as a markdown auto-link:

```
filePath: "/Users/x/proj/[notes.md](http://notes.md)"
```

The writeFile tool obediently creates a file literally named
`[notes.md](http://notes.md)`. This is not a hallucination — it's
post-training chat distribution leaking through the tool boundary. The
model has been rewarded for auto-linking in conversational output
and is applying that prior in a context where it makes no sense.

**Don't fix this in the generic repair layer.** Fix it in the schema:

```python
def path_string():
    return z.string().refine(
        lambda p: not re.search(r"\[.+\]\(http", p),
        "path contains a markdown auto-link — emit the raw path, "
        "not a chat-distribution artifact",
    )
```

This is mode #5, but it's narrow enough to a path field that the
right fix is `pathString()` in the file tools schemas, not a 5th
generic repair.

---

## Relational invariants (mode #6, don't repair)

`read_file` had a *relational* invariant: "if you provide `offset`,
you must also provide `limit`, and vice versa." DeepSeek kept calling
`readFile({ absolutePath, limit: 30 })` and getting an error back.

You can't fix this with input repair — each field is independently
valid. The bug is in the relationship. So teach the function the
model's intent instead:

```python
def read_file(absolutePath, offset=None, limit=None):
    if offset is not None and limit is None:
        offset, limit = 0, offset
    if limit is not None and offset is None:
        offset, limit = 0, limit  # offset=0, limit=2000 default
    elif limit is None and offset is None:
        offset, limit = 0, 2000  # both default
    result = _read(absolutePath, offset, limit)
    if defaulted:
        result["note"] = (
            f"limit was not provided; defaulted to {limit} lines. "
            f"To override, retry with both offset and limit."
        )
    return result
```

No `Error:` prefix — the model sees what was picked and self-corrects.

> Repair where you can. Extend semantics where you can't. Surface the
> choice either way.

---

## Where this lives in Hermes

- `model_tools.coerce_tool_args` — implements modes #1, #3, #4
- `model_tools._coerce_value` — implements mode #2 (JSON parse for
  array/object types)
- `model_tools.handle_function_call` — calls `coerce_tool_args` first,
  then dispatches
- `tests/run_agent/test_tool_arg_coercion.py` — 72 tests covering all
  four modes + edge cases (nullable, required, union types)

Result: a 6/10 win rate on the internal eval Ahmad ran. The model
didn't change. The contract got more forgiving in exactly the places
it needed to be.
