# Node.js Inspect Debugger

## Overview

When `console.log` isn't enough, drive Node's built-in V8 inspector from the terminal.

Two tools:

- **`node inspect`** — built-in, zero install, CLI REPL.
- **`ndb` / CDP via `chrome-remote-interface`** — scriptable; best for automation.

**Prefer `node inspect` first.** It's always available.

## When to Use

- A Node test fails and you need to see intermediate state
- ui-tui crashes or behaves wrong and you want to inspect React/Ink state pre-render
- tui_gateway child processes (`_SlashWorker`, PTY bridge workers) misbehave
- You need to inspect a closure value that `console.log` can't reach

**Don't use for:** things `console.log` solves in under a minute.

## Quick Reference: `node inspect` REPL

```bash
node inspect path/to/script.js
# or with tsx
node --inspect-brk $(which tsx) path/to/script.ts
```

The `debug>` prompt:

| Command | Action |
|---|---|
| `c` / `cont` | continue |
| `n` / `next` | step over |
| `s` / `step` | step into |
| `o` / `out` | step out |
| `sb('file.js', 42)` | set breakpoint at file.js line 42 |
| `sb('functionName')` | break on function entry |
| `cb('file.js', 42)` | clear breakpoint |
| `bt` | backtrace (call stack) |
| `list(5)` | show 5 lines of source around current position |
| `watch('expr')` | evaluate expr on every pause |
| `repl` | drop into REPL in current scope (Ctrl+C to exit REPL) |
| `.exit` | quit debugger |

## Attaching to a Running Process

```bash
# 1. Enable inspector on existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# 2. Attach the debugger CLI
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

Start with inspector from the beginning:

```bash
node --inspect script.js           # listen on 127.0.0.1:9229, keep running
node --inspect-brk script.js       # listen AND pause on first line
node --inspect=0.0.0.0:9230 script.js   # custom host:port
```

For TypeScript via tsx:

```bash
node --inspect-brk --import tsx script.ts
```

## Programmatic CDP (scripting from terminal)

```bash
npm i -g chrome-remote-interface
node --inspect-brk=9229 target.js &
```

Driver script (`/tmp/cdp-debug.js`):

```javascript
const CDP = require('chrome-remote-interface');

(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);

    // Walk scopes for locals
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId,
          ownProperties: true,
        });
        for (const p of result) {
          console.log(`  ${scope.type}.${p.name} =`, p.value?.value ?? p.value?.description);
        }
      }
    }

    const { result } = await Debugger.evaluateOnCallFrame({
      callFrameId: top.callFrameId,
      expression: 'typeof state !== "undefined" ? JSON.stringify(state) : "n/a"',
    });
    console.log('state =', result.value ?? result.description);

    await Debugger.resume();
  });

  await Runtime.enable();
  await Debugger.enable();

  await Debugger.setBreakpointByUrl({
    urlRegex: '.*app\\.tsx$',
    lineNumber: 119,
    columnNumber: 0,
  });

  await Runtime.runIfWaitingForDebugger();
})();
```

Run it:
```bash
node /tmp/cdp-debug.js
```

Note: `chrome-remote-interface` is NOT in `ui-tui/package.json`. Install to a throwaway location:
```bash
mkdir -p /tmp/cdp-tools && cd /tmp/cdp-tools && npm i chrome-remote-interface
NODE_PATH=/tmp/cdp-tools/node_modules node /tmp/cdp-debug.js
```

## Debugging Hermes ui-tui

### Debugging a single Ink component under dev

```bash
cd /home/bb/hermes-agent/ui-tui
npm run build
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
# Then:
sb('dist/app.js', 220)
cont
```

### Debugging a running `hermes --tui`

```bash
hermes --tui &
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)
kill -SIGUSR1 "$TUI_PID"
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'
node inspect ws://127.0.0.1:9229/<uuid>
```

### Debugging `_SlashWorker` / PTY child processes

Those are Python, not Node — use the `python-debugpy` skill for them.

## Running Vitest Tests Under the Debugger

```bash
cd /home/bb/hermes-agent/ui-tui
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
# In another terminal:
node inspect -p <pid>
sb('src/app/foo.tsx', 42)
cont
```

Use `--no-file-parallelism` so only one worker exists.

## Heap Snapshots & CPU Profiles

```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));
// Open in Chrome DevTools → Performance tab
```

```javascript
// Heap snapshot
await client.HeapProfiler.enable();
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

## Common Pitfalls

1. **Wrong line numbers in TS source.** Breakpoints hit the emitted JS, not the `.ts`. Use `dist/*.js` or enable sourcemaps (`node --enable-source-maps`). `node inspect` CLI does not follow sourcemaps.
2. **`--inspect` vs `--inspect-brk`.** `--inspect` doesn't pause; use `--inspect-brk` when you need breakpoints before any code runs.
3. **Port collisions.** Default is `9229`. Use `--inspect=0` (random port) and read from `/json/list`.
4. **Child processes.** `--inspect` on a parent does NOT inspect children. Use `NODE_OPTIONS='--inspect-brk'` to propagate.
5. **Background kills.** If you `Ctrl+C` out of `node inspect` while target is paused, target stays paused. `cont` first or `kill` explicitly.
6. **`node inspect` through an agent terminal.** Use `terminal(pty=true)` or `background=true` + `process(action='submit', data='...')`.

## Verification Checklist

- [ ] `curl -s http://127.0.0.1:9229/json/list` returns the target you expect
- [ ] First breakpoint actually hits
- [ ] Source listing at pause shows the right file
