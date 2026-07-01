---
name: vercel-api-key-proxy
description: "Serverless proxy pattern for keeping third-party API keys (MiniMax, OpenAI, Anthropic, etc.) out of public Vercel bundles. Use when a Vite/React app needs to call a paid LLM API and the key would otherwise ship in client JS. Covers the /api/*.ts serverless function pattern, MINIMAX_API_KEY vs VITE_MINIMAX_API_KEY distinction, CORS, vercel env add, the husky lint-staged auto-fix trap, and the 401-vs-wrong-host diagnostic trap. See references/minimax-capabilities.md for the working MiniMax endpoints, model names, and capability matrix."
version: 1.0.0
author: Hermes Agent (Thomas)
license: MIT
metadata:
  hermes:
    tags: [vercel, serverless, api-proxy, secrets, vite, llm]
    category: software-development
---

# Vercel API Key Proxy Pattern

When a Vite/React app deployed to Vercel needs a paid third-party API key
(MiniMax, OpenAI, Anthropic, etc.), **never use `VITE_*` prefixed env vars**
for that key — Vite bundles them into `dist/assets/*.js` and ships them to
every visitor. A public bundle with a paid API key is a billing risk.

The fix: a serverless proxy under `/api/` that holds the key server-side.

## When to use this

- Vite/React app deployed to Vercel
- Calls a paid third-party API (LLM, image gen, etc.) from the browser
- `VITE_API_KEY` / `VITE_OPENAI_API_KEY` / `VITE_MINIMAX_API_KEY` would
  otherwise ship in the client bundle
- You want production-billing-safe deployment without spinning up a separate
  backend

## The pattern

```
[Browser]
   │
   │ POST {messages, ...}     ← no API key here
   ▼
/api/minimax  (Vercel serverless function)
   │
   │ Authorization: Bearer $MINIMAX_API_KEY  ← key read server-side
   ▼
MiniMax API
```

## Three things to write

1. **`api/<service>.ts`** — the serverless function. Vercel auto-detects
   files under `/api/` as endpoints. The key is read from
   `process.env.<NAME>` (no VITE prefix, so it stays server-side).

2. **`src/services/<service>.ts`** — the browser client. No `import.meta.env`
   reads. Just `fetch('/api/<service>', { method: 'POST', body: ... })`.

3. **`.env.example`** — documents the server-side env var.

## Skeleton

**api/minimax.ts:**
```ts
import type { VercelRequest, VercelResponse } from '@vercel/node';

const KEY = process.env.MINIMAX_API_KEY ?? '';
const BASE = process.env.MINIMAX_BASE_URL ?? 'https://api.example.com/v1';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', process.env.ALLOWED_ORIGIN || '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  if (!KEY) return res.status(500).json({ error: 'API key not configured on server' });

  const upstream = await fetch(`${BASE}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${KEY}` },
    body: JSON.stringify(req.body),
  });
  const text = await upstream.text();
  return res.status(upstream.status).send(text);
}
```

**src/services/minimax.ts:**
```ts
export const chat = async (messages, options) => {
  const res = await fetch('/api/minimax', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, ...options }),
  });
  if (!res.ok) throw new Error(`Proxy ${res.status}`);
  return res.json();
};
```

**vite.config.ts** — proxy `/api` to the vercel dev server (port 3000) so
`npm run dev` works without `vercel dev`:
```ts
proxy: {
  '/api': { target: 'http://localhost:3000', changeOrigin: true },
}
```

## Setting the env vars on Vercel

```bash
vercel link                    # if not already linked
vercel env add MINIMAX_API_KEY production   # paste when prompted
vercel env add MINIMAX_API_KEY preview
vercel env add MINIMAX_API_KEY development
```

Names are **plain** (`MINIMAX_API_KEY`), not `VITE_MINIMAX_API_KEY`. The
`VITE_` prefix tells Vite to bundle the value into the client; without it,
the value is only available server-side.

## Verifying the bundle is clean

After `npm run build`, scan `dist/assets/*.js` for key patterns:
```bash
grep -E "Bearer\s+[A-Za-z0-9]|sk-[a-zA-Z0-9]{20,}|cr_[a-zA-Z0-9]{20,}" dist/assets/*.js
```
Empty output = no leaked keys.

## Pitfalls

- **`VITE_` prefix = bundled to client.** This is the #1 mistake. If you see
  the key in `dist/assets/*.js` after a build, the prefix is wrong.
- **`process.env` reference in client code without `VITE_` is `undefined` at
  runtime.** The `define:` block in `vite.config.ts` only replaces prefixed
  vars.
- **`@vercel/node` types** — add `"@vercel/node": "^3.0.0"` to dependencies
  for the `VercelRequest` / `VercelResponse` types.
- **`vercel dev` may fail to link repo-based projects** with "Could not
  retrieve Project Settings". Production deployment is unaffected — Vercel
  routes `/api/*` to `/api/*.ts` automatically on deploy.
- **CORS** — set `ALLOWED_ORIGIN` to your production domain in prod, leave
  `*` for dev. Browsers block cross-origin POSTs without it.
- **Local dev without `vercel dev`** — `npm run dev` alone serves Vite but
  not the serverless functions. Either use `vercel dev` (slower boot) or add
  the Vite `/api` proxy block above so `/api/*` requests forward to whatever
  is listening on `:3000`.
- **Husky `lint-staged` can silently rewrite your source.** The pre-commit
  hook runs `eslint --fix` and `prettier --write` on staged files — it can
  reformat a file in a way that drops a const declaration, merges an import
  with the next line, or rewrites a string. If `npm run build` fails
  immediately after a `git commit`, the cause is almost always lint-staged.
  Re-read the file with `cat` before assuming you typed it wrong. To bypass
  for one commit: `git -c core.hooksPath=/dev/null commit -m "..."` — this
  is a valid one-time escape hatch, not a habit. Better fix long-term:
  tighten the husky config so its auto-fixes never drop declarations.
- **Wrong vendor URL = 401, not 404.** MiniMax's API returns
  `{"type":"error","error":{"type":"authorized_error","message":"invalid api
  key (NNNN)"}}` for a wrong key, a deleted key, OR a request to the wrong
  host that still reaches MiniMax's auth layer. Two different "wrong URL"
  scenarios both return 401 — you can't distinguish "host is wrong" from
  "key is wrong" by status code alone. **Always verify the base URL**
  against an existing reference (`~/.hermes/.pi/skill-memory.json`, a
  working config file, or the vendor's own published OpenAPI spec) BEFORE
  declaring the key invalid. See `references/minimax-capabilities.md` for
  the working endpoints, model names, and the gotchas that look like key
  issues but aren't.

## Why this matters

A Vite env var like `VITE_OPENAI_API_KEY` is replaced at build time with
the literal string and shipped in `dist/assets/*.js`. Anyone who opens
devtools can grep the bundle for the key. For paid APIs, that's an open
billing tap. The proxy pattern costs ~25 lines and keeps the key on
infrastructure you control.