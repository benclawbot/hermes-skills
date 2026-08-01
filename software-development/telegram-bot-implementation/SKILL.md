---
name: telegram-bot-implementation
description: "Build a Node.js Telegram bot with inline-keyboard approval flows — covers the patterns that bite in practice: sourcing the bot token from the platform's own env (Hermes's ~/.hermes/.env), resolving the chat id safely (never fall back to TOKEN.split(':')[0] — that DM's the bot itself, 403), MarkdownV2 escaping (template-literal \\= is silently dropped, need \\\\) for the literal backslash), pre-send + post-send keyboard validation (Telegram's 64-byte callback_data cap, silent reply_markup stripping on parse_mode rejection), the strip-keyboard lifecycle after approve/dismiss/modify, and the let-binding shadow trap when helper functions are defined at module top-level. Trigger when writing or debugging a Telegram bot that sends messages with inline_keyboard, uses callback_query handlers, or shares bot identity with another platform process."
metadata:
  hermes:
    tags: [telegram, bot, inline-keyboard, callback-query, markdownv2, hermes, node-telegram-bot-api]
    category: software-development
---

# Telegram Bot Implementation (Node)

Pitfalls and patterns for shipping a Telegram bot that uses inline_keyboard
buttons — the kind that drives approval flows, digests, and decision surfaces
in Hermes-style systems.

## 0. Source the bot token from the platform's own env, not a side `.env`

