# Vendor Swap in a Deployed SPA

The "swap one vendor API for another in a static frontend" pattern — most often
triggered by "switch from X to Y" requests for AI providers, auth, storage, or
analytics. Distinct from a full port (no platform change) and from extension
(new modules added). The challenge is that the existing code is wired around
the old vendor's shape (auth methods, snapshot listeners, vendor-specific AI
features), and the new vendor has a different surface — sometimes with gaps.

## When this applies

Triggers that should pull this reference:

- "Switch from Gemini to M2.7 / OpenAI / Claude"
- "Move from Firebase to Supabase / localStorage / PocketBase"
- "Replace Auth0 with Clerk / workos"
- "Use a different LLM provider / endpoint"
- "Use OAuth for [X] instead of API keys" (usually a bad request — see §3)

The shape is always: a deployed frontend that calls vendor X's API at runtime,
with the vendor's client SDK in `package.json` and the vendor's API shape
inlined across components.

## The 4-phase shape

### Phase 1 — Feature parity audit (BEFORE writing any code)

The new vendor is rarely a 1:1 replacement. The old vendor may have features
the new one doesn't, and components may depend on those features even if it
doesn't look like it at first glance.

**The audit:**

1. Enumerate every distinct *capability* the old vendor is used for. Don't
   list API methods — list capabilities. Examples: "text generation with JSON
   schema", "realtime audio transcription", "image generation", "vector search",
   "cross-tab realtime sync".
2. For each capability, mark: **Direct equivalent** / **Workable substitute** /
   **No equivalent (drop)**.
3. Find which components depend on the "drop" capabilities. Search the
   codebase, don't trust the README or your memory.

