# Omni-Memory Hub on MacBook Air — worked fix log (2026-06-15)

End-to-end port of `benclawbot/Omni-Memory` (a cross-agent skill-distribution
hub) onto the local MacBook Air, with a working Telegram approval bot. This
file condenses the actual chain of bugs found and fixed; load it when
debugging a similar hub-style daemon.

## Stack landed

- Node.js 22.22.2 (built-in `node:sqlite`, no `better-sqlite3`)
- `node-telegram-bot-api` v1.1.0 (sourcing token from `~/.hermes/.env`)
- `dotenv` for env layering (hermes canonical, memory local override)
- ~100-line `sqlite-shim.mjs` backed by `node:sqlite`

## Bugs encountered (in order)

1. **`better-sqlite3` prebuild ABI mismatch** — `npm install` downloaded
   prebuild for Node 23 (`NODE_MODULE_VERSION 137`), host was Node 22 (`127`).
   `npm rebuild --build-from-source` hit the 600s timeout. Fix: pivoted
   to built-in `node:sqlite` via the shim. See `node-sqlite-shim` skill.

2. **`node:sqlite` returns raw TEXT for JSON columns** — `proposal.steps`
   came back as the literal string `'["a","b"]'`, not `["a","b"]`.
   `handleApprove` did `(proposal.steps ?? []).map(...)` and threw
   `(proposal.steps ?? []).map is not a function`. Fix: `parseJsonCols`
   helper at the read site (also called by `formatProposal` defensively
   so it works whether rows came pre-parsed or raw).

3. **`--approve-all` required `TELEGRAM_BOT_TOKEN`** — original gate was
   `if (!TOKEN && !DRY_RUN)`. Fix: gate is now
   `if (!TOKEN && !DRY_RUN && !APPROVE_ALL)`. Also the bot-instantiation
   gate was `if (!DRY_RUN)`; became `if (!DRY_RUN && !APPROVE_ALL)`.

4. **`--approve-all` instantiated the bot anyway** — even after skipping
   the token-required exit, the bot was created with `new TelegramBot("",
   { polling: true })` and entered a 60-second polling loop that fired
   `EFATAL: Telegram Bot Token not provided!` 60×/sec. Fix: only
   `await import("node-telegram-bot-api")` and construct when
   `!DRY_RUN && !APPROVE_ALL`. Plus added `if (APPROVE_ALL) return;`
   after the first poll so it doesn't enter `setInterval`.

5. **`--approve-all` did not exit after one pass** — it ran the first
   `poll()`, then `setInterval(poll, 60_000)`, so the process hung
   forever. Fix: explicit `if (APPROVE_ALL) return;` after the first
   poll, before the `setInterval`.

6. **`bot is not defined` in `sendProposal`** — the function referenced
   `bot` from module scope, but `let bot = null` was declared *inside*
   `main()`, shadowing any module-level reference. Fix: declared
   `let bot = null` at module level, removed the local one in `main()`.

7. **`let bot` shadowing is sneaky** — when the module-level `let bot`
   was added, the LSP error pointed at a missing `}` elsewhere (line
   442), but the real bug was the local declaration. The phantom
   LSP error was a clue to read the function carefully, not to chase
   the brace. `node --check <file>` confirmed parse was actually OK.

8. **Telegram `ETELEGRAM: 400 Bad Request: Character '=' is reserved
   and must be escaped`** — `formatProposal` built
   `confidence=${confidence}%` without escaping `=`. Fix: `\\=` in the
   source template literal (because `\=` is silently dropped by the JS
   engine). Same fix for `|`, both in the source.

9. **`ETELEGRAM: 403 Forbidden: the bot can't send messages to the bot`** —
   `sendProposal` was falling back to `TOKEN.split(":")[0]` when no
   `TELEGRAM_CHAT_ID` was set. The first segment of the token IS the
   bot's own numeric user id. Fix: hard-fail with a clear "set
   TELEGRAM_HOME_CHANNEL" message if `CHAT_ID` is null. Resolution
   hierarchy: `TELEGRAM_HOME_CHANNEL ?? TELEGRAM_CHAT_ID ??
   TELEGRAM_USER_ID ?? null`.

10. **Live bot worked** — first Telegram round-trip succeeded: two
    proposals sent to the user's home channel, both with `inline_keyboard`
    intact (msg_ids 18940, 18941). The user clicked ✅ Approve on
    `a72371a6-...`, the callback fired, `handleApprove` ran, the row
    was marked `approved`, and `SKILL.md` + `SKILL.json` were written to
    `~/Omni-Memory/skills/a72371a6-.../`.