If the bot shares identity with another process (Hermes's gateway, a sister
service, the user's automation stack), that process already stores
`TELEGRAM_BOT_TOKEN` and `TELEGRAM_HOME_CHANNEL` in *its* env file. Don't
demand a duplicate token; read theirs.

```js
import dotenv from "dotenv";
import os from "node:os";
import path from "node:path";

// Platform env first (canonical). Local env second (override for sandbox).
dotenv.config({ path: path.join(os.homedir(), ".hermes", ".env"), override: true });
dotenv.config({ path: path.join(os.homedir(), ".memory", ".env"), override: true });
```

User signal: "I told you 10 times to use Hermes bot token for this" — the
lesson is *don't ask for a new token, source the existing one*. If the user
mentions a platform name (`hermes`, `homeassistant`, `kanban`) and the bot
will live alongside it, check `~/.<platform>/.env` first.

## 1. Resolve the destination chat id safely — never `TOKEN.split(":")[0]`

The token's first segment (`855123456:AAH...` → `855123456`) is the bot's own
numeric user id. Sending there yields:

```
ETELEGRAM: 403 Forbidden: the bot can't send messages to the bot
```

Resolution hierarchy (highest priority first):

```js
const CHAT_ID =
  process.env.TELEGRAM_HOME_CHANNEL ??   // Hermes canonical
  process.env.TELEGRAM_CHAT_ID ??        // explicit
  process.env.TELEGRAM_USER_ID ??        // direct DM
  null;

if (!CHAT_ID) {
  console.error("Set TELEGRAM_HOME_CHANNEL (or TELEGRAM_CHAT_ID) in ~/.hermes/.env");
  process.exit(1);
}
```

Refuse to start without a real chat id. The "self-DM fallback" is never what
the user wants.

## 2. MarkdownV2 escape — template-literal `\=` is silently dropped

Telegram MarkdownV2 reserved chars (outside code/entities) are:
`_ * [ ] ( ) ~ \` > # + - = | { } . ! \`

JS template literals: `\=`, `\|`, `\.` are *not* recognized escapes — the
backslash is silently dropped. Verify:

```js
const t = `confidence\=85%`;
console.log(t);            // "confidence=85%"  ← no backslash!
console.log(JSON.stringify(t));  // "\"confidence=85%\""  ← confirms
```

Fix: **double the backslash** in source so the runtime string contains one
literal `\`:

```js
const t = `confidence\\=85% \\| sessions\\=7`;
// runtime:  "confidence\=85% \| sessions\=7"
```

Or use a dedicated escape helper that takes a *string* and rewrites it
post-construction (no template-literal trap):

```js
function escapeMd(s) {
  return String(s ?? "").replace(/([_*\[\]()~`>#+\-=|{}.!\\])/g, "\\$1");
}
```

The `escapeMd` form is safer for user-controlled text; the `\\=` form is
fine for static label strings you control.

## 3. Inline-keyboard validation — pre-send AND post-send

Telegram enforces a 64-byte hard cap on `callback_data`. If you exceed it,
`sendMessage` fails with `BUTTON_DATA_INVALID` and the message arrives
without any keyboard — the user has no way to interact.

**Pre-send assertion** (before any round-trip):

```js
const TELEGRAM_CALLBACK_DATA_MAX = 64;
function assertKeyboardValid(keyboard, rowId) {
  for (const row of keyboard.inline_keyboard) {
    for (const btn of row) {
      if (typeof btn.callback_data !== "string") {
        throw new Error(`Button "${btn.text}" missing callback_data (proposal ${rowId})`);
      }
      const bytes = Buffer.byteLength(btn.callback_data, "utf8");
      if (bytes > TELEGRAM_CALLBACK_DATA_MAX) {
        throw new Error(
          `Button "${btn.text}" callback_data is ${bytes}B, exceeds ` +
          `Telegram's ${TELEGRAM_CALLBACK_DATA_MAX}B cap (proposal ${rowId})`
        );
      }
    }
  }
}
```

**Post-send self-check** (Telegram sometimes silently strips `reply_markup` —
notably when `parse_mode` rejects the body, the message is re-sent plain
and the keyboard is dropped):

```js
const msg = await bot.sendMessage(CHAT_ID, text, { parse_mode: "MarkdownV2", reply_markup: keyboard });
if (!msg?.reply_markup?.inline_keyboard?.length) {
  console.error(`⚠️ Telegram returned a message with NO inline_keyboard for ${rowId}. ` +
    `Buttons are dead. Likely cause: parse_mode rejected the text.`);
}
```

The pre-send assert catches the bytes. The post-send check catches the
silent parse_mode downgrade. Together they convert "dead button, user
complains later" into "loud error, you fix it now."

## 4. Strip keyboard lifecycle — and the `telegram_msg_id` fallback

After approve/dismiss/modify, strip the inline_keyboard from the sent
message so the buttons don't linger as dead UI. Use `editMessageReplyMarkup`
with an empty `inline_keyboard`.

`node-telegram-bot-api` v1.x sometimes delivers `callback_query` events
with a partial `query.message` (no `chat.id` / `message_id`). When this
happens, `editMessageReplyMarkup` returns:

```
ETELEGRAM: 400 Bad Request: message identifier is not specified
```

**Resilient `stripKeyboard`** — fall back to the message id persisted in
the DB at send time:

```js
async function stripKeyboard(chatId, msgId, proposalId) {
  let resolvedChatId = chatId;
  let resolvedMsgId = msgId;

  // Fallback: pull the message id we recorded at send time.
  if ((!resolvedChatId || !resolvedMsgId) && proposalId) {
    const row = db.prepare(`SELECT telegram_msg_id FROM proposals WHERE id = ?`).get(proposalId);
    if (row?.telegram_msg_id) {
      resolvedChatId ??= CHAT_ID;
      resolvedMsgId = row.telegram_msg_id;
    }
  }

  if (!resolvedChatId || !resolvedMsgId) return;  // nothing to strip
  if (!bot) return;
  try {
    await bot.editMessageReplyMarkup(
      { chat_id: resolvedChatId, message_id: resolvedMsgId },
      { inline_keyboard: [] }
    );
  } catch (err) {
    const msg = String(err?.message ?? "");
    if (
      msg.includes("message is not modified") ||
      msg.includes("message identifier is not specified") ||
      msg.includes("message to edit not found")
    ) {
      return;  // benign — already stripped, gone, or stripped twice
    }
    console.warn(`Could not strip keyboard: ${msg}`);
  }
}
```

**At send time, persist the message id** so the fallback works:

```js
const msg = await bot.sendMessage(CHAT_ID, text, { reply_markup: keyboard });
if (msg?.message_id) {
  db.prepare(`UPDATE workflow_proposals SET telegram_msg_id = ? WHERE id = ?`)
    .run(msg.message_id, row.id);
}
```

## 5. `let bot` shadowing — module-level vs function-level

If helper functions (`sendProposal`, `stripKeyboard`, `handleCallback`)
reference `bot` but the variable is declared as `let bot = null` *inside*
`main()`, the helpers see `null` (or the global `bot` if one exists) — not
the `bot` instance `main()` just constructed.

The trap:

```js
// BAD — helpers reference module-level `bot` (which is `undefined`!)
let bot = null;  // wait, no — this is also broken
async function sendProposal(row) {
  await bot.sendMessage(...);  // ReferenceError: bot is not defined
}