**Why this matters:** the user often says "just swap it" without realizing
that a feature they use is vendor-specific (Google Search grounding, live
audio, image gen, OAuth with the vendor's own product). If you skip the
audit, you'll ship a half-broken app and discover the missing piece when the
user clicks a button.

**For MiniMax M2.7 (and most text-only OpenAI-compatible APIs):**

| Old (Gemini) | New (M2.7) | Action |
|---|---|---|
| `models.generateContent` with JSON schema | `chat.completions` with `response_format: { type: "json_object" }` | Direct |
| `getTaskChatSession` (stateful chat) | Per-turn `chat()` call with history array | Drop the session helper, stateless calls work |
| `googleSearch` tool / `groundingChunks` | No tool calling for web search | Drop the sources field, return `[]` |
| `ai.live.connect` (realtime audio) | No realtime API | Drop the feature entirely (UI + service) |
| `generateContent` with image output | No image gen | Drop the feature, keep upload UI offline-only |

**Output of Phase 1:** a list of "drop, keep, transform" decisions. Do not
write code until the user has signed off on this list — especially the drops.
Each drop is a feature the user thought they were keeping.

### Phase 2 — Vendor client + service rewrite

**Write a single new client file** (e.g. `services/minimax.ts`) that wraps
the new vendor's API in the same shape your components expect. Don't leak
the vendor's API shape (model name magic strings, response field names)
into the rest of the codebase — components shouldn't know whether the
backend is MiniMax, OpenAI, or Anthropic.

```ts
// services/<vendor>.ts — keep it small
const API_KEY = (import.meta.env.VITE_<VENDOR>_API_KEY as string) ?? '';
const BASE_URL = (import.meta.env.VITE_<VENDOR>_BASE_URL as string) ?? '<default>';
export const MODEL = (import.meta.env.VITE_<VENDOR>_MODEL as string) ?? '<default-model>';

export const chat = async (messages, options) => { /* vendor call */ };
export const chatJSON = async <T>(messages, options) => { /* parse + throw on bad JSON */ };
```

**Then rewrite the existing service file** (e.g. `services/ai.ts`) to import
from the new client. Each function in the service file preserves the same
exported signature so React components don't change. Internal prompts and
JSON schemas may need light edits because:

- New vendor may not have the same response shape (Gemini returns `response.text`,
  OpenAI-compatible returns `choices[0].message.content`).
- JSON schema syntax may differ (Gemini uses `Type.OBJECT` from `@google/genai`,
  OpenAI-compatible uses `response_format: { type: "json_object" }` and the
  model infers shape from the prompt).

### Phase 3 — UI surface changes for dropped features

If you dropped a feature in Phase 1, the UI must reflect that. Three patterns,
ranked by cleanliness:

1. **Delete the UI entirely** (button, panel, modal). Cleanest, no stubs.
   Use this when the feature has no substitute.
2. **Gray-out + tooltip** ("Not supported in this build"). Use this when
   the user explicitly wants the affordance preserved but is OK with
   non-functionality.
3. **Stub that throws a clear error**. Never. Stubs that look functional
   but aren't are worse than no UI.

For the MindDrop swap, the voice button and image-gen UI were deleted
entirely (pattern 1) — M2.7 has no equivalent. The image upload in
`NewTaskInput` was kept but the image is no longer passed to the AI; it
just becomes a local attachment. That's a pattern-1.5 — the UI is
preserved for user workflow but the AI is not called on the bytes.

### Phase 4 — Storage migration, env vars, type defs

**Env vars:** add a `.env.example` and update the user's `.env.local`. Use
the `VITE_*` prefix so Vite exposes them to the client (and the
`import.meta.env` types resolve). Vite's `loadEnv` only picks up `VITE_*`
by default — anything else is `undefined` at build time.

**Type defs:** if you use `import.meta.env.<X>`, add `"vite/client"` to
`tsconfig.json`'s `types` array. Without it, `import.meta.env` is
`any`-typed and every reference produces a TS2339 error.

**Dependencies:** drop the old vendor's SDK from `package.json` and
`node_modules`. Always clean reinstall: `rm -rf node_modules package-lock.json
&& npm install`. A half-installed `node_modules` produces phantom
typecheck errors that vanish after the clean reinstall.

**Storage keys:** if you also swapped the persistence layer (Firestore →
localStorage), keep the same `minddrop-tasks-${uid}` key shape so
already-saved data still loads. Cross-tab sync is one `window.addEventListener('storage', ...)`.

## The pushback reflex (when the user requests a wrong vendor)

**If the user requests a vendor that doesn't fit a static SPA, push back
in the same turn with engineering reasoning, not later.** Three common
wrong requests:

- **"Use ChatGPT OAuth"** — OAuth for ChatGPT is account-bound (routed
  to the user's ChatGPT session). There's no documented flow for "OAuth
  token → arbitrary `/v1/chat/completions` call". A vendor API key
  (`VITE_OPENAI_API_KEY`) is the right pattern; OAuth is the wrong one.
- **"Use Firebase Auth for the SPA"** — costs latency, adds an auth
  pop-up that breaks the local-first UX the user is asking for.
- **"Use a vendor that does X and Y"** — sometimes the user assumes a
  vendor has a capability it doesn't (M2.7 has no image gen, no realtime
  audio). Check the docs, not your memory.

The pushback template (Telegram-friendly, 1-question-at-a-time default):

> *"[Vendor] doesn't fit this deployment because [one-sentence engineering
> reason]. [Better path] does [what they actually need] and [one-sentence
> why]. Going with [better path] — say if you want me to stop."*

Don't ask "is this OK?" — that triggers the user into agreeing. State the
default, do the work, surface the one place where you actually need a
decision. The user can interrupt; they don't need a menu.

## Real worked example (2026-06-24, MindDrop → MiniMax + localStorage)

**Before:** MindDrop used `@google/genai` for AI features (text + voice +
image gen) and `firebase` for auth + Firestore. Auth was bypassed in an
earlier turn, so the auth half was already done.

