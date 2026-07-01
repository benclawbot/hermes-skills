---
name: node-sqlite-shim
description: "Use Node 22.5+ built-in `node:sqlite` instead of `better-sqlite3` for zero-dep SQLite access. Trigger when: hit `NODE_MODULE_VERSION` ABI mismatch on `better-sqlite3`, hit 5-10 min `node-gyp` rebuild timeouts, see `Cannot find module 'better-sqlite3'`, or any hub/server that needs SQLite and can require Node 22.5+."
---

# node:sqlite better-sqlite3-compat shim

## The trap

`better-sqlite3` is the de-facto sync SQLite binding for Node, but the install story on Node 22+ is broken in two ways:

1. **Prebuild ABI mismatch** — `npm install better-sqlite3` downloads a `.node` prebuild for `NODE_MODULE_VERSION 137` (Node 23.x) by default, fails on Node 22.x (`127`) with `Error: NODE_MODULE_VERSION 137. This version of Node.js requires NODE_MODULE_VERSION 127.`
2. **Source build times out** — `npm rebuild better-sqlite3 --build-from-source` invokes `node-gyp` and takes 5-10 min, hitting the 600s Hermes terminal cap.

The escape: Node 22.5+ ships `node:sqlite` built-in. Zero compile, zero prebuild, zero ABI trap.

## The shim

`hub/ingest/sqlite-shim.mjs` in `benclawbot/Omni-Memory` is a working example. ~100 lines covering the API surface `better-sqlite3` callers actually use:

```js
import { DatabaseSync } from "node:sqlite";

class Database {
  constructor(dbPath, opts = {}) {
    // node:sqlite wants `file:...?mode=ro` for readonly; bare path for read-write
    const openPath = dbPath === ":memory:" ? ":memory:"
      : opts.readonly ? `file:${dbPath}?mode=ro` : dbPath;
    this._db = new DatabaseSync(openPath, { readOnly: !!opts.readonly });
  }
  exec(sql) { this._db.exec(sql); }
  pragma(name) { this._db.exec(`PRAGMA ${name};`); }
  prepare(sql) { /* @name → ?N rewrite + object-bind */ }
  transaction(fn) { /* BEGIN/COMMIT/ROLLBACK */ }
  close() { this._db.close(); }
}
function Database(dbPath, opts) { return new Database(dbPath, opts); }
export default Database;
```

## Four subtleties that bite

### 0. JSON columns return raw TEXT, not parsed objects

`better-sqlite3` callers often expect JSON-typed columns to come back as objects (this depends on driver config / your own column typing). `node:sqlite` **always** returns TEXT columns as strings — `(row) => row.steps` gives you `'["a","b"]'`, not `["a","b"]`. If you then do `row.steps.map(...)`, you get `(proposal.steps ?? []).map is not a function`.

**Two ways to fix:**

```js
// A) Parse on read (cheapest, one helper, no schema migration)
const JSON_COLUMNS = ["steps", "sources", "devices"];
function parseJsonCols(row) {
  if (!row) return row;
  for (const col of JSON_COLUMNS) {
    if (typeof row[col] === "string") {
      try { row[col] = JSON.parse(row[col]); } catch { /* leave as-is */ }
    }
  }
  return row;
}
const row = parseJsonCols(getProposal(id));

// B) Use defensive decode at the use site, accepting either string or array
const steps = Array.isArray(row.steps) ? row.steps
             : (typeof row.steps === "string" ? JSON.parse(row.steps) : []);
```

Pick A if you control the read path (one helper, callers stay clean). Pick B if the row can come from multiple sources (some pre-parsed, some raw). The lesson caught the day `--approve-all` crashed: `node:sqlite` doesn't auto-parse the way some `better-sqlite3` setups do.

### 1. `@name` params don't exist in node:sqlite

`better-sqlite3` accepts `VALUES (@id, @name)`. `node:sqlite` does not — it uses `?`, `?N`, or `:name`. Rewrite at `prepare()` time:

```js
prepare(sql) {
  const names = [];
  const rewritten = sql.replace(/@(\w+)/g, (_, key) => {
    let idx = names.indexOf(key);
    if (idx === -1) { names.push(key); idx = names.length - 1; }
    return `?${idx + 1}`;  // 1-indexed
  });
  return new Statement(this._db.prepare(rewritten), names);
}
```

