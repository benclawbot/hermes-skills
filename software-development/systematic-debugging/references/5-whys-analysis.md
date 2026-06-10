---
name: 5-whys-analysis
description: Use when Thomas says "figure out why", "root cause", "5 why", or any task that needs true cause diagnosis before fixing. Drill down to root causes using the 5 Whys technique, then fix every identified issue autonomously.
version: 1.0.0
author: Thomas
metadata:
  hermes:
    tags: [debugging, root-cause, systematic]
    related_skills: [systematic-debugging, requesting-code-review]
---

# 5 Whys Analysis + Fix

## Concept

The 5 Whys technique: repeatedly ask "why" to drill past symptoms to the root cause. After the analysis, automatically fix every issue identified — no fix left for later.

The skill has two phases:
1. **Diagnose** — 5 Whys iteration until root cause is reached
2. **Fix** — apply targeted fixes for each identified cause, in dependency order

---

## Phase 1: Diagnose (5 Whys Iteration)

For each "why", write:
- The question
- The answer (observable fact, not speculation)
- The next "why" triggered

Stop when the answer is:
- A concrete root cause (no further "why" applies)
- Something outside your control to fix

**Common stopping points for software/data issues:**
- User action / misconfiguration → stop (user must correct)
- Missing dependency → fixable
- Bug in external service → document, work around if possible
- Design flaw → fixable if code, escalate if not

---

## Phase 2: Fix

For each cause identified:

| Cause type | Fix approach |
|---|---|
| Code bug | Patch the file directly |
| Missing file | Create it with correct content |
| Wrong config | Patch the config |
| Permission/ownership | `sudo chown` or `chmod` via terminal |
| Missing dependency | Install or document installation |
| Data corruption | Overwrite with corrected data |
| Environment issue | Export env var or patch shell config |
| External service bug | Document + suggest workaround |

**Critical rule:** Fix causes in dependency order. If cause B exists because cause A exists, fix A first.

**After all fixes:** Verify each fix by re-running the relevant check, test, or observation that originally surfaced the symptom.

---

## Output Format

```
## 5 Whys Analysis

### Why 1
**Q:** Why [symptom]?
**A:** [Observable fact]

### Why 2
**Q:** Why [answer from Why 1]?
**A:** [Observable fact]

...

### Root Cause
[Final root cause]

## Fixes Applied

| # | Cause | Fix | Verified |
|---|---|---|---|
| 1 | [cause] | [what was done] | ✅/❌ |

## Residual Issues
[Any causes outside scope to flag to Thomas]
```

---

## Embedded Auto-Fix (no-agent scripts)

For `no_agent=true` cron jobs that run shell scripts, the script itself should carry embedded 5-whys auto-fix logic so failures self-heal before alerting you.

**Reusable wrapper:** `scripts/sandy-auto-fix-wrapper.sh` — takes scenario path and fail file path as args. Call it from any Sandy cron script instead of hand-coding the pattern each time.

**The pattern:**
```bash
#!/bin/bash
FAIL_FILE="/tmp/$(basename $0).fail"
PYTHON="/home/thomas/Desktop/hermes-agent/.venv/bin/python3"

output=$($PYTHON /path/to/scenario.json 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    rm -f "$FAIL_FILE"
    [ -n "$output" ] && echo "$output"
    exit 0
fi

# 5-whys auto-fix: common deterministic failures
# Detect missing Python deps and install them
if echo "$output" | grep -q "ModuleNotFoundError"; then
    MODULE=$(echo "$output" | grep -oP "No module named '\K[^']+")
    if [ -n "$MODULE" ]; then
        uv pip install --python "$PYTHON" "$MODULE" 2>/dev/null
        output=$($PYTHON /path/to/scenario.json 2>&1)
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            rm -f "$FAIL_FILE"
            [ -n "$output" ] && echo "$output"
            exit 0
        fi
    fi
fi

# Retry didn't work — write fail file for agent diagnosis
echo "$output" > "$FAIL_FILE"
exit $exit_code
```

**Always use the explicit venv Python path**, never bare `python3` — the Sandy scripts depend on packages installed in the Hermes venv, not system Python.

**Known failure patterns to auto-fix:**
- `ModuleNotFoundError` → extract module name, `uv pip install --python "$PYTHON" <module>`, retry once
- Exit code 1 with no output → check `.fail` file for the real error

## Pitfalls

- **Speculation instead of facts** — each "why" answer must be based on observable evidence (file content, command output, error message, network response)
- **Stopping too early** — if the answer is "because the code is wrong", ask why the code is wrong (wrong logic, wrong assumption, missing edge case?)
- **Fixing symptoms not causes** — deleting error messages is not fixing the bug; patching the bug is
- **Missing dependency order** — fixing B before A when A causes B wastes time
- **No verification** — a fix without confirmation is just a guess
- **Bare `python3` in wrappers** — resolves to system Python, not the venv with all Hermes deps; always use explicit venv path

## Verification

After all fixes:
1. Re-run the original failing command or trigger
2. Confirm the symptom no longer occurs
3. Confirm no new symptoms introduced
4. Report what was fixed and what still needs manual attention