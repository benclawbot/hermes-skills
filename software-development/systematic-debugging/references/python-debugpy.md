# Python Debugger (pdb + debugpy)

## Overview

Three tools, picked by situation:

| Tool | When |
|---|---|
| **`breakpoint()` + pdb** | Local, interactive, simplest. Add `breakpoint()` in the source, run normally. |
| **`python -m pdb`** | Launch an existing script under pdb with no source edits. |
| **`debugpy`** | Remote / headless / attach to already-running process. Talks DAP. |

**Start with `breakpoint()`.** It's the cheapest thing that works.

## When to Use

- A test fails and the traceback doesn't reveal why a value is wrong
- Long-running process (hermes gateway, tui_gateway) misbehaves and you can't restart it
- Post-mortem: an exception fired and you want to inspect locals at the crash site
- A subprocess is the actual bug site

**Don't use for:** things `print()` / `logging.debug` solve in under a minute.

## pdb Quick Reference

Inside any pdb prompt (`(Pdb)`):

| Command | Action |
|---|---|
| `h` / `h cmd` | help |
| `n` | next line (step over) |
| `s` | step into |
| `r` | return from current function |
| `c` | continue |
| `unt N` | continue until line N |
| `l` / `ll` | list source |
| `w` | where (stack trace) |
| `u` / `d` | move up / down in the stack |
| `p expr` / `pp expr` | print / pretty-print |
| `display expr` | auto-print on every stop |
| `b file:line` | set breakpoint |
| `cl N` | clear breakpoint N |
| `interact` | drop into full Python REPL (Ctrl+D to exit) |
| `q` | quit |

## Recipe 1: Local breakpoint

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # drops into pdb here
    return result + y
```

Run normally. Remove before committing:
```bash
rg -n 'breakpoint\(\)' --type py
```

## Recipe 2: Launch under pdb (no source edits)

```bash
python -m pdb path/to/script.py arg1 arg2
(Pdb) b path/to/script.py:42
(Pdb) c
```

## Recipe 3: Debug a pytest test

pdb does NOT work under pytest-xdist. Add `-p no:xdist` or `-n 0`:

```bash
scripts/run_tests.sh tests/foo_test.py::test_bar --pdb -p no:xdist
```

## Recipe 4: Post-mortem on any exception

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

Or:
```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it at the exception frame
```

## Recipe 5: Remote debug with debugpy

### Pattern A: Source-edit — process waits for debugger at launch

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678, waiting for client...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()       # optional
```

Start the process; it blocks on `wait_for_client()`. Attach a DAP client.

### Pattern B: No source edit — launch with `-m debugpy`

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py
```

### Pattern C: Attach to an already-running process

```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
```

Needs debugpy installed in the target's environment.

### Connecting a client

**Option 1: VS Code / Cursor / Zed** — add `launch.json`:

```json
{
  "name": "Attach to Hermes",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 },
  "justMyCode": false,
  "pathMappings": [
    { "localRoot": "${workspaceFolder}", "remoteRoot": "/home/bb/hermes-agent" }
  ]
}
```

**Option 2: `remote-pdb`** — the cleanest terminal agent choice:

```bash
pip install remote-pdb
```

```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```

Then:
```bash
nc 127.0.0.1 4444
# You get a (Pdb) prompt
```

## Debugging Hermes-specific Processes

| Process | Approach |
|---------|---------|
| Tests | `scripts/run_tests.sh` + `-p no:xdist` |
| `run_agent.py` / CLI | `breakpoint()` near suspect line, run normally |
| `tui_gateway` subprocess | `remote-pdb` with `set_trace()` inside handler; `nc` to attach |
| `_SlashWorker` subprocess | `remote-pdb` inside the worker's exec path |
| Gateway (`gateway/run.py`) | `debugpy` with `--wait-for-client` or `remote-pdb` at handler |

## Common Pitfalls

1. **pdb under pytest-xdist silently does nothing.** Always use `-p no:xdist` or `-n 0`.
2. **`breakpoint()` in CI / non-TTY hangs the process.** Never commit it.
3. **`PYTHONBREAKPOINT=0`** disables all `breakpoint()` calls. Check env if breakpoint isn't hitting.
4. **`debugpy.listen` blocks only if you also call `wait_for_client()`.**
5. **Attach to PID fails on hardened kernels.** `ptrace_scope=1` allows only same-user ptrace of child processes. Fix: `echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope` or use `remote-pdb`.
6. **Threads.** `pdb` only debugs the current thread. For multithreaded code, use `debugpy` (thread-aware DAP).
7. **asyncio.** `pdb` works in coroutines but `await` inside pdb requires Python 3.13+.
8. **`scripts/run_tests.sh` strips credentials and sets `HOME=<tmpdir>`.** If bug depends on user config, debug with raw `pytest` first.

## Verification Checklist

- [ ] After `pip install debugpy`, confirm: `python -c "import debugpy; print(debugpy.__version__)"`
- [ ] For remote debug, confirm port listening: `ss -tlnp | grep 5678`
- [ ] First breakpoint actually hits
- [ ] Post-debug cleanup: no stray `breakpoint()` / `set_trace()` in committed code
  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```
