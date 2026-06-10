# M3 emits `` blocks in practice (2026-06-07, self-recursive-improvement session)

The current SKILL.md says "M3 routes through Anthropic-format and M3 itself doesn't currently emit reasoning blocks." This was an overclaim.

**Empirical finding:** Calling MiniMax-M3 directly via `https://api.minimax.io/v1/chat/completions` with a strict-JSONL prompt produced a multi-thousand-token ``...`` block before the final JSON. The block contained step-by-step reasoning about the user's request, the rubric, and proposed candidates, then a single JSON object on the last line.

**Same finding for the strict-JSON judge call to MiniMax-M2.7.** The judge is a smaller/older model but it does the same.

**Implication:** Any direct (non-Hermes) call to the M-series models for strict-JSON output **must** run the `_extract_json_from_text` pre-pass or an equivalent `re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)` before the JSONL parse. Failure mode if you skip it: the parse tries to extract JSON from inside the `` block, gets confused by `{` chars in the prose, and reports 0 valid proposals even when the model did produce one.

**Update for the SKILL.md "Commercial vs. open model contracts" section:**

Replace the line "M3 routes through Anthropic-format and M3 itself doesn't currently emit reasoning blocks" with "M3 routes through Anthropic-format but **does** emit `` blocks in `content` when the prompt asks for structured output. The pre-pass (modes #9–12) is required for direct (non-Hermes) M3 calls, not just for open-weight sub-agents."

**The proposed prompt template that worked in this session** (in case future sessions need it):

```
## Output format (strict, non-negotiable)

For each proposal, emit a JSON object on its own line. NO OTHER TEXT
in the output — no markdown commentary, no preamble, no explanation
of your reasoning. The cron parser will fail on anything that isn't
valid JSON.

If you have multiple proposals, emit one JSON object per line.
If you have none, emit exactly one line: `{"no_proposals": true, "reason": "..."}`.

The final line of your response MUST be valid JSON.
```

**Pair with `max_tokens=4000` minimum.** The M3 model can spend 2500+ tokens on reasoning before emitting the JSON. Setting `max_tokens=2000` silently truncates the JSON output and the parse returns 0 valid proposals with no error.
