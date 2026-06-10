# Mode #19 — list-of-dicts when schema wants list-of-strings

**Where:** the boundary between `coerce_tool_args` and the tool's own
validation. The element-level inverse of mode #3 (which is the
*field-level* "empty dict for array" case).

**Repro:**

```python
# Tool schema declares: {"choices": {"type": "array", "items": {"type": "string"}}}
# Model emits: choices=[{"value": "Option A"}, {"value": "Option B"}]
# Tool code does:  choices = [str(c).strip() for c in choices if str(c).strip()]
# Result: choices = ["{'value': 'Option A'}", "{'value': 'Option B'}"]
# Then rendered in the message body as a numbered list of literal dicts.
```

**Why it bites:** the schema validation passed (most JSON-schema
validators don't enforce element types inside an array) and the
tool's `str(c)` fallback produced a *valid Python string* — so no
error was raised. The bug is silent at runtime and only surfaces in
the rendered UI: the user sees a numbered list of
`{'value': 'Option A'}` literals instead of the actual options.

Real incident (June 2026, `clarify` tool on Telegram): the M3 model
emitted `choices=[{"value": "..."}]` against a `List[str]` schema. The
gateway's `render_clarify_prompt` in
`gateway/platforms/telegram.py:2801-2805` does `str(c)` on each
element when building the message body. The result was a question
with a numbered list of `1. {'value': 'Split into two jobs...'}`
entries — opaque to the user.

**Why it's not a strict type error:** the underlying JSON-schema
validators used in most agent harnesses accept the dicts because
they check "is this an array?" (yes) but don't recursively validate
element types against the `items` schema. The dict is JSON-valid
inside an array; it just doesn't match the declared element type.
The harness layer sees "valid JSON" and lets it through.

**Fixes — choose by where the trust is:**

1. **Strict element-type validation in `coerce_tool_args`** — if
   `schema.items.type == "string"` and an element is a dict, treat as
   invalid and either reject the call or attempt a dict-to-string
   coercion. The safe coercion is `c.get("value")` or
   `c.get("text")` or `str(c)` if those fail — same fallback as the
   model-facing tools use, but the schema *declared* `string` so the
   coercion is the harness's responsibility, not the tool's.
2. **Model-side correction via prompt engineering** — when the
   system prompt or tool description says "array of strings," the
   model *should* emit strings. If the model regularly gets this
   wrong, add a one-line example to the tool description: "Pass
   plain strings, e.g. `[\"Option A\", \"Option B\"]`, NOT
   `[{value: \"Option A\"}]`."
3. **Tool-side `c.get("value", str(c))` — defensive, but loses
   schema rigor.** The tool author shouldn't have to know that the
   model might emit dicts. This is a fallback if (1) and (2) can't
   ship fast.

**Tier:** 2 (data loss without telemetry). The session doesn't crash
— the question is delivered, the user can still type a free-form
answer, and the dicts are obvious enough in the message body that
the user will report it. The risk is silent: a long-running
deployed agent that uses `clarify` for production prompts would
generate useless option lists without anyone noticing until user
complaints roll in.

**Test count:** 3 (dict with `value` key, dict with `text` key, dict
with arbitrary key — last one falls through to `str(c)` and is the
silent-failure case).

## Related skill note: `one-question-at-a-time`

This mode is most likely to surface when the tool is `clarify` (the
Telegram decision-prompt tool). When you use `clarify` and want
inline-keyboard buttons to render, **always pass plain strings** in
`choices`, never `[{value: '...'}]`. The buttons do not render in
many Telegram contexts regardless, but if you do this in addition,
you can guarantee the message body at least is readable.

## Companion mode — same family, different direction

- **Mode #3** — field-level: model emits `{"items": {}}` where schema
  wants a list. Caught at field parse.
- **Mode #19** — element-level: model emits a list of dicts where the
  list's element type is declared `string`. Caught at element parse.

Both are "model uses the wrong shape for the declared type" and the
fix family is the same: either strict validation in the harness, or
a one-line example in the tool's prompt that shows the correct
shape. Mode #19 is the one that's *silent at runtime* — mode #3
usually crashes when the tool tries to iterate.