**Request:** "Use MiniMax M2.7 instead of Gemini. Store locally instead
of Firebase if it makes sense." (Then later: "Use ChatGPT OAuth instead"
— pushed back on, user accepted M2.7 path.)

**Feature parity audit:**

| Old | New | Decision |
|---|---|---|
| Gemini text + JSON | M2.7 OpenAI-compatible | Direct equivalent |
| Gemini voice (live audio) | None | **Drop**, remove voice button + modal |
| Gemini image gen | None | **Drop**, no UI to begin with (`generateTaskImage` was never called) |
| Google Search grounding | None | **Drop**, return `[]` for sources |
| Firestore | localStorage | Local-first, same key shape, cross-tab `storage` event |
| Firebase Auth | None | Already bypassed in earlier turn |

**Files changed (13):** 2 new services (`minimax.ts`, `storage.ts`), 1
service rewritten (`ai.ts`), 4 deleted (`firebase.ts`, `gemini.ts`,
`VoiceAssistant.tsx`, `AuthView.tsx`, `useAuth.ts`), 5 patched
(`App.tsx`, `useTasks.ts`, `hooks/index.ts`, `package.json`,
`tsconfig.json`, `vite.config.ts`), 1 new file (`.env.example`).

**Bundle size impact:** 1052 KB / 244 KB gzip → 254 KB / 74 KB gzip
(76% reduction). Firebase SDK + Gemini SDK were massive; MiniMax uses
plain `fetch`.

**Verification:**

- `tsc --noEmit` → exit 0 (after adding `vite/client` to types and
  `@types/node` to devDependencies — both required by the swap)
- `npm run build` → exit 0
- `npm run lint` → exit 0 (1 pre-existing `prefer-const` error in
  NewTaskInput, not from this swap)
- Dev server live at :5173, HTTP 200
- Live-served App.tsx: 0 Firebase/Voice refs, 9 new hook calls

## Common pitfalls specific to vendor swaps

- **LSP errors inside `/* ... */` blocks ≠ `tsc` errors.** The in-process
  LSP flags `Cannot find name 'Foo'` even when `Foo` is inside a
  JSDoc-style block comment. The real `tsc --noEmit` treats `/* */` as a
  comment and skips it. When typecheck "fails" with names-from-comments
  errors, the *real* cause is usually missing types in `node_modules`,
  not the commented imports. Verify by `git stash` → re-run typecheck →
  compare counts.

- **A half-installed `node_modules` produces phantom typecheck errors.**
  Symptom: `tsc` reports 20+ `Cannot find module 'X'` errors for modules
  that ARE in `package.json`. First fix attempt is `npm install` — which
  fails with `ENOTEMPTY: directory not empty, rename '.../acorn'`. The
  only reliable recovery: `rm -rf node_modules package-lock.json
  && npm install`. Always clean-reinstall before assuming a real
  typecheck failure.

- **Stale call signatures leak through.** When the old service had a
  3-arg function (`analyzeNewTask(title, desc, imageBase64)`) and you
  rewrite to 2-args because the new vendor doesn't support images, the
  caller still passes 3 args. Search for the old signature, not just
  the new one. `grep -rn "analyzeNewTask(" src/` catches callers.

- **`process.env.X` vs `import.meta.env.VITE_X`.** Vite serves
  `import.meta.env.VITE_*` to the client and `process.env.*` is the
  Node-only path. If your service file is imported by both the SPA and
  a Vite plugin / script, use `import.meta.env`. The `vite.config.ts`
  `define` block can pre-define `process.env.X` for the build, but the
  canonical Vite pattern is `import.meta.env.VITE_X`.

- **LSP exit codes can lie through `npm` wrappers.** When you run
  `npx tsc --noEmit; echo $?`, you get the real exit. When you run
  `npm run typecheck; echo $?`, npm sometimes masks tsc's exit on
  certain warnings-as-errors configs. Always check via `npx tsc
  --noEmit` directly when you suspect the wrapper is hiding the truth.