### 2. `run(obj)` → positional spread, NOT nested array

If you naively do `stmt.run([val1, val2])`, `node:sqlite` interprets the array as the FIRST arg and complains "Unknown named parameter '0'". Spread it:

```js
// WRONG: stmt.run([val1, val2])     → array is arg 0, looks like named params
// RIGHT: stmt.run(val1, val2)       → positional
return this._names.map((k) => args[0][k] ?? null);  // spread, not [wrapped]
```

### 3. `Database(path, opts)` is callable in better-sqlite3

`bsqlite(path)` works WITHOUT `new` because bsqlite exports a callable instance. Match that:

```js
function Database(dbPath, opts) { return new DatabaseImpl(dbPath, opts); }
```

Otherwise call sites that drop `new` get `TypeError: Class constructor cannot be invoked without 'new'`.

## Migration steps

1. Add the shim to your project (copy from `benclawbot/Omni-Memory/hub/ingest/sqlite-shim.mjs`).
2. Find/replace `from "better-sqlite3"` → `from "./path/to/sqlite-shim.mjs"` (relative path from each caller's dir).
3. Remove `better-sqlite3` from `package.json` dependencies.
4. Drop `npm install` from your setup script.
5. Add a Node 22.5+ check in setup: `node -e "require('node:sqlite')"` is the canary.

## Verify it works

```bash
# Shim is good if all four return without error:
node --input-type=module -e "
import D from './sqlite-shim.mjs';
const db = D(':memory:');
db.exec('CREATE TABLE t (id TEXT PRIMARY KEY, name TEXT)');
const ins = db.prepare('INSERT OR IGNORE INTO t (id, name) VALUES (@id, @name)');
ins.run({id:'a1', name:'alice'});
console.log(db.prepare('SELECT * FROM t').all());
const tx = db.transaction((vs) => { for (const v of vs) ins.run({id:v, name:v}); });
tx(['x','y','z']);
console.log(db.prepare('SELECT COUNT(*) as c FROM t').get());
db.close();
"
```

## When NOT to use this

- **Node < 22.5** — no `node:sqlite`. Upgrade Node, or stay on `better-sqlite3` and live with the build pain.
- **Heavy `.transaction()` use with SAVEPOINT nesting** — the shim's `.transaction()` is BEGIN/COMMIT/ROLLBACK only, no nested savepoints. `better-sqlite3` does both. If you need nesting, either stay on `better-sqlite3` or extend the shim.
- **Async I/O** — both libraries are sync. Don't try to make this async.

## Anti-patterns observed

- `npm rebuild better-sqlite3 --build-from-source` from a clean clone → 300s+ timeout. The shim is faster than the build, every time.
- Pinning `better-sqlite3@11.x` because "the prebuild matches Node 22" → fragile, breaks the day Node 23 ships. The shim works on both 22 and 23.
- Conditional `import("better-sqlite3")` with fallback — adds runtime branching for a problem that doesn't exist anymore.
- **Audit ONLY the dep you're replacing in package.json — not transitive deps that share the same problem.** Grep the entire project (collectors/, hub/, scripts/) for the import, not just the obvious call site. In Omni-Memory I audited `hub/package.json` for `better-sqlite3`, fixed the hub, then `install-mac.sh`'s collector step blew up because `collectors/package.json` had its own copy. Same trap, two places.

## Multi-surface audit checklist (when replacing a fragile dep)

Before declaring the migration done:

1. `grep -rln 'from "<fragile-dep>"\|require("<fragile-dep>")' <project-root>/` — every import, not just the obvious one.
2. `find <project-root> -name 'package.json' -not -path '*/node_modules/*'` — every manifest. Each one may pin the dep independently.
3. Check install/setup scripts for `npm install` steps that could re-introduce the dep.
4. Run the install from a fresh clone, end-to-end. If the install completes without a native compile, you got them all.

## Reference

- Working shim: `hub/ingest/sqlite-shim.mjs` in `benclawbot/Omni-Memory`
- Real-data validation: 15,596 events ingested + 7 proposals synthesized against the shim on 2026-06-15
- Worked-example commit: `065aa4b` (hub) + `d5cee24` (collectors) in `benclawbot/Omni-Memory`
- See `references/omni-memory-port.md` for the full session-specific port log (call sites swapped, three subtle bugs encountered, the npm-gyp pile-of-shame we sidestepped)
