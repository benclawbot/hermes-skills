# Upstream PRs and captcha-resistant research sources

A note for the next audit session: when the harness repair layer needs
new modes, **check upstream first** before reinventing. The auditing
discipline is "don't ship what already exists upstream" — match the
contract verbatim and your merges stay clean.

## Hermes open PRs relevant to tool-call repair (as of June 2026)

These are *open* PRs targeting the exact failure modes surfaced by the
audits. If you re-audit, check whether they've merged before designing
your own fix.

| PR | Title | Failure mode it fixes | Status |
|---|---|---|---|
| [NousResearch/hermes-agent#25346](https://github.com/NousResearch/hermes-agent/pull/25346) | `fix(run_agent): split concatenated streamed tool-call args` | `{"a":1}{"b":2}` concatenated parallel calls (Gemini-3-flash-preview) | open |
| [NousResearch/hermes-agent#36039](https://github.com/NousResearch/hermes-agent/pull/36039) | Same fix, different PR | (same) | open |
| [NousResearch/hermes-agent#35129](https://github.com/NousResearch/hermes-agent/pull/35129) | `feat(transports): execute tool calls models emit in 'content' (Ollama/Kimi/MiniMax/Gemma)` | Content-channel tool calls (M3 fallback case) | open |
| [sgl-project/sglang#25658](https://github.com/sgl-project/sglang/pull/25658) | `Fix AttributeError in encode_arguments_to_dsml for non-dict JSON values` | `tool_call["arguments"]` is a valid JSON scalar (not dict) | open |
| [ollama/ollama#16075](https://github.com/ollama/ollama/pull/16075) | `parser: avoid premature Gemma4 tool call termination` | Literal `<tool_call|>` marker inside an argument | open |

To check current status: `curl -s "https://api.github.com/repos/NousResearch/hermes-agent/pulls?state=open&per_page=50" -A "Mozilla/5.0" | python3 -c "import json,sys; [print(f\"#{p['number']:>5} [{p['state']}] {p['title'][:80]}\") for p in json.load(sys.stdin)]"`.

## Captcha-resistant research sources

When the friendly-fire search engines (Google, DuckDuckGo, Mojeek) hit
CAPTCHAs, fall back to these in order. They are unauthenticated-friendly
and have no bot detection that throws an anomaly modal at you:

1. **GitHub REST API search** — `https://api.github.com/search/issues?q=<query>&per_page=10`
   - Best for: finding the *exact* open PR or issue addressing the bug
   - Auth: unauthenticated works for low-volume use; rate-limited to 60/hr
   - Use this when you know the *repo* and want bug reports
2. **GitHub REST API repo PR list** — `https://api.github.com/repos/<owner>/<repo>/pulls?state=open&per_page=50`
   - Best for: enumerating open work in a specific codebase
   - Use this to find a PR that *you* should mirror locally
3. **Jina reader** — `https://r.jina.ai/<url>`
   - Best for: reading a specific article cleanly, especially medium/dev.to
   - Returns markdown, no JS required
4. **Bing RSS** — `https://www.bing.com/search?q=<query>&format=rss`
   - Best for: when DuckDuckGo captcha's you and you still want SERP-style results
   - The fallback heuristic depersonalises after a few queries, so results go to "Wikipedia" generic — rotate queries and accept the noise
5. **Brave HTML SERP** — `https://search.brave.com/search?q=<query>`
   - Best for: most captcha-free, but returns client-rendered HTML — grep for `uddg=` and `href=` patterns
   - Works without JS for basic queries
6. **HackerNews Algolia API** — `https://hn.algolia.com/api/v1/search?query=<query>`
   - Best for: when the failure mode is "real production users hit this" — HN comments are brutally specific about reproductions

What to **avoid**:
- Google search — anomaly captcha after 1-2 queries
- DuckDuckGo HTML — anomaly captcha after 1-2 queries
- Mojeek — same
- Startpage — same
- Reddit JSON API (`reddit.com/r/.../comments.json`) — rate-limits unauthenticated hard

## Methodology: "audit finds existing PR"

The four-step dance when a new failure mode appears:

1. **Probe the harness** with an adversarial input (cheap, finds obvious gaps in 5 minutes)
2. **Cross-reference upstream** — `curl -s "https://api.github.com/search/issues?q=<failure-mode-keywords>&per_page=10"` — if a fix exists, adopt its function name + contract verbatim
3. **Read the PR's body and diff** — `curl -s "https://api.github.com/repos/<owner>/<repo>/pulls/<n>/files"` — this is the "designed" version of the fix, including edge cases the original author hit
4. **Audit locally** with the PR's test cases added to your probe grid

Cost in this session: ~10 minutes of curl-driven discovery, vs. ~30 minutes to design from scratch and miss the streaming-integration seam.

## The "previous session claimed but didn't patch" pitfall

Multiple audit sessions have ended with summaries that say "all 196 tests
passing, changes committed" — but `git status` is clean and the file is
unchanged. The cause is usually a session that *described* the changes
without *applying* them (the diff got lost in compaction, the patch
landed in a worktree, etc.).

**Trust signal: the diff, not the prose.**

Before declaring any audit closed:

```bash
git status                                # must show modified files
git diff --stat                            # must show the new lines
git diff -- agent/message_sanitization.py  # must show the actual patch
```

If `git status` is clean and the prose claims a fix was shipped, treat
the work as un-shipped and start fresh. The tests are still in
`test_repair_tool_call_arguments.py`; just re-apply the patch and re-run.
