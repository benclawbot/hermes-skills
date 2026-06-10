---
name: tool-call-harness-repair
description: "JSON-schema tool-calling harness design for LLM agents. Use when designing or debugging the layer between model-emitted tool calls and tool dispatch — preprocessing vs. validate-then-repair, open-model failure modes, schema strictness tradeoffs, when to coerce silently vs. surface the choice to the model, and how to localize the bug from the validator's own issue list. Applies to Hermes, Claude Code, custom agents, and any harness wrapping an LLM with JSON-schema tools. ALSO load this skill first when the task matches any failure mode #1-#18 - the audit is impossible to do correctly without it."
version: 1.5.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [llm, tools, json-schema, harness, repair, open-models, design-pattern]
---

# Tool-call harness repair

A field guide to the layer between an LLM emitting tool calls and the tool actually executing. Every public LLM that exposes tool calling has a contract the model has to honor (JSON schema, param names, type). Most "the model can't use tools" reports are actually harness bugs.

The pattern that works: **validate-then-repair, in that order, with telemetry at every step.**

## STOP — Load-check before proceeding

**If you are reading this skill because a session just told you to audit tool-call repair, JSON parse failures, coerce_tool_args, or any of the failure modes catalogued below, this section is for you.**

A prior session (2026-06-03) re-derived every failure mode in this skill from scratch and shipped 1,035 lines of duplicated work — *because it did not load this skill first*. The failure mode it fell into ("The previous session already fixed this") is the exact trap the Verification checklist at the bottom warns about. That session's root-cause analysis is in `references/2026-06-03-session.md`. Read it after you have internalised the methodology below.

If the session's task is "audit X" or "fix Y" where X or Y is one of the failure modes #1-#18, the first action is:

1. **Run `git status` and `git diff`** on the named files. If a prior session claimed work, the diff is the only truth.
2. **Run `scripts/probe_repair_layer.py`** to triage current state. Do not write a new probe.
3. **Read the rationalization traps below** — they exist because the trap keeps firing.
4. **Then** start the audit, knowing the modes, the upstream PRs, and the probe grid already documented.

The rest of the skill is the technical content. The trap and the load-check above are the workflow content. Both are load-bearing.

## 3-step verify protocol (when the prose says work is done)

When a session-summary or compaction handoff claims work was shipped, do this *before* trusting the claim:

```bash
git status                                # must show modified or staged files
git diff --stat                           # must be non-zero
git diff -- <file-from-summary>           # must show the actual patch
```

If `git status` is clean and the prose claims a fix was shipped, the work is **un-shipped**. Re-apply, don't trust. If `git diff --stat` shows zero changes, also un-shipped. If the diff is in the wrong file, the patch landed in the wrong place — recover from the worktree or branch the prior session was on.

This is the positive form of the trap-table warning. The trap says "don't trust the prose." The protocol says "here's exactly what to type to verify the prose." A future audit should treat the protocol as the only way to close the "previous session claimed but didn't patch" gap.

## Recurring rationalization traps (read first)

**This section exists because the trap keeps firing, even after being added to memory and the Verification checklist.** When auditing tool-call repair, watch for these specific rationalizations in your own reasoning. They sound like reasonable engineering judgement but they are *always* the wrong disposition for a confirmed real bug.

| Rationalization | Why it's wrong | What to do instead |
|---|---|---|
| "This is pre-existing, not part of this audit." | "Pre-existing" describes *when* the bug was introduced, not whether it should be fixed. A pre-existing bug in the local install is still a bug in the local install. | If the bug is confirmed real (probe or reproducer), fix it as part of the same change. The user is paying for the audit, not the audit-without-the-fixes. |
| "There's an open upstream PR for this; no point duplicating." | The PR is *open* — meaning it isn't merged into your local install. The local install has the bug *now*. | If the PR is open, mirror its contract verbatim (function name, signature, return shape) so a future merge is conflict-free. If the PR is *closed* without merging, you may genuinely defer — file a comment so it doesn't get lost. |
| "This is path-specific / model-specific / not generic." | Maybe. But the *user is hitting it in production*. The "generic" bar is a code-quality preference, not a shipping priority. | If a tool is in your critical path and the bug bites, fix it for that tool. Generic-ify in a follow-up if the abstraction is clean; don't let "not generic enough" block the fix. |
| "It's out of scope for this session's stated goal." | A real bug found during audit *is* in scope, by definition — the audit's job is to find bugs. Scope is set by the user, who said "fix them". | Fix the bug. The "scope" framing only applies to features, not to fixing broken things. |
| "The previous session already fixed this." | A session can describe work as "done" in its summary without the patch ever landing. The trust signal is the diff, not the prose. | `git status` + `git diff` first. If the file is unchanged, the work is un-shipped. Re-apply, don't trust. |
| "I'll mention it in the summary and let the user decide." | Mentioning is *deferring*. The user already decided when they said "fix them" — you're just adding a turn to confirm what was already confirmed. | Fix it. If you genuinely can't (missing permission, blocked dependency), say so explicitly with the blocker, not a "you decide" question. |

