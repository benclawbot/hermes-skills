# Hermes Agent Codebase Findings (hermes-agent)

Findings from systematic codebase review. These are concrete, verified issues with fix
notes. Start here before generating new findings from scratch — many issues are already
known and some have partial fixes.

---

## Verified Fixes Applied

### 1. TTS tool: bare `os.remove` → try/except OSError
**File:** `tools/tts_tool.py:1310, 1534`
**Pattern:** After ffmpeg conversion, `os.remove(wav_path)` raised `FileNotFoundError`
if the file was already moved/renamed by a prior cleanup attempt.
**Fix:** Wrap in `try: os.remove() except OSError: pass` — same pattern already used
elsewhere in the same file (lines 1226-1228).

### 2. Async tool timeout made configurable via env var
**File:** `model_tools.py:35`
**Before:** `_ASYNC_TOOL_TIMEOUT = 300  # seconds` (hardcoded)
**After:** `_ASYNC_TOOL_TIMEOUT = int(os.environ.get("HERMES_ASYNC_TOOL_TIMEOUT", 300))`
**Usage:** `export HERMES_ASYNC_TOOL_TIMEOUT=600` (seconds)

### 3. Silent import error in tool availability warnings
**File:** `cli.py:5050-5057`
**Before:** `except Exception: pass` — import/tool-check failures vanished
**After:** Logs a warning with exception details so failures are visible in logs

### 4. Cache race in `_check_fn_cached`
**File:** `tools/registry.py:126-141`
**Bug:** Computed value outside the lock while holding it for cache-hit fast-path.
Concurrent calls for same uncached function all computed simultaneously (thundering herd).
**Fix:** Hold lock for entire miss-compute-store cycle. Concurrent callers now wait
rather than duplicate work. Comment updated to explain.

---

## Known Issues (Not Yet Fixed)

### 5. `history_offset` in `_run_agent` return dict
**File:** `gateway/run.py:15238`
**Status:** Fixed at line 7755 (the consumer). At production call sites `_run_agent`
returns `history_offset: len(agent_history)` which is the filtered length — correct.
The bug test (`tests/gateway/test_transcript_offset.py`) documents the old vs new
behavior. The fix is already in place; the test serves as regression prevention.

### 6. `AIAgent.close()` already calls cleanup (zombie process issue)
**File:** `run_agent.py:5607-5660`
**Status:** Already implemented. Calls `process_registry.kill_all()`,
`cleanup_vm()`, `cleanup_browser()`, closes child agents and client.
Tests in `tests/tools/test_zombie_process_cleanup.py` verify this.
The zombie issue in the report was a doc/test finding, not a code bug.

### 7. `ignore_errors=True` on cleanup (terminal_tool, browser_tool)
**Status:** Intentional — best-effort cleanup where failure is acceptable.
Failures are logged at DEBUG level (hidden by default) but logged on success.
Not a bug.

### 8. `_profile_fallback_warned` bare `except Exception`
**File:** `hermes_constants.py:65-66`
**Status:** Intentional — warns about misconfigured HERMES_HOME at import time,
before logging is configured. Writes to stderr as fallback. Not a bug.

---

## Codebase Structure Notes

**Large files to be aware of (hard to navigate):**
- `run_agent.py` — 15,679 lines
- `gateway/run.py` — 16,532 lines
- `cli.py` — 13,564 lines
- `hermes_cli/main.py` — 11,875 lines

**Entry points:**
- `tools/registry.py` — all tools self-register via `registry.register()` at import time
- `model_tools.py` — bridges registry to agent, handles async tool execution
- `hermes_constants.py` — profile-aware paths, imported by 30+ files

**Key patterns observed:**
- Silent `pass` in exception handlers: common pattern throughout. When fixing, prefer
  `logger.warning(...)` or `logger.debug(...)` over removing the guard.
- `threading.Lock()` (non-reentrant) used in some places where `threading.RLock()`
  would be safer against nested acquisition.
- `shutil.rmtree(path, ignore_errors=True)` is the standard cleanup pattern — do not
  "fix" by removing `ignore_errors` without understanding the intent.