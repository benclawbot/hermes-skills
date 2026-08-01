# Codebase Audit Reference

## Audit Pattern

**When:** User says "look at your code base and identify fixes/improvements and implement them"

**Approach:**
1. Dispatch parallel auditor subagents across distinct areas (gateway/, tools/, agent/, skills/, cron/)
2. Each auditor gets its own scope + trigger list (bare except/pass, error handling gaps, race conditions, resource leaks, silent failures, hardcoded values)
3. Collect findings from all subagents
4. Prioritize: critical bugs first, then medium, then low
5. Implement fixes with compile check + tests after each

## Findings Taxonomy

| Severity | Types |
|---|---|
| **Critical** | Data loss risk, security bypass, resource leaks on hot paths |
| **Medium** | Performance issues on hot paths (repeated syscalls per invocation), silent fallback masking errors, wrong return value for empty case |
| **Low** | Logging inconsistencies (print vs logger), hardcoded values, complex functions needing refactor, test stubs with placeholder errors |

## Common Audit Triggers

```
# Silent failure patterns
except: pass                    → always log or re-raise
except Exception: pass         → catch specific exceptions
logger.debug only on failure    → upgrade to warning for actionable failures

# Resource leak patterns  
open() without with            → use context manager
os.remove without try/except    → ffmpeg may not produce output on failure

# Race condition patterns
compute outside lock, store inside → hold lock for entire miss-compute-store
cache without invalidation key     → key on all inputs that affect computation

# Return value bugs
return "caution" for empty      → should be "safe" when no findings
return None vs {} ambiguous     → use sentinel for "path not found" vs "definitively absent"

# Signal swallowing
except Exception: raise         → re-raise KeyboardInterrupt/SystemExit explicitly
```

## Hermes-Specific Findings Applied

| # | Fix | File | Severity |
|---|---|---|---|
| 1 | os.remove wrapped in try/except OSError | tools/tts_tool.py | Medium |
| 2 | HERMES_ASYNC_TOOL_TIMEOUT from env | model_tools.py | Low |
| 3 | Silent import → warning log | cli.py | Low |
| 4 | Cache race in _check_fn_cached | tools/registry.py | Medium |
| 5 | Module-level cache for write-denied sets | agent/file_safety.py | Medium |
| 6 | Verdict "caution" → "safe" for empty scan | tools/skills_guard.py | Medium |
| 7 | Re-raise KeyboardInterrupt/SystemExit | tools/skills_tool.py | Low |

## Testing Strategy

After any fix:
1. `python3 -m py_compile <file>` — syntax check
2. `python3 -m pytest tests/<area>/test_<file>.py -v --tb=short` — existing tests
3. If no existing tests for the changed code: verify the fix works manually, note that tests are missing

## Not Bugs (Intentional Design)

- `ignore_errors=True` on best-effort cleanup in terminal_tool.py/browser_tool.py — intentional, cleanup is best-effort
- `_profile_fallback_warned` writing to stderr before logging is set up — correct fallback behavior
- `raise NotImplementedError` in test stubs — markers that tests haven't been written
- `raise NotImplementedError` in abstract method base classes — subclass responsibility markers