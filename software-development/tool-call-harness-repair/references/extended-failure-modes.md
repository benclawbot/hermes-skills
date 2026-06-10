# Extended failure modes (modes #5–#17)

Audit passes from June 2026, four more trips through the same Hermes
`coerce_tool_args` + `_repair_tool_call_arguments` code path that the
original four-mode catalogue covered. Each pass adds a layer:

- **Pass 2 (modes #5–#8)** — outer-envelope and numeric-precision
  failures. Live in the raw-args repair layer (`_scrub_nonfinite_numbers`,
  array/envelope unwrap) and the numeric coercion path
  (`_coerce_number(integer_only=True)`).
- **Pass 3 (modes #9–#15)** — text-noise extraction and string-sentinel
  coercion. Live in a *new* pre-pass (`_extract_json_from_text`) and in
  the value-coercion paths (`_coerce_boolean`, the string-`"null"` branch
  in `coerce_tool_args`).
- **Pass 4 (modes #16–#17)** — concatenated payloads and trailing-garbage
  extraction. Live in two complementary helpers:
  `_split_concatenated_tool_call_arguments` (2+ complete top-level
  dicts, no delimiter) and `_extract_first_json_object` (first dict
  parses, trailing text is junk). Both use `json.JSONDecoder.raw_decode()`
  walking left-to-right — the same primitive the upstream Hermes PR
  #25346 / #36039 uses for the parallel-call case.

Each entry includes a minimal repro, the observed current behavior, the
fix, and the test count added.

The probe script that produced these results lives at
`scripts/probe_repair_layer.py`. Re-run it after any change to the
repair layer to confirm the audit stays closed.

For the open upstream PRs that informed Pass 4 (and the captcha-
resistant research sources that surfaced them) see
`references/upstream-prs-and-search.md`.

---

## Mode #5 — NaN / Infinity pass-through

**Where:** `_repair_tool_call_arguments`, pass-0 (`json.loads(strict=False)` + `json.dumps`).

**Repro:**

```python
raw = '{"score": NaN, "name": "x"}'
print(_repair_tool_call_arguments(raw, "t"))
# Before fix: {"score": NaN, "name": "x"}    ← wire form is invalid JSON
# After fix:  {"score": null, "name": "x"}   ← allow_nan=False-safe
```

**Why it bites:** Python's `json` module with `strict=False` accepts
`NaN` / `Infinity` / `-Infinity` as number tokens because they come
from JavaScript. The re-serialised form (`NaN` literal in the output
string) is rejected by strict-validating providers (Anthropic, most
OpenRouter routing) and even when accepted, the wire form is
ambiguous across parsers.

**Fix:** after parse, recursively replace non-finite floats with
`None`. Then re-serialise with `allow_nan=False` so a regression
fails loudly instead of silently re-introducing the bug.

**Test count:** 5 (top-level NaN, +Inf, -Inf, NaN nested in array, NaN
nested in object).

---

## Mode #6 — Top-level array wrapping

**Where:** `_repair_tool_call_arguments`, pass-0.

**Repro:**

```python
raw = '[{"path": "/tmp/foo", "content": "hello"}]'
print(_repair_tool_call_arguments(raw, "write_file"))
# Before fix: [{"path": "/tmp/foo", "content": "hello"}]  ← list, not dict
# After fix:  {"path": "/tmp/foo", "content": "hello"}    ← unwrapped
```

**Why it bites:** the model treats the args envelope as a generic
JSON container and sometimes emits an array. Tool dispatch assumes
`args` is a dict and crashes on the first `args["path"]` lookup.

**Fix:** if `parsed` is a list of length 1 whose only element is a
dict, unwrap to the dict. Do NOT unwrap multi-element arrays — those
represent parallel calls and dropping data silently is worse than the
original bug.

**Test count:** 3 (single-element unwrap, empty array passthrough,
multi-element array not unwrapped).

---

## Mode #7 — `result` envelope wrapping

**Where:** `_repair_tool_call_arguments`, pass-0.

**Repro:**

```python
raw = '{"result": {"path": "/tmp/x"}}'
print(_repair_tool_call_arguments(raw, "t"))
# Before fix: {"result": {"path": "/tmp/x"}}  ← dispatch sees "result" key it doesn't expect
# After fix:  {"path": "/tmp/x"}              ← unwrapped
```

**Why it bites:** the model has been trained on chain-of-thought
traces that wrap function-call responses in `{"result": ...}`. It
sometimes wraps its own tool-call args the same way.

**Fix:** strict rule — only unwrap when there is **exactly one key
named `result`** AND the value is a dict. Mixed envelopes
(`{"result": {...}, "status": "ok"}`) and non-dict values
(`{"result": 42}`) are real shapes the model intended and must be
preserved.

**Test count:** 3 (pure envelope unwrap, mixed envelope preserved,
non-dict result preserved).

---

## Mode #8 — Integer overflow silent corruption

**Where:** `_coerce_number(integer_only=True)` in `model_tools.py`.

**Repro:**

```python
from model_tools import _coerce_number
result = _coerce_number("99999999999999999999", integer_only=True)
# Before fix: 99999999999999991433150857216    ← float round-trip corrupted
# After fix:  99999999999999999999             ← int() preserves precision
```

**Why it bites:** the old code went `float(value)` → `int(value)`.
For values past 2^53, `float()` rounds to the nearest representable
double, and `int()` preserves the *rounded* value. Huger-than-2^53
IDs, timestamps, and other long integers get silently corrupted.

**Fix:** for integer-only fields, try `int(value)` first. Python's
`int()` has arbitrary precision and handles the full input range
correctly. Fall through to the float path only for `"3.0"`-style
decimal strings (where `int()` raises `ValueError`).

**Test count:** 8 (huge integer preserved, normal integer, whitespace,
decimal fallback, three-point-zero, negative, inf rejection,
end-to-end through `coerce_tool_args`).

---

## Mode #9 — Reasoning block leak

**Where:** `_repair_tool_call_arguments`, *before* pass-0. The structural
passes can't help when the issue is *outside* the JSON.

**Repro:**

```python
raw = "<think>Let me think...\nThe user wants write_file.\n</think>\n{\"path\": \"/tmp/x\"}"
print(_repair_tool_call_arguments(raw, "write_file"))
# Before fix: {}                              ← entire call lost
# After fix:  {"path": "/tmp/x"}              ← JSON extracted from noise
```

**Why it bites:** reasoning models (Qwen 3.6+, DeepSeek-R1, o1) emit a
`<think>...</think>` block before the actual tool call. The block can
be 50–800 tokens and the model may place the JSON *anywhere* in or
around it. The old repair pipeline dropped the whole call to `{}`.

**Fix:** new pre-pass `_extract_json_from_text` that scans
byte-by-byte, respects string boundaries and escape sequences, and
returns the first balanced JSON value that either parses or looks
JSON-shaped. Runs *before* every other pass so the rest of the
pipeline operates on a clean string.

**Test count:** 3 (think-block full, think-block compact, thinking-tag XML variant).

---

## Mode #10 — Markdown code-fence wrapping

**Where:** same as #9.

**Repro:**

```python
raw = "```json\n{\"path\": \"/tmp/x\"}\n```"
print(_repair_tool_call_arguments(raw, "t"))
# Before fix: {}              ← entire call lost
# After fix:  {"path": "/tmp/x"}  ← JSON extracted
```

**Why it bites:** models that emit tool calls in their `content`
channel (not the structured `tool_calls` channel) almost always wrap
the JSON in a `` ```json ... ``` `` fence. The dispatch layer
sometimes can't tell if this is text content or a tool call; the
repair layer at least preserves the JSON.

**Fix:** same `_extract_json_from_text` pre-pass.

**Test count:** 2 (with `json` language tag, without language tag).

---

## Mode #11 — Preamble / postscript text

**Where:** same as #9.

**Repro:**

```python
raw = "Here is the JSON:\n{\"a\": 1}\nHope this helps!"
print(_repair_tool_call_arguments(raw, "t"))
# Before fix: {}              ← entire call lost
# After fix:  {"a": 1}        ← JSON extracted
```

**Why it bites:** the most common failure mode for less-disciplined
models. They treat tool-call JSON as "code they're sharing" and
surround it with conversational scaffolding. The eastondev "format
drift" framework labels this "extra content" — Type 3 of the three
format-drift families (missing fields, wrong type, extra content).

**Fix:** same `_extract_json_from_text` pre-pass. The extractor is
robust against worst-case combinations: reasoning-block + preamble +
JSON + postscript all in one stream.

**Test count:** 2 (simple preamble, worst-case reasoning+preamble+postscript).

---

## Mode #12 — `<tool_call>...</tool_call>` envelope

**Where:** same as #9.

**Repro:**

```python
raw = "<tool_call>\n{\"name\": \"end_call\", \"arguments\": {}}\n</tool_call>"
print(_repair_tool_call_arguments(raw, "t"))
# Before fix: {}              ← entire call lost
# After fix:  {"name": "end_call", "arguments": {}}  ← JSON extracted
```

**Why it bites:** Qwen 3.x via Groq is documented to speak the tool
call envelope literally in `content` when `tool_choice` is `auto`
instead of `required`. The dispatch layer is responsible for
recognising the shape and turning it into a real `tool_calls` entry,
but at least the args survive.

**Fix:** same pre-pass. Caveat: the extracted JSON is the
*tool-call shape* (`{"name": ..., "arguments": {...}}`), not the
*args shape*. The dispatch layer must handle the conversion — that
is a different concern (tool-name parsing), not arg-shape repair.

**Test count:** 2 (with newlines, compact form).

---

## Mode #13 — String `"null"` in non-nullable string field

**Where:** `coerce_tool_args` in `model_tools.py`, value-coercion
loop.

**Repro:**

```python
schema = {"type": "object", "properties": {"v": {"type": "string"}}}
args = {"v": "null"}
coerce_tool_args("t", args)  # schema says no nullable, no required
# Before fix: {"v": "null"}    ← literal text "null" passed through
# After fix:  {"v": None}      ← coerced to None
```

**Why it bites:** models occasionally emit the JSON-encoding of null
as a *string* when the schema field is declared non-nullable. The
tool's validator sees the literal text "null" and rejects it as a
non-null string — a hard schema error that loses the call's intent
(the model clearly meant null/absent).

**Fix:** new branch in `coerce_tool_args` — when `value == "null"`,
`expected == "string"`, and the schema doesn't explicitly allow null,
coerce to `None`. Convergent with the existing `_coerce_value` path
that already does this for *nullable* string schemas; the new branch
extends coverage to the non-nullable case.

**Test count:** 7 (string-null coerced, nullable preserved, exact
match only, non-string field unaffected, normal string unaffected,
CSV-boolean 1, CSV-boolean 0, yes/no variant).

---

## Mode #14 — CSV-style boolean `"1"` / `"0"`

**Where:** `_coerce_boolean` in `model_tools.py`.

**Repro:**

```python
from model_tools import _coerce_boolean
_coerce_boolean("1")  # Before fix: "1" (str)  # After fix: True
_coerce_boolean("0")  # Before fix: "0" (str)  # After fix: False
```

**Why it bites:** models that reason about CSV files, shell exit
codes, or script-style boolean fields emit `"1"` / `"0"` instead of
`"true"` / `"false"`. The old boolean coercion accepted only the
literal words.

**Fix:** extend `_coerce_boolean` to accept the four universally
recognised boolean-ish conventions: `true`/`false`, `1`/`0`,
`yes`/`no`, `on`/`off`. The first pair is safe by definition; the
latter two are fuzzy (`"no"` could appear in a string field
legitimately) but the schema has already committed to a boolean
interpretation by declaring `"type": "boolean"`.

**Test count:** included in the Mode #13 batch above.

---

## Mode #15 — Yes/No/On/Off in boolean field

**Where:** same as #14.

**Repro:**

```python
_coerce_boolean("yes")  # Before fix: "yes" (str)  # After fix: True
_coerce_boolean("no")   # Before fix: "no"  (str)  # After fix: False
_coerce_boolean("on")   # Before fix: "on"  (str)  # After fix: True
_coerce_boolean("off")  # Before fix: "off" (str)  # After fix: False
```

**Why it bites:** same as #14 but with the natural-language pair.
Most often seen when a model is paraphrasing a system prompt that
says "set the `enabled` flag to yes" or "turn notifications off".

**Fix:** same as #14.

**Test count:** included in the Mode #13 batch above.

---

## Full probe grid (32 cases)

Used during the audits. Run via `scripts/probe_repair_layer.py`. The
first 16 cases target modes #1–#8 (Pass 2 audit). The next 16 target
modes #9–#15 (Pass 3 audit) plus the false-positive regression case.

| # | Mode | Input | Tier |
|---|---|---|---|
| 1 | top-level array wrapping | `[{"a": 1}]` | 1 |
| 2 | result envelope wrapping | `{"result": {"a": 1}}` | 1 |
| 3 | JSONP wrapper | `callback({"a": 1})` | 3 |
| 4 | NaN literal | `{"x": NaN}` | 1 |
| 5 | +Infinity literal | `{"x": Infinity}` | 1 |
| 6 | single-quote (Python style) | `{'a': 1}` | 3 |
| 7 | Python True/False | `{"x": True, "y": False}` | 3 |
| 8 | unquoted string value | `{"a": hello}` | 3 |
| 9 | JSON5 comment | `{"a": 1, /* x */ "b": 2}` | 2 |
| 10 | duplicate keys (Python last-wins) | `{"a": 1, "a": 2}` | 3 |
| 11 | truncated enum value mid-string | `{"color": "re` | 2 |
| 12 | JS-style unquoted key | `{a: 1, b: 2}` | 3 |
| 13 | hex numeric | `{"x": 0xFF}` | 3 |
| 14 | trailing semicolon | `{"a": 1};` | 3 |
| 15 | multi top-level objects | `{"a": 1}{"b": 2}` | 3 |
| 16 | mixed-quote in string | `{"msg": "he said 'hi'"}` | 3 |
| 17 | reasoning block leak | `<think>...</think>\n{"a": 1}` | 1 |
| 18 | reasoning block compact | `<think>x</think>{"a": 1}` | 1 |
| 19 | markdown code fence (with lang) | ` ```json\n{...}\n``` ` | 1 |
| 20 | markdown code fence (no lang) | ` ```\n{...}\n``` ` | 1 |
| 21 | preamble text | `Here is the JSON: {...}` | 1 |
| 22 | preamble + postscript | `Sure, here: {...} Done!` | 1 |
| 23 | worst case (reasoning+preamble+json+postscript) | (all four stacked) | 1 |
| 24 | tool_call envelope with newlines | ` ```\n{...}\n``` ` | 2 |
| 25 | tool_call envelope compact | ` ```\n{...}\n``` ` | 2 |
| 26 | nested object extraction | `preamble {"a": {"b": 1}} postamble` | 1 |
| 27 | array extraction | `arr [{"a": 1}] end` | 1 |
| 28 | string containing `}` | `{"a": 1, "b": "}"}` | 1 |
| 29 | unquoted-word false positive | `text "{curly}" {"a": 1}` | 1 |
| 30 | no JSON at all | pure text | 3 |
| 31 | already-valid JSON unchanged | `{"a": 1, "b": 2}` | 1 (regression) |
| 32 | extract+repair combined | ` ```\n{"a": 1,}\n``` ` | 1 |

**Triage summary:**

- **Tier 1 (ship now):** cases 1, 2, 4, 5, 17–23, 26–29, 31, 32 — silent
  corruption, hard dispatch crash, or whole-call data loss. All shipped
  in their respective PRs.
- **Tier 2 (ship this week or backlog):** cases 9, 11, 24, 25 — data
  loss but session stays alive via last-resort `{}`. Case 9 (JSON5
  comment) and 11 (truncated enum) are rare in practice. Cases 24/25
  (`<tool_call>` envelope) are technically the right shape for the
  dispatch layer to handle, not the args repair — backlog them.
- **Tier 3 (skip):** cases 3, 6–8, 10, 12–16, 30 — last-resort `{}`
  keeps the session alive at the cost of one lost call. Not worth the
  repair complexity.

The `{curly}` false positive (case 29) is the most interesting Tier 1
case — the extractor needs a `_looks_like_json` heuristic that accepts
balanced candidates that *look* JSON-shaped (start with `{"` or have
non-trivial array content) while rejecting random balanced substrings
like `{curly}` that happen to appear in conversational text.

---

## Triage template (for the next audit)

When probing any LLM harness, classify each finding before fixing:

```text
Mode #: <one-line description>
Where: <file:function>
Repro: <3-line code snippet>
Symptom: <what goes wrong, who notices>
Fix shape: <repair in same layer / push to schema / extend semantics>
Tier: 1 (ship now) | 2 (this week) | 3 (skip, fallback already safe)
Test count: <how many test cases prove the fix>
```

The audit is done when every finding has a tier and Tier 1 is
shipped with TDD. Tier 2 and 3 findings go in a follow-up backlog,
not a parallel PR — they earn their own audit when the telemetry
says they bite.

## Audit methodology recap

The pattern that finds these tiers reliably:

1. **Read the external catalogue** — Ahmad's post for the original
   four, eastondev's "format drift" framework for missing/wrong-type/extra
   content, the Qwen 3.6 reasoning-block pitfall for `<think>` leakage.
2. **Audit the existing repair code against it** — mark each mode as
   covered, not covered, or partially covered.
3. **Write a probe script** that exercises every related code path
   with 15–20 realistic failure cases per audit pass.
4. **Triage by production risk** into three tiers as above.
5. **Ship Tier 1 with TDD**, then re-probe to confirm the audit is
   closed. Tier 2/3 findings go in a follow-up backlog, not a parallel
   PR.
6. **Re-audit on a schedule** — every ~6 months, or whenever a new
   model class is added (e.g. when M3 routes through a new provider,
   the noise-extraction pre-pass becomes load-bearing because the new
   provider's response format is slightly different).