**The meta-pattern:** I have a memory entry for this lesson. I have it in the skill's Verification checklist. I keep bypassing both. The structural fix is: *audit pre-existing bugs as part of the audit's deliverable*, not as something the audit might optionally produce. The audit-without-the-fixes is the failure mode, not the audit-with-scope-creep.

If you find yourself writing any of the rationalization phrases above, treat that as a stop signal: re-read the bug you just rationalized, verify it's still real, and either fix it or explicitly defer with a reason that *isn't* a rationalization.

The rest of this skill is the technical content. The traps above are the workflow content. Both are load-bearing.

## The four open-model failure modes

Ahmad Awais's June 2026 catalogue from two days of DeepSeek/Qwen/GLM traffic in production (CommandCode AI CLI) identifies the *only four* mistakes these models make on tool calls. Not "they're bad at tool calling" — four specific patterns, each ~30–100 lines to fix, ordered by what to run first:

1. **`null` for optional field** — model emits `{"tag": null}` where the schema means "omit if absent". Fix: strip `None` from the args dict when the field isn't required and the schema doesn't explicitly allow null. **Run first** — if you preprocess later, you've already corrupted type detection.

2. **JSON string instead of native array** — model emits `{"urls": "[\"a\",\"b\"]"}` where the schema wants `["a","b"]`. Fix: try `json.loads` on string values for array/object-typed fields; if it parses to the right Python type, use it. **Run before** mode #4 or you'll wrap the parsed array as `[["a","b"]]`.

3. **Empty-dict placeholder for array** — model emits `{"items": {}}` where the schema wants a list. Fix: substitute `[]` instead of letting the bare-scalar wrap path turn it into `[{}]`. Only check `value == {}` literally — non-empty dicts are intentional single-element arrays.

4. **Bare string for array field** — model emits `{"urls": "https://a.com"}` where the schema wants `["https://a.com"]`. Fix: wrap in a single-element list. Apply AFTER modes #2 and #3.

These four cover ~90% of open-model tool-call failures. The rest is one-offs (markdown auto-links in path fields — a DeepSeek-flash-specific chat-distribution leak; fix with a `pathString()` zod refinement, not a generic repair).

### Beyond the four: outer-envelope and numeric-precision failures

A second audit pass (June 2026) probed a wider space of model output and surfaced four more modes that live in the *raw-args repair* and *numeric coercion* paths, not in the `coerce_tool_args` dispatcher. Treat them as a checklist, not a recipe — only ship the ones your probe finds.