11. **`stripKeyboard` failed with "message identifier is not specified"** —
    `node-telegram-bot-api` v1.1.0 sometimes delivers `callback_query`
    events with a partial `query.message` (missing `chat.id` /
    `message_id`). The user's click approved the skill correctly, but
    the keyboard-strip step errored. Fix: persist `telegram_msg_id` to
    the DB at send time; `stripKeyboard` falls back to that id when the
    callback context is partial. Also added a benign-error list:
    `message is not modified`, `message identifier is not specified`,
    `message to edit not found` all become silent no-ops.

12. **TDZ + camelCase compound — `bot is not defined` masked a real bug** —
    After the previous round of fixes, restarting the bot produced
    `[bot] Failed to send message: bot is not defined` and exit 143.
    Two stacked root causes:
    (a) `const CHAT_ID` guard at line ~38 read `DRY_RUN` and
    `APPROVE_ALL`, but those `process.argv.includes(...)` reads were
    declared at lines ~51–52 (below the guard). TDZ = the guard threw
    `ReferenceError: Cannot access 'DRY_RUN' before initialization`.
    (b) `const Proposals_PATH = ...` (camelCase) was the only
    declaration; three call sites used `Proposals_PATH` and one
    inconsistently used `PROPOSALS_PATH` (uppercase) — so any
    surviving call would have hit `ReferenceError: Proposals_PATH is
    not defined`.
    The displayed error was `"bot is not defined"`, not TDZ, because
    the top-level `main().catch(...)` swallowed the real failure and
    a *later* lazy `await import("node-telegram-bot-api")` /
    `new TelegramBot(TOKEN, { polling: true })` was the next thing
    to throw — its constructor reached for a module-scope `bot` still
    in TDZ, and node-telegram-bot-api's error string happened to read
    `"bot is not defined"`. **Fix:** declared `TOKEN` / `DRY_RUN` /
    `APPROVE_ALL` immediately after the env-var load, before any
    guard; renamed the constant to `PROPOSALS_PATH` everywhere; added
    `OMNI_DB_PATH` env override for portable installs. **Smoke test:**
    `node telegram/bot.mjs --dry-run` now exits 0 with
    `[bot] No pending proposals. Waiting...` and the dry-run summary.
    **Lesson:** when a `Fatal:` message names an unrelated line, the
    real failure is upstream in declaration order — `node --check`
    confirms syntax, only a run surfaces TDZ.

## Verification artifacts

- `verify-bot.mjs` (in this session, archived separately) — 11/11 pass
  on the final state. Covers: source-shape checks (assertKeyboardValid +
  64B cap + stripKeyboard all present), `parseJsonCols` behavior, full
  end-to-end approve flow (seed → --approve-all → SKILL.md written → DB
  updated → registry updated → idempotent re-run → --dry-run formatting).
- Live click test: msg_id 18940 → approve → SKILL.md at
  `~/Omni-Memory/skills/a72371a6-98e1-4bd4-8f45-9f07d426b50d/SKILL.md`
  with rendered Markdown body matching the proposal content.

## Process traps (Hermes-specific)

- **Background `tee` is silent** — when piping node-telegram-bot-api's
  long-running polling loop through `tee`, `process(action='log')` shows
  empty output. Workaround used here: redirect to a file via the
  terminal, then `cat` the file from a separate call.
- **Inline `-e` scripts with quotes in SQL values** — the shell eats
  backslashes inside double-quoted strings, so a seed with `When user
  says "test"` becomes broken. Fix: write a `/tmp/seed.mjs` file via
  `write_file`, run it with `node /tmp/seed.mjs`.
- **`node:sqlite` is experimental** — emits an `ExperimentalWarning` on
  every process start. Filter it out of verification output with
  `2>&1 | grep -v ExperimentalWarning | grep -v "trace-warnings"`.

## Files touched

- `hub/telegram/bot.mjs` — 12 fixes above, ~460 lines
- `hub/ingest/sqlite-shim.mjs` — pre-existing, was already in the
  upstream repo from a prior session's `node-sqlite-shim` work

## What was NOT changed (intentional)

- The SQLite schema (`workflow_proposals` columns) — used what was
  already there, didn't migrate. `telegram_msg_id` column was already
  present, just never written to.
- The `node:sqlite` shim — copied as-is from upstream.
- The Telegram API client choice — `node-telegram-bot-api` v1.1.0
  supports everything needed (polling, callback_query, editMessageReplyMarkup,
  reply_markup on sendMessage).
