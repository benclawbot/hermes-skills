# Omni-Memory: better-sqlite3 → node:sqlite port log

Session: 2026-06-15
Repo: `benclawbot/Omni-Memory`
Commits: `065aa4b` (hub), `d5cee24` (collectors)

## Why we ported

`npm install better-sqlite3` on Node 22.22.2 downloaded a `.node` prebuild for `NODE_MODULE_VERSION 137` (Node 23.x), failed at load with:

```
Error: NODE_MODULE_VERSION 137. This version of Node.js requires NODE_MODULE_VERSION 127.
```

`npm rebuild better-sqlite3 --build-from-source` invoked `node-gyp`, compiled `sqlite3.c` for 5-10+ minutes, hit the 600s Hermes terminal cap. Repeatable failure on every clean clone.

## What was swapped

**Hub** (3 files, 1-line import path change each):
- `hub/ingest/merge-events.mjs` — uses `.prepare().run(obj)`, `.prepare().all()`, `.transaction((events) => {...})`
- `hub/synthesis/analyze.mjs` — uses `.prepare().all()`, `.prepare().get()`, `.pragma()`, dynamic `import()` in one helper
- `hub/telegram/bot.mjs` — uses `.prepare().all()`, `.prepare().run()`, callable form `betterSqlite3(path, {readonly:true})` (no `new`)

**Collectors** (1 file, 1 site):
- `collectors/ai/claude-cli.mjs` — `#extractFromSqlite` uses `.prepare().all()`, `.close()`. The JSONL fallback path doesn't need SQLite at all.

**Shim files** (duplicated, by design):
- `hub/ingest/sqlite-shim.mjs`
- `collectors/ingest/sqlite-shim.mjs`

**Removed**:
- `hub/package.json`'s `better-sqlite3` dep
- `collectors/package.json` (entire file — only dep was `better-sqlite3`)
- `collectors/package-lock.json`
- `install-mac.sh` `[2b/6]` collector-npm step
- All `npm install` lines from both READMEs

## Three subtle bugs the shim had to handle

These don't appear in the `node:sqlite` docs as warnings — they only show up the first time you try to use a `better-sqlite3`-style call site.

### 1. `@name` params don't exist in node:sqlite

`better-sqlite3` accepts `INSERT INTO t VALUES (@id, @name)`. `node:sqlite` does not — it uses `?`, `?N`, or `:name`. Rewrite at `prepare()` time:

```js
const names = [];
const rewritten = sql.replace(/@(\w+)/g, (_, key) => {
  let idx = names.indexOf(key);
  if (idx === -1) { names.push(key); idx = names.length - 1; }
  return `?${idx + 1}`;  // 1-indexed
});
return new Statement(this._db.prepare(rewritten), names);
```

`merge-events.mjs` SQL has `@id, @timestamp, ...`; same name appearing twice (e.g. `MAX(@x, @x)`) dedupes correctly.

### 2. `run(obj)` → positional spread, NOT nested array

If you naively do `stmt.run([val1, val2])`, `node:sqlite` interprets the array as the FIRST arg and complains "Unknown named parameter '0'". Spread it:

```js
// WRONG: stmt.run([val1, val2])     → array is arg 0, looks like named params
// RIGHT: stmt.run(val1, val2)       → positional
return this._names.map((k) => args[0][k] ?? null);  // spread, not [wrapped]
```

This is the bug that ate 30 min. The error message ("Unknown named parameter '0'") points at node:sqlite, not at your shim, so the temptation is to debug node:sqlite internals. Don't. Fix the shim.

### 3. `Database(path, opts)` is callable in better-sqlite3

`better-sqlite3` exports a callable instance — `bsqlite(path)` works WITHOUT `new`. `bot.mjs` does this. Match it:

```js
function Database(dbPath, opts) { return new DatabaseImpl(dbPath, opts); }
```

Otherwise call sites that drop `new` get `TypeError: Class constructor cannot be invoked without 'new'`. Tested on `bot.mjs:98`.

## Audit miss I made the first time

I grepped `hub/package.json` for `better-sqlite3` and fixed the hub. Pushed. Re-ran `install-mac.sh`. The hub worked, but the install script's `[2b/6]` step (`npm install` in `collectors/`) blew up the same way, because **`collectors/package.json` had its own `better-sqlite3@^11.0.0` dep**. The grep was too narrow.

Fix: search the whole repo, not just the obvious package.json. Or: have install-mac.sh do the audit itself and refuse to `npm install` if any package.json references `better-sqlite3`.

## Verification artifacts

- **Static:** shim loadable from both `hub/ingest/` and `collectors/ingest/`, all 3 subtle-bug scenarios pass (object bind, named dedup, transaction with rollback).
- **Real ingest:** `node hub/ingest/merge-events.mjs --export-dir exports/linux-thomas-macbookair6-2` → 15,596 events ingested, 405 skipped (dups), 4 sources (pi, hermes, claude-cli, codex).
- **Real synthesis:** `node hub/synthesis/analyze.mjs` → 7 proposals generated, written to `~/.memory/hub/proposals.db`.
- **Install (partial):** `OMNI_MEMORY_NONINTERACTIVE=1 bash install-mac.sh` ran steps 1, 2 (Node check), 3 (env), 5 (first hub run), 6 (cron). Hub run failed initially because the just-cloned repo didn't have the shim yet (we hadn't pushed it before re-installing) — fix was to push `065aa4b` first, then re-clone.

## Known follow-ups (not done in this session)

- The seven proposals are all at 70% confidence — the synthesis engine's default template floor. To get proposals that are actually specific to *your* workflow (not just generic "code creation"), the engine needs cross-device data and a higher confidence floor.
- Telegram dispatch not tested — no `TELEGRAM_BOT_TOKEN` in `~/.memory/.env`. The bot starts cleanly with a fake token and exits with the expected 401, so the wiring is correct.
- `node:sqlite` emits an `ExperimentalWarning`. Add `NODE_NO_WARNINGS=1` to `install-mac.sh` if you want silent output.