async function main() {
  let bot = null;  // ← shadows the module-level one
  bot = new TelegramBot(TOKEN, { polling: true });
  await sendProposal(row);  // reads module-level bot (undefined), not the local
}
```

Fix: **declare once, at module level**, and let `main()` assign it:

```js
// Module-level
let bot = null;
async function sendProposal(row) { await bot.sendMessage(...); }
async function stripKeyboard(...) { if (!bot) return; ... }

async function main() {
  if (!DRY_RUN && !APPROVE_ALL) {
    const { default: TelegramBot } = await import("node-telegram-bot-api");
    bot = new TelegramBot(TOKEN, { polling: true });  // assigns module-level
  }
  // helpers now see the right instance
}
```

If you need a sentinel before `main()` runs (e.g. for lazy imports or
top-level re-exports), initialize at module level: `let bot = null;`.

## 6. `--dry-run` vs `--approve-all` vs live mode — gate all three correctly

A common bug: the gate says `if (!DRY_RUN)` for "no Telegram needed", but
`--approve-all` doesn't use Telegram either. Result: `--approve-all` is
refused (token not set), or worse, the bot is instantiated and spins
spamming `EFATAL: Telegram Bot Token not provided!` at 1 Hz.

```js
if (!TOKEN && !DRY_RUN && !APPROVE_ALL) {
  console.error("Set TELEGRAM_BOT_TOKEN in ~/.hermes/.env (or ~/.memory/.env)");
  console.error("  pass --dry-run to preview proposals without sending");
  console.error("  pass --approve-all to skip Telegram and write skills directly");
  process.exit(1);
}

let bot = null;
if (!DRY_RUN && !APPROVE_ALL) {
  const { default: TelegramBot } = await import("node-telegram-bot-api");
  bot = new TelegramBot(TOKEN, { polling: true });
}

await poll();
if (DRY_RUN) return;
if (APPROVE_ALL) return;   // ← one-shot: do NOT enter the polling loop
setInterval(poll, 60_000);
```

The `if (APPROVE_ALL) return;` is the load-bearing line — without it,
`--approve-all` enters the polling loop and the bot tries to do Telegram
things on a 1-minute cadence.

## 7. Verify with a real round-trip, not a dry-run print

A `--dry-run` that prints formatted text proves the formatting code works.
It does NOT prove:
- The Telegram API accepts the message (parse_mode can reject)
- The keyboard survives the round-trip (Telegram can drop reply_markup)
- The callback_query event fires and routes to the right handler
- The DB transition completes and the file write succeeds
- The stripKeyboard on the sent message works (need the real chat_id)

The minimum live verification:

1. Seed one real proposal in the DB.
2. Start the bot with the real token + chat id.
3. Tail the log: confirm `[bot] Sent proposal: <title> (msg_id=N)`.
4. Confirm no parse errors (`can't parse entities`).
5. Click ✅ in Telegram. Confirm `[bot] Callback: approve <id>`.
6. Confirm DB row is `status='approved'`.
7. Confirm the side-effect file was written (e.g. `SKILL.md`).
8. Confirm `stripKeyboard` ran (look for the edit-message call or the
   benign-fallback log).

If you can't do step 3+ (no token, no Telegram, wrong chat id), say so
explicitly. Don't claim the bot "works" because the dry-run formatted
text.

## Common mistakes (from real sessions, 2026-06-15)

- **Reached for `better-sqlite3` and the prebuild ABI mismatched Node 22**
  → see `node-sqlite-shim` skill. Always reach for `node:sqlite` first on
  Node 22.5+.
- **JSON columns came back as raw TEXT** (`(row) => row.steps` is a string,
  not an array) → `parseJsonCols` helper at the read site. See
  `node-sqlite-shim` → Subtlety #0.
