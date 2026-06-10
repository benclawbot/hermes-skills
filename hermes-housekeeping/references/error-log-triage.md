# Error Log Triage — Finding Real Bugs in 851 Lines of "ERROR"

Captured: 2026-06-05 (after `hermes doctor` showed 2 issues and a request to "check for bug fixes" surfaced 851 recent tool errors in `~/.hermes/logs/errors.log`).

## The Trap

When you grep the error log and see hundreds of `ERROR` / `WARNING` lines, the naive response is to start fixing them. Most are noise. The actual bugs are buried under 90%+ false-positive patterns: security working as designed, agent errors caught by validators, transient blips. Fixing the wrong ones wastes hours and may regress valid behavior.

## The Triage Method (4 steps)

### 1. Quantify the noise first

```bash
# How many errors per tool?
grep -iE "error|exception|traceback" ~/.hermes/logs/errors.log 2>/dev/null \
  | grep -oE "Tool [a-z_]+ returned" | sort | uniq -c | sort -rn
```

If one tool accounts for 50%+ of errors, that's where to focus — but it might still be noise (e.g. `terminal` shows 475 hits because users actually run shell commands and they fail sometimes).

### 2. Categorize the error messages

```bash
# Pull the actual error strings, not just the tool names
grep -iE "error|exception|traceback" ~/.hermes/logs/errors.log 2>/dev/null \
  | grep -oE '"error": "[^"\\]{0,150}' | sort | uniq -c | sort -rn | head -20
```

Group by pattern. Typical categories you'll see:

| Pattern | Class | Action |
|---------|-------|--------|
| "Background review denied non-whitelisted tool: X" | CSL policy working | Ignore — security feature firing |
| "BLOCKED: Command timed out" | Approval system working | Ignore |
| "BLOCKED (hardline): recursive delete" | Security blocklist working | Ignore |
| "Foreground command uses shell-level background wrappers" | Agent misuse of `terminal()` | Ignore (agent error, not code) |
| "old_string and new_string are identical" | Agent mistake | Ignore |
| "Could not find a match for old_string" | Agent context drift | Ignore |
| "Dotfile overwrite detected" | Tirith/secret scan working | Ignore |
| "Tool patch returned error" on whitelist denial | Background review | Ignore |

### 3. Find the actual bugs

Real bugs cluster in these patterns:

- **Recurring validator failures** on the same target — patch/SKILL tool rejecting the same content repeatedly suggests the validator has a gap (or the input is genuinely malformed but the error message is unhelpful)
- **False negatives** — "X not found" when X exists on disk (skill resolution, module import, file path)
- **Memory/storage at limit** — "X at N/max chars. Adding this entry would exceed the limit" is a real action item
- **Repeat config drift** — same warning across multiple cron jobs, same broken toolset, same import error
- **New code in main repo** that hasn't been battle-tested — look for tracebacks in recently-added modules (check `git log --oneline -20` for new code, then grep for errors involving those modules)

### 4. Verify the "bug" is actually a bug

Before patching, look at the source:

```bash
# Where is the error string emitted?
grep -rn "<error-string-snippet>" ~/.hermes/hermes-agent --include="*.py"
```

Many "errors" are intentional validators that prevent worse outcomes (e.g. SKILL.md YAML frontmatter pre-check). The error in the log is the validator *saving you* — removing the validator creates the actual bug.

## Quick Decision Matrix

| Finding type | Example | Decision |
|--------------|---------|----------|
| Tool blocked from background review | "denied non-whitelisted tool: patch" | NO ACTION — security working |
| Validator preventing bad write | "Patch would break SKILL.md structure" | NO ACTION — validator working |
| Same warning on a cron job for days | "skill not found, skipping" | INVESTIGATE — silent failure |
| "X not found" but X exists | "Skill 'foo' not found" (it IS installed) | INVESTIGATE — false negative |
| Memory/storage near limit | "Memory at 2,087/2,200 chars" | ACTION — compact now |
| Repeated traceback in new code | ImportError after recent merge | INVESTIGATE — actual bug |
| Agent hallucinated a tool/skill name | "Skill 'tool-call-failure-audit' not found" | NO ACTION — agent error |
| Cross-process resource exhaustion | OOM, file handle, port bind | INVESTIGATE — may be real |

## Real Numbers from June 5 Sweep

Of 851 tool errors in 30 days:
- ~750 (88%) — security/validator working as designed
- ~50 (6%) — agent mistakes (wrong imports, hallucinated names, identical patch args)
- ~30 (3%) — silent cron skill-resolution drift
- ~10 (1%) — actual fixable state (memory full, one cron config drift, one cosmetic false positive)
- ~10 (1%) — transient blips (network, timeout)

**Takeaway:** 99% of the time, the right answer is "no real bugs to fix." That itself is a valid result. Report it directly:

```
BUGS FIXED: 1 (memory full → compacted)
FALSE ALARMS INVESTIGATED: 4 (all working as designed or already fixed)
```

## When to Sweep

- After `hermes doctor` shows issues that don't match the lean-config defaults
- Before any "fix all" type request (verify the "all" is real first)
- Quarterly, paired with config migration
- When the user says "is anything broken" / "any bug fixes" / "audit"

## Anti-Patterns

- **Fixing validator errors** — they're saving you from corruption. Removing the validator creates the bug.
- **Disabling "broken" toolsets** that are actually working with a missing env var — user may fill the key later.
- **Running `git pull` on diverged forks** without checking why they're diverged — your 339-commit lead may be intentional local work, not stale.
- **Treating `last_status: ok` as gospel** — it's the previous tick's status. If a fix just landed, wait for the next scheduled run, OR run the script directly to verify.
- **Spawning subagents to triage** — the log is local text, grep is fast, just do it inline.