5. **NaN / Infinity literals in raw JSON** — `json.loads(strict=False)` (used by every local-model repair layer to accept llama.cpp's literal control characters) silently accepts `NaN`, `Infinity`, `-Infinity` as number tokens. They are invalid per the JSON spec, and even when a provider accepts them, the wire form is ambiguous. Fix: recursively replace non-finite floats with `None` after parse, then re-serialise with `allow_nan=False`. Symptom: provider returns HTTP 400 "invalid tool call arguments" for an arg like `{"score": NaN}`.

6. **Top-level array wrapping** — model emits `[{"k": v}]` for a single tool call's args; tool dispatch expects a dict and crashes on `args["k"]`. Fix: in the raw-args repair layer, if `parsed` is a single-element list of one dict, unwrap to the dict. Do NOT unwrap multi-element arrays — those are legitimate parallel-call payloads and dropping data silently is worse than the original bug.

7. **`result` envelope wrapping** — model emits `{"result": {...}}` thinking it's wrapping a function-call response (a habit from chain-of-thought traces). Strict rule: only unwrap when there is **exactly one key named `result`** AND its value is a dict. Mixed envelopes (`{"result": {...}, "status": "ok"}`) are real shapes the model intended and must be preserved.

8. **Integer overflow silent corruption** — `_coerce_number(integer_only=True)` going through `float(value)` then `int(value)` rounds any integer past 2^53 to the nearest representable double. `'99999999999999999999'` returns `99999999999999991433150857216`. Fix: for integer-only fields, parse the string directly with `int()` (Python's arbitrary precision) and only fall through to the float path for `"3.0"`-style decimal strings.

### Beyond the eight: text-noise extraction and string-sentinel coercion

A third audit pass (June 2026) — this time pulling current research from eastondev's "three-types-of-format-drift" framework, the dev.to Qwen 3.6 `enable_thinking` pitfall writeup, and the LiveKit community thread on Qwen-via-Groq "speaking tool call JSON out loud" — surfaced a new *class* of failure: the JSON is *fine*, it's just buried in surrounding noise or the value is a string-form sentinel that the schema doesn't accept. These need a *pre-pass* that runs before everything else, plus targeted string-sentinel coercions in the value-coercion path.

9. **Reasoning block leak** — reasoning models (Qwen 3.6+, DeepSeek-R1, o1) emit a `<think>...</think>` block (or the XML `<thinking>...</thinking>` variant) before the actual tool call. The block can be 50–800 tokens. Fix: extract the first balanced JSON value from the raw text *before* any structural repair pass. The pre-pass is `_extract_json_from_text` — scans byte-by-byte respecting string boundaries and escape sequences, returns the first candidate that either parses or *looks* JSON-shaped (starts with `{\"` or has non-trivial array content). This rejects the `{curly}` false positive in conversational text.

10. **Markdown code-fence wrapping** — models that emit tool calls in their `content` channel (not the structured `tool_calls` channel) almost always wrap the JSON in a `` ```json ... ``` `` fence. Fix: same pre-pass as #9.

11. **Preamble / postscript text** — the most common failure mode for less-disciplined models per the eastondev "extra content" Type 3 drift. They treat tool-call JSON as "code they're sharing" and surround it with conversational scaffolding like "Here is the JSON: ... I hope this helps!". Fix: same pre-pass as #9. The extractor is robust against worst-case combinations: reasoning-block + preamble + JSON + postscript all in one stream.

12. **`<tool_call>...</tool_call>` envelope** — Qwen 3.x via Groq is documented to speak the tool call envelope literally in `content` when `tool_choice` is `auto` instead of `required`. Fix: same pre-pass extracts the JSON inside, but the *shape* is the tool-call envelope (`{"name": ..., "arguments": {...}}`), not the *args shape*. That's a dispatch-layer concern (tool-name parsing), not arg-shape repair. Caveat: the pre-pass saves the JSON; the dispatch layer is responsible for splitting it into name + args.

13. **String `"null"` in non-nullable string field** — models occasionally emit the JSON-encoding of null as a *string* when the schema field is declared non-nullable. The tool's validator sees the literal text "null" and rejects it. Fix: new branch in `coerce_tool_args` — when `value == "null"`, `expected == "string"`, and the schema doesn't explicitly allow null, coerce to `None`. Convergent with the existing `_coerce_value` path that already does this for *nullable* schemas; the new branch extends coverage to non-nullable.

14. **CSV-style boolean `"1"` / `"0"`** — models that reason about CSV files, shell exit codes, or script-style boolean fields emit `"1"` / `"0"` instead of `"true"` / `"false"`. Fix: extend `_coerce_boolean` to accept the four universally-recognised boolean-ish conventions: `true`/`false`, `1`/`0`, `yes`/`no`, `on`/`off`. The first pair is safe by definition; the latter two are fuzzy (`"no"` could appear in a string field legitimately) but the schema has already committed to a boolean interpretation by declaring `"type": "boolean"`.

15. **Yes/No/On/Off in boolean field** — same as #14 but with the natural-language pair. Most often seen when a model is paraphrasing a system prompt that says "set the `enabled` flag to yes" or "turn notifications off". Fix: same as #14.

### Beyond the fifteen: concatenated payloads and Unicode-whitespace traps

A fourth audit pass (June 2026) — this time cross-referencing **open upstream PRs** on the Hermes repo via GitHub's search API — surfaced two failure-mode families that hide inside the raw-args layer even when the JSON itself is technically valid. The unifying signal: `json.loads()` rejects the *whole* string because of *adjacent* junk, even when a complete JSON object is plainly visible in the payload. The pattern is "valid JSON + something else", not "broken JSON".

The two helpers that address these are *complementary*, not competing:

- **`_split_concatenated_tool_call_arguments(raw)`** — handles the case where the payload is **2+ complete top-level dicts** with no delimiter. Uses `json.JSONDecoder.raw_decode()` walking left-to-right. Returns a list of re-serialised JSON strings *only* when the entire string decodes losslessly into 2+ dicts; returns `None` otherwise (so existing partial-truncation handling stays in control). This is the case where the **model emitted multiple parallel tool calls as a single chunk** — Gemini-3-flash-preview is the documented culprit. **Match the upstream PR's contract verbatim** (function name, return type, "None vs list" semantics) so a future merge is conflict-free.
- **`_extract_first_json_object(raw)`** — handles the case where the **first** JSON value parses but the trailing text does not. This is the "valid + garbage" pattern. Uses `raw_decode()` at *every* `{` position, returns the first complete dict, discards the rest. Different from `_split_concatenated_tool_call_arguments` because the tail is *not* a complete dict — it's a U+2028 line separator, a BOM, a model preamble/postscript, or another model-emitted value the schema doesn't accept.

16. **Concatenated streamed payloads `{"a":1}{"b":2}`** — Gemini-3-flash-preview and certain Ollama routes emit multiple complete top-level argument objects without delimiters when the model decides to do parallel calls in a single streaming chunk. Without the split, the repair layer returns `{}` and **all** calls are lost. The upstream Hermes fix (PR #25346 / #36039) uses `_split_concatenated_tool_call_arguments` and the streaming-integration seam fans a single split into multiple `tool_calls` entries with synthetic IDs (`call_xyz`, `call_xyz-split-2`, ...). **Tier 1 in production** — bump the original probe grid's case 15 ("multi top-level objects") from Tier 3 to Tier 1; the Gemini traffic proves it.

17. **Trailing-garbage after valid JSON `{"a":1}garbage`** — model preamble, postscript text, U+2028 / U+2029 line separators, BOM markers, extra values that aren't part of the call (`{"a":1} true`, `{"a":1} null`, `{"a":1}"excess"`, `{"a":1}, `). `json.loads` rejects the whole string even though the first dict is valid. Different from mode #16 in that the tail is *not* another complete dict. The `_extract_first_json_object` helper handles this with the "looks like JSON" fallback (accepts a balanced candidate that *starts* with `{\"` even if it doesn't fully parse, so trailing-comma cases like `{"a":1,}` get rescued too).

**Why these belong in a *fourth* class, not in the pre-pass with #9–#12:**

The #9–#12 pre-pass handles JSON that is *fully valid but embedded in noise* (think blocks, code fences, tool_call envelopes). The #16–#17 case is JSON that is *adjacent to something else at the same nesting level* — the model emitted the right thing, then kept going. The right fix is the **byte-level decoder pattern** (walk left-to-right with `raw_decode()`), not a structural pre-pass. Adding a 6th pre-pass to handle this would dilute the discipline above; using the same primitive that the upstream PR already designed is cleaner.

**Why modes #9–#12 deserve their own pre-pass, not more `coerce_tool_args` entries:** the structural repair passes operate *inside* the JSON. When the JSON is *absent* — buried in noise — the passes see garbage and bail. The right fix is a pre-pass that locates the JSON first; everything downstream is unchanged.

**Why modes #13–#15 belong in `coerce_tool_args`, not as a 6th generic repair layer:** they're schema-driven coercions (the schema declares `type: string` or `type: boolean`), and `coerce_tool_args` is exactly where the schema is consulted. Adding them to the raw-args repair layer would mean re-parsing the schema there, which is wrong layering.

### Beyond the seventeen: content-channel recovery (a different layer)

Mode #18 is *not* a repair to JSON shape. It's a recovery at the **response normalization layer** — a different place in the harness entirely. The previous 17 modes operate on the *raw argument string* and the *arg-shape coercion path*. Mode #18 operates on the *assistant message as a whole*, deciding what to do when the model emitted a tool call in the wrong channel.

18. **Content-channel tool calls** — model emits `<invoke name="..."><parameter name="...">value</parameter></invoke>` or `<tool_call>{...}</tool_call>` or `<function name="...">{json}</function>` in the response `content` field instead of the structured `tool_calls` field. Symptom: the call leaks as chat text, gets forwarded to Telegram, or stalls the agent loop. Documented production failure for M2.7-via-LiteLLM (Hermes issue #12090); likely for M3 and other open-weight models under load.

    **Why this is mode #18 and not a sub-case of #9–#12:** modes #9–#12 assume the JSON is buried in *text noise* around a tool call. Mode #18 assumes the model intended a *real tool call* and used the wrong transport channel. The fix is a *promotion seam* in the response normalization path, not a pre-pass in the arg repair path.

    **Fix shape:** a leaf parser module (e.g. `agent/transports/content_tool_calls.py`) that detects the various emission shapes (6 parsers is a good starting set: `<tool_call>` JSON, bare JSON object, Kimi K2 tokens, MiniMax `<invoke>`, Gemma `<function name="...">`, Ollama-cloud `<function=NAME>`), plus a single promotion seam in `agent/conversation_loop.py` after response normalization but before the `post_api_request` hook. The seam is a strict no-op when structured `tool_calls` already exist, so native tool-calling paths are untouched.

    **Critical design rules:**

    - **Exact-name match only** for the promotion gate. A tool name lifted from free-text `content` is lower-trust than one from a structured `tool_calls` field. Fuzzy-repairing it risks executing the wrong tool from prose. Native structured calls still get the fuzzy repair at the loop seam; content-channel calls do not.
    - **Line-start / tag-wrapped gates** on the regexes. Prose like "you'd call `<function=x>`" mid-sentence must not promote.
    - **Deterministic call IDs** (sha256 of name+args+index) so the prompt cache stays warm.
    - **Env kill-switches** (`HERMES_PROMOTE_TOOLCALLS`, `HERMES_PROMOTE_BARE_JSON_TOOLCALL`) for the parsers that are most false-positive-prone (bare JSON object especially — opt-in via `HERMES_PROMOTE_BARE_JSON_TOOLCALL=false` if the model starts emitting legitimate prose that looks like a bare tool call).

    The upstream Hermes fix is PR #35129. Port the leaf parser module verbatim (function names, parser names, dedup logic) and add only the promotion seam locally. The full PR (with the early-gate seam in `_should_treat_stop_as_truncated`) is a 6-file change — porting only the leaf module + the main seam covers the primary symptom (M3 / M2.7 content-channel leak) without the larger conversation-loop surgery.

    Test for "is this happening?" before porting: watch your model logs for response.finish_reason == "stop" with `content` containing `<invoke` / `<tool_call>` / `<function` and `tool_calls` empty. If you see it once a week or more, port mode #18.

The audit methodology that finds these:

1. Read the external catalogue (Ahmad's post, the eastondev format-drift framework, your own telemetry, etc.)
2. **Cross-reference open upstream PRs for the codebase you're auditing** — `https://api.github.com/search/issues?q=tool_call+arguments+JSON+parse+OR+repair&per_page=10` is captcha-resistant (the unauthenticated REST API has no bot detection) and surfaces PRs that have *already* designed the fix. Adopt their function names and contracts verbatim to keep future merges clean. Don't reinvent when a mature fix exists upstream.
3. Audit the existing repair code against it — mark which modes are covered, which are not, and which are partially covered
4. Write a probe script that exercises *every* related code path with 15–20 realistic failure cases
5. Triage by production risk into three tiers:
   - **Tier 1 (ship now)**: silent corruption or hard provider rejection
   - **Tier 2 (ship this week)**: data loss without telemetry
   - **Tier 3 (skip)**: rare, fallback already safe
6. Ship Tier 1 with TDD, then re-probe to confirm the audit is closed
7. **Re-audit on a schedule** — every ~6 months, or whenever a new model class is added. Modes #9–#15 only became Tier 1 in 2026 when Qwen 3.6 and DeepSeek-R1 became production models; they were Tier 3 (rare) in 2024. The #16–#17 class became Tier 1 the moment Gemini
flash-preview went live in production traffic — the upstream PRs are the proof. Mode #18 became Tier 1 the moment M2.7-via-LiteLLM hit issue #12090 in production.
8. **Verify "previous session applied the fix" with `git status` / `git diff` before declaring audit closed** (see the 3-step verify protocol at the top of this file). A session that describes work as "done" in its summary can still have *not actually patched* the file (this has happened more than once). The trust signal is the diff, not the prose.

A reusable probe template lives at `scripts/probe_repair_layer.py` (32-case default grid, covers modes #1–#15; bump the grid to 36+ cases if you include the #16–#17 class). The per-mode detail and the full probe grid are in `references/extended-failure-modes.md`. **Mode #18 lives in a different layer (response normalization) and is not covered by the probe grid** — port it as a leaf parser with its own test file, run the local content-channel integration test for your specific model. **Mode #19** (list-of-dicts when schema wants list-of-strings — silent at runtime, see `references/mode-19-list-of-dicts.md`) is element-level inverse of mode #3 and was surfaced by a 2026-06-07 `clarify` tool incident on Telegram.

## The core design pattern: validate-then-repair

```python
def dispatch(tool_name, args):
    # 1. Parse the input as-is. If the schema validates, ship it.
    try:
        validated = schema.validate(args)
        return invoke(tool_name, validated)
    except ValidationError as e:
        pass  # fall through to repair

    # 2. Walk the validator's own issue list. For each issue path, try
    #    the four repairs in order until one applies.
    for issue in e.issues:
        repaired = apply_repair(args, issue, repair_chain=[
            strip_null,           # mode #1
            parse_json_string,    # mode #2
            empty_dict_to_list,   # mode #3
            wrap_singleton,       # mode #4
        ])
        if repaired is not args:
            args = repaired
            break

    # 3. Parse again. On success, log and ship.
    try:
        validated = schema.validate(args)
        log("tool_input_repaired", tool=tool_name, repair=...)
        return invoke(tool_name, validated)
    except ValidationError:
        log("tool_input_invalid", tool=tool_name, args=args)
        return model_readable_retry_message(args, e)
```

**Why this beats the obvious alternative** (preprocess-then-validate):

- Preprocess encodes a prior about what's broken. When you preprocess a string that *happened* to be JSON-shaped content (e.g. a `writeFile` body), you rewrite user data before it hits disk. Silent corruption, easy to miss in smoke tests.
- Validate-then-repair lets the schema be the prior. The validator localizes the bug to specific paths; you only spend repair budget at the exact fields that disagree with the contract.
- Per-tool telemetry comes for free — `tool_input_repaired:${toolName}` and `tool_input_invalid:${toolName}` lines let you spot a model regressing on a specific contract before users do.

**Caveat for the pre-pass (modes #9–#12):** the `_extract_json_from_text` pre-pass is the *one* place where preprocessing is correct. It runs *before* validate-then-repair, on the *raw text* (not the parsed args), and the cost of a wrong extraction is bounded — the worst case is that the extracted substring is unrepairable, the original `{}` last-resort kicks in, and the session survives. The structural-repair-pass risk of "rewriting `writeFile` content that happened to be JSON-shaped" doesn't apply because we never touch parsed values at the pre-pass stage.

**Caveat for the content-channel promotion (mode #18):** it operates on the assistant message, not the args. It runs *after* response normalization but *before* the dispatch path. It is a *promotion* (move from `content` channel to `tool_calls` channel), not a *repair* (rewrite malformed args). The semantics are different and the seam should not be confused with the arg-repair pipeline.

## Design decisions that matter

### Strip vs. preserve null

Strip `None` ONLY when the field is not required AND the schema doesn't explicitly allow null (`nullable: true` or `"type": ["string", "null"]` or a oneOf/anyOf with a null variant). Required fields and explicitly-nullable fields get their null preserved — the model committed to that value or the tool opted in to handling it.

### Wrap silently vs. surface the choice

For mode #4 (bare string → array), wrapping silently is fine. The model said one URL; you passed one URL. No information lost.

For mode #14 (CSV-style boolean), coercing silently is fine — the schema declared `type: boolean`, so the model has already committed to a boolean interpretation, and the four conventions (`true/false`, `1/0`, `yes/no`, `on/off`) are universally recognised. No information lost.

For RELATIONAL invariants (e.g. "if `offset` is provided, `limit` must be too"), **don't try to repair**. The fields are each independently valid; the bug is in the relationship. Instead, teach the function the model's intent: `limit` alone → default `offset = 0`; `offset` alone → default `limit = 2000`. Then **surface the decision back to the model in the result**: "Note: limit was not provided; defaulted to 2000 lines. To override, retry with both." No `Error:` prefix — the model self-corrects on the next turn.

> Repair where you can. Extend semantics where you can't. Surface the choice either way.

### Where to draw the line on repair

If you find yourself writing a 5th or 6th repair in the **same layer**, you have a contract design problem, not a model problem. Step back and ask: should this field be optional? Should the schema accept a wider union? Should the tool default more aggressively? Silent repairs that go beyond ~4 patterns tend to mask the real issue and create new ones.

Modes #9–#12 are an exception: they live in a *new* pre-pass, not the existing repair layer. Adding a pre-pass to locate the JSON before the structural passes operate on it is a layering change, not "one more repair" — it doesn't dilute the discipline above.

Modes #13–#15 are also an exception: they live in `coerce_tool_args`, the same place as modes #1–#4, but they're *coercions*, not *repairs*. A coercion maps a value the model sent to the value the schema expects; a repair guesses the model's intent. Conflating the two in the same code path is the mistake to avoid.

Modes #16–#17 are a *split + extract* layer that uses the same `raw_decode()` primitive as the upstream PR. Same `raw_decode` primitive, different return contract (list vs single), different pre-pass ordering rule (split before extract, or the extractor eats the second dict in `{"a":1}{"b":2}`).

Mode #18 is a *promotion seam* in a different layer entirely (response normalization, not arg repair). It does not extend the validate-then-repair pattern; it extends the response-normalization pattern. Treat it as a separate design with its own critical rules (exact-name match, line-start gates, deterministic call IDs, env kill-switches).

## Commercial vs. open model contracts

The largest commercial models (Claude Opus, GPT-4, etc.) eat schema strictness invisibly because they've seen enough of every contract during pretraining. Open models pay it loudly and get dismissed for it. The repair layer is the difference — and the same layer that makes DeepSeek-v4-Pro beat Opus-4.7 on internal evals is what lets M3 route through Anthropic-format tool calling without choking on a slightly off JSON.

**The harness is where you mediate between distributions.**

Reasoning models (Qwen 3.6+, DeepSeek-R1, o1) are a new wrinkle: they emit `<think>` blocks that the pre-2024 repair layers were never designed for. A model that "speaks the JSON out loud" in its content channel, wrapped in `<tool_call>...</tool_call>` envelopes, or with explicit reasoning blocks is still a *good* tool-calling model — it just needs a pre-pass to find the JSON. M3 routes through Anthropic-format, and M3 itself **does** emit `` blocks when called directly (non-Hermes) with a structured-output prompt — see `references/m3-think-blocks-2026-06.md` for the empirical evidence and the working prompt template. The pre-pass (modes #9–12) is required for any direct M3 call, not just for open-weight sub-agents.

Content-channel recovery (mode #18) is the production-incident case for M2.7-via-LiteLLM and likely M3 under load. The port from upstream Hermes PR #35129 is the right shape; the leaf parser + single promotion seam covers the primary symptom without the larger conversation-loop surgery.

## Applies to

- **Hermes Agent** — `model_tools.coerce_tool_args` implements modes #1, #3, #4, #13, #14, #15 (run order: null-strip → empty-dict → string-`"null"` → wrap → boolean coercion). `run_agent._repair_tool_call_arguments` implements modes #5–#8 (pass-0 envelope unwrap + NaN scrub) and the pre-pass `run_agent._extract_json_from_text` implements modes #9–#12. The split + extract layer (modes #16, #17) lives in `_split_concatenated_tool_call_arguments` and `_extract_first_json_object` in the same file. The content-channel promotion (mode #18) lives in `agent/transports/content_tool_calls.py` and the promotion seam in `agent/conversation_loop.py`. Tests: `tests/run_agent/test_tool_arg_coercion.py`, `tests/run_agent/test_repair_tool_call_arguments.py`, and `tests/agent/transports/test_content_tool_calls.py`.
- **Claude Code / Cursor / Cline** — same failure modes apply when you point these at open-weight models via custom providers
- **Custom agent harnesses** — if you're building one and the model is failing on tool calls, your contract is the problem ~90% of the time, not the model

## Verification

After any repair-layer change:

1. **Confirm the patch is actually applied** — `git status` should show your modified file in the uncommitted list, and `git diff <file>` should show your changes. A session that describes work as "done" in its summary can still have *not actually patched* the file (this has happened more than once across audit sessions). The trust signal is the diff, not the prose. If a previous session claimed to have shipped a fix but `git status` is clean, treat the work as un-shipped and start fresh. (See the 3-step verify protocol at the top of this file.)
2. Run the existing test suite for the dispatch path — make sure you didn't regress previously-handled cases
3. Add tests for each new repair with the schema in the test, not just the args (the schema is the prior; the test should reflect that)
4. Watch the `tool_input_repaired` / `tool_input_invalid` log lines for a session or two to confirm the repairs are firing on real traffic
5. Don't add a 5th repair in the same layer — if you need one, push the change up to the schema. (Modes #9–#12 are a *new pre-pass*, not a 5th repair in the existing layer; modes #13–#15 are coercions, not repairs; modes #16–#17 are a *split + extract* layer that uses the same `raw_decode()` primitive as the upstream PR; mode #18 is a *promotion seam* in a different layer entirely — all four are layering changes, not discipline violations.)
6. Run `scripts/probe_repair_layer.py` — exits nonzero if any Tier 1 failures remain, useful in CI
7. If you ported mode #18 (content-channel promotion), also run `tests/agent/transports/test_content_tool_calls.py` to confirm the leaf parsers are working and the promotion seam is wired correctly

**Fixing pre-existing bugs found during an audit:** if a probe surfaces a bug that was there before you started — silent corruption in `_coerce_number`, a missing null-strip path, an envelope that crashes dispatch — fix it as part of the same change. Don't dismiss real bugs as "pre-existing" and skip them. Verify the bug actually exists and is worth fixing first (a probe or reproducer beats a guess), but once confirmed, ship the fix with the rest of the audit. The user is paying for the audit, not for the audit-without-the-fixes. Not every "I think this is broken" claim is real — the audit includes *verifying* the claim, not just fixing the thing you assumed was broken.

## PR-porting protocol (when adopting an open upstream fix)

When a mature open-source fix exists upstream (same repo or neighbouring one), adopt its contract verbatim. The mature fix already encodes the edge cases the original author hit, and matching the contract makes the future merge conflict-free.

The protocol:

1. **Function name** — copy exactly. If the upstream is `_split_concatenated_tool_call_arguments`, name yours `_split_concatenated_tool_call_arguments`. Don't rename to `split_tool_call_args` because it's "cleaner."
2. **Signature** — copy the parameters, defaults, and return type annotation. The "None vs list" semantics in particular are usually load-bearing.
3. **Return shape** — copy. If the upstream returns `Optional[List[str]]`, yours should too. Don't return a dict or raise exceptions just because your local style prefers it.
4. **Test cases** — copy. The upstream's test grid is part of the contract. If they test that `"partial tail"` returns `None`, you should test the same thing.
5. **Module location** — match where you can. If the upstream puts the helper in `agent/transports/content_tool_calls.py`, putting it in a different module just creates a small re-import when the PR merges.

The cost of matching the contract is zero (you'd write the code either way). The benefit is a near-zero-conflict merge when the upstream lands. The cost of *not* matching is having to re-port later, which is more work than doing it right the first time.

## References

- `references/open-model-tool-calls.md` — full text of the Awais catalogue and the JSON repair example
- `references/extended-failure-modes.md` — modes #5–#15 (outer-envelope, numeric-precision, text-noise extraction, string-sentinel coercion), the full 32-case probe grid, and the triage template
- `references/upstream-prs-and-search.md` — open upstream PRs to mirror (Hermes #25346 / #36039, #35129, SGLang #25658, Ollama #16075), captcha-resistant research sources (GitHub REST API, Jina, Brave HTML, HN Algolia), and the "previous session claimed but didn't patch" pitfall checklist
- `references/2026-06-03-session.md` — session transcript + decision log from the audit that shipped modes #16-#17 + content-channel promotion (mode #18); includes the root-cause analysis of why this skill was not loaded and how the meta-pattern keeps recurring. **Read this if you are auditing tool-call repair for the first time in a session that didn't load the skill — it's the "what happened last time you skipped the load check" cautionary tale.**
- `references/m3-think-blocks-2026-06.md` — empirical finding: MiniMax-M3 (and M2.7) DO emit `` blocks when called directly via the OpenAI-compatible endpoint, contradicting the older "M3 doesn't emit reasoning blocks" claim. Includes a working strict-JSONL prompt template and the `max_tokens=4000` minimum requirement.
- `references/mode-19-list-of-dicts.md` — Mode #19: model emits `[{"value": "..."}]` against a `List[str]` schema, downstream `str(c)` fallback renders the dict literal. Silent at runtime; opaque to the user. Element-level inverse of mode #3.
- `scripts/probe_repair_layer.py` — reusable probe driver: imports any module's repair function, runs the 32-case grid (or a custom JSON cases file), classifies each result by tier, and exits nonzero if Tier 1 failures remain