- **Inline-script quoting bit the seed test** (the `\` in `When user says
  "test"` was interpreted as a line continuation in a bash heredoc) →
  write to `/tmp/seed.mjs` with `write_file`, run with `node /tmp/seed.mjs`.
  Don't try to embed SQL with quotes in a one-liner.
- **LSP error about missing `}` is a phantom after a partial edit** → run
  `node --check <file>` to confirm parse, then re-read the suspected
  region. LSP can lag the actual file state by a few seconds.
- **Background process log appears empty when piped through `tee`** when
  the inner process doesn't flush stdout. Workaround: redirect to a file
  (`> /tmp/bot.log 2>&1`), then `cat` it from a separate terminal call.
- **DB column not in the schema, error says "no such column: feedback"** →
  `PRAGMA table_info(<table>)` to see what's actually there. Don't trust
  memory of the schema; the previous session's seed may have left a
  different shape.
- **`Failed to send message: bot is not defined` masks a TDZ error above it.**
  A top-level guard that reads `if (!CHAT_ID && !DRY_RUN && !APPROVE_ALL)`
  will throw `ReferenceError: Cannot access 'DRY_RUN' before initialization`
  if `DRY_RUN` / `APPROVE_ALL` are declared further down the file. The
  `main().catch(...)` at the bottom of the file swallows the real TDZ and
  prints a secondary error from a *later* failed line (e.g. the lazy
  `await import("node-telegram-bot-api")` constructor reaching for a
  `bot` that's still in TDZ). **Order rule:** declare all
  `process.argv.includes(...)` flags and `process.env.*` reads *before*
  any guard that references them. **Diagnostic rule:** when a `Fatal:`
  message names an unrelated line, suspect the file's declaration order,
  not the named line. `node --check <file>` confirms syntax; only an
  actual run surfaces TDZ.
- **Inconsistent constant naming across the file breaks every call site.**
  Declaring `const Proposals_PATH = ...` and then calling it as
  `PROPOSALS_PATH` in some helpers (or vice versa) yields
  `ReferenceError` at the first call. JS hoists `const`/`let` *names*
  but not their values into TDZ, so the error is consistent per call
  site — not a flaky crash. **Rule:** pick one name, use it everywhere
  in the same file, and grep before commit:
  `rg "Proposals_PATH|PROPOSALS_PATH" hub/telegram/bot.mjs` should show
  one consistent form.

## Verification checklist

- [ ] `node --check bot.mjs` returns "PARSE OK"
- [ ] `--dry-run` prints the proposal with proper MarkdownV2 escaping
      (look for `\|`, `\=`, `\.` in the raw output)
- [ ] `--approve-all` writes the side-effect file and marks the DB row
      `approved` *without* spinning up a bot or polling loop
- [ ] `assertKeyboardValid` test: oversized `callback_data` is rejected
      with a clear error
- [ ] Live bot with real token sends a message; the returned
      `msg.reply_markup.inline_keyboard` is non-empty (post-send assertion
      passes)
- [ ] Click ✅ in Telegram → DB row → `approved`, side-effect file
      written, `stripKeyboard` either succeeds or hits a known-benign
      fallback (not an unhandled error)
- [ ] `CHAT_ID` is set to a real value (not the bot's own id from
      `TOKEN.split(":")[0]`)

## Related skills

- `node-sqlite-shim` — use Node 22.5+ `node:sqlite` for zero-dep SQLite
- `self-improvement-loop` → "Inline-keyboard decision flow 2026-06-08" —
  the `callback_data` schema, polling offset persistence, and Modify
  semantics for the SRI loop's approval surface
- `build-spec-workflow` — implementing an external repo/spec (the Omni-Memory
  hub was ported to the Macbook Air following this skill)
- `test-what-you-built` → "Multi-surface audit" — when changing the env
  var or path conventions here, audit the cron jobs, scripts, and other
  skills that reference them

## References

- `references/omni-memory-hub-2026-06-15.md` — the original session
  reference: env-var precedence, MarkdownV2 escaping, stripKeyboard
  resilience, let-binding shadow trap, TDZ on argv flags, camelCase
  constant naming
- `references/html-effectiveness-pattern.md` — when building a Telegram
  flow that ships LLM-generated HTML artifacts (specs, reports, build
  plans), use the thariqs/html-effectiveness catalog as the design
  anchor. The implementation-plan template (`16-implementation-plan.html`)
  is the canonical shape for spec-style output. Single LLM call →
  single self-contained HTML file, no image gen, no JS required.
