# MiniMax M2.7 — capabilities, endpoints, and the gotchas that look like key issues

Quick reference for any agent wiring MiniMax M2.7 into a Vite/Vercel app via
the `vercel-api-key-proxy` pattern. Distilled from a real MindDrop integration
(2026-06-24) where two wrong base URLs and a husky auto-fix cost an extra
deploy cycle.

## Endpoints (verified live)

| Region | Base URL | Status |
|---|---|---|
| Global | `https://api.minimax.io/v1` | **WORKS** (correct) |
| China | `https://api.minimaxi.com/v1` | works for some accounts; this agent hit auth layer but never got a 200 — only the .io host returned 200 with a real key |
| Wrong guesses | `https://api.MiniMax.chat/v1`, `https://api.MiniMax.com/v1` | DNS resolves / auth layer reached but returns 401 — looks like a key issue but is the wrong host |

**The 401 "invalid api key" trap:** MiniMax's auth layer returns
`{"error":{"type":"authorized_error","message":"invalid api key (NNNN)"}}`
for THREE different conditions:
1. Key is genuinely wrong / deleted / expired
2. Key is correct but the host is wrong (still routes through auth)
3. Key is for a different account/region

You cannot distinguish these from the status code alone. **Always verify the
base URL is right** before assuming the key is bad. The worked URL is
`https://api.minimax.io/v1` for the global region.

## Model names (from MiniMax's published OpenAPI spec)

- `MiniMax-M3` — latest
- `MiniMax-M2.7` — used by MindDrop, OpenAI-compatible chat ✅
- `MiniMax-M2.7-highspeed`
- `MiniMax-M2.5` / `MiniMax-M2.5-highspeed`
- `MiniMax-M2.1` / `MiniMax-M2.1-highspeed`
- `MiniMax-M2`

## Capabilities matrix

| Feature | M2.7 | Workaround if needed |
|---|---|---|
| Chat completions | ✅ | — |
| JSON mode (`response_format: json_object`) | ✅ | — |
| Function/tool calling | ✅ | — |
| Streaming | ✅ | — |
| System messages | ✅ | — |
| **Realtime audio** (WebSocket/streaming) | ❌ | no API at all; can't be polyfilled |
| **Image generation** | ❌ | not in API; can't be polyfilled |
| **Web search / grounding** (Google Search-style sources) | ❌ | no tool support; drop the feature |
| **Vision input** (image in messages) | ❌ | drop multimodal input |
| **Embeddings** | unclear | not in M2.7 model card; check MiniMax docs for separate embedding model |

**Design rule:** if a product feature requires one of the "❌" rows, push back
on the requirement and propose a text-only alternative. Don't stub the UI with
gray buttons — the user pays for that with confusing UX and dead code paths.
"Image gen button that does nothing" is worse than "no image gen button."

## Request shape (OpenAI-compatible, POST /v1/chat/completions)

```json
{
  "model": "MiniMax-M2.7",
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user",   "content": "..." }
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "response_format": { "type": "json_object" }
}
```

## Response shape (OpenAI-compatible, with one extra)

Standard OpenAI `chat.completion` object, but M2.7 returns an extra
`reasoning_tokens` field under `usage.completion_tokens_details` — this is
the M2.7 thinking-trace token count. It counts against `max_tokens`. If you
set `max_tokens: 20` to test the API, M2.7 burns the budget on thinking
before it ever produces visible text, and the response cuts off mid-thought.
Bump to `max_tokens: 200+` for any test where you want to see actual output.

```json
{
  "id": "068b7032d496d0833398d0cafd1b057c",
  "object": "chat.completion",
  "model": "MiniMax-M2.7",
  "choices": [{
    "finish_reason": "length",
    "message": { "role": "assistant", "content": "...", "name": "MiniMax AI" }
  }],
  "usage": {
    "prompt_tokens": 46,
    "completion_tokens": 20,
    "total_tokens": 66,
    "completion_tokens_details": { "reasoning_tokens": 20 }
  }
}
```

## Verifying a working connection in 1 curl

```bash
curl -s -X POST https://api.minimax.io/v1/chat/completions \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7","messages":[{"role":"user","content":"Reply with exactly: pong"}],"max_tokens":200}'
```

Expected 200 with `choices[0].message.content` containing "pong" (or close to
it — M2.7 may add brief reasoning preamble).

If you get `401 invalid api key` on this URL, the key is the problem.
If you get `404`, the URL is the problem.
If you get `000` (curl exit), DNS is the problem.

## What this file replaces

You don't need to re-derive any of this. If a future session needs to add
another LLM-backed feature to MindDrop or wire a second model into the
`/api/minimax` proxy, the working config is:

- Base URL: `https://api.minimax.io/v1`
- Default model: `MiniMax-M2.7`
- Auth: `Authorization: Bearer $MINIMAX_API_KEY`
- All env vars: server-side only (never `VITE_` prefix)

That's it. The five other facts in this doc (capability matrix, request
shape, response shape, curl test, the 401 trap) are the things that bite
when you assume the same shape as OpenAI's API.
