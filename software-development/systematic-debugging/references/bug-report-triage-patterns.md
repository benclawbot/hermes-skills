# Bug Report Triage Patterns

Catalog of false-alarm patterns observed in real bug-audit sessions. Use this when triaging a "any bug fixes?" or "find issues" request. Each pattern includes: the signature, why it's a false alarm, how to verify in <60 seconds.

---

## 1. Security Working As Designed

**Signature:** Errors like "Background review denied non-whitelisted tool", "BLOCKED: recursive delete of home directory", "Dotfile overwrite detected", "Secret redaction triggered".

**Why it's a false alarm:** CSL policy, hardline blocklist, and Tirith security scan are *supposed* to block these. The "error" is the system succeeding at its job.

**How to verify:**
```bash
# Check the policy file
grep -rn "BLOCKED.*recursive delete" ~/.hermes/hermes-agent --include="*.py" | head -3
# If it returns code that explicitly blocks and returns the error, it's working as designed.
```

**Triage label:** `security working`

---

## 2. Pre-Validation Rejection (Validator Saved Corruption)

**Signature:** "Patch would break SKILL.md structure: YAML frontmatter parse error", "YAML mapping values are not allowed here", "Schema validation failed".

**Why it's a false alarm:** The validator caught a bad input and refused to write. The code that emits this error is *the fix*, not the bug.

**How to verify:**
```bash
# Find the validator
grep -rn "Patch would break" ~/.hermes/hermes-agent --include="*.py"
# Read it. If it returns the error AND rolls back the write (atomic_write with rollback, or returns success=False before commit), it's working.
```

**Real example (June 2026):** `tools/skill_manager_tool.py:638-643` calls `_validate_frontmatter()` before `_atomic_write_text()`. Three log entries that read like errors were the validator saving us from three corrupt SKILL.md writes.

**Triage label:** `validator working as designed`

---

## 3. Stale Log Entry (Already Fixed)

**Signature:** Error from a date weeks/months in the past, in a config that's now correct.

**Why it's a false alarm:** The log entry captured a transient state. The issue was fixed in a later session, but the log was never pruned.

**How to verify:**
```bash
# Check the timestamp
grep "ERROR" ~/.hermes/logs/errors.log | head -5
# If the most recent occurrence of the error is from >7 days ago and the current state of the affected system is healthy, it's stale.
```

**Triage label:** `stale log entry`

---

## 4. Agent Mistake Logged As Error

**Signature:** "old_string and new_string are identical", "old_string not found in file", "Foreground command uses shell-level background wrappers", "BLOCKED: Command timed out. Do NOT retry this command."

**Why it's a false alarm:** The agent (or a prior session's agent) misused a tool. The error is the tool refusing to do something stupid. Not a code bug.

**How to verify:** Read the tool's argument validation code. If the error is emitted by an `if X: return error` guard before the operation runs, the tool is correct.

**Triage label:** `agent error, not code`

---

## 5. Hallucinated Identifier

**Signature:** "Skill 'foo-bar-baz' not found in active profile", "Module 'X' has no attribute 'Y'", "Unknown tool 'X'", where X doesn't exist anywhere in the codebase.

**Why it's a false alarm:** The agent that emitted the error invented the name. Common when:
- An agent tried to use a skill that "sounded right" but was never created
- An agent confabulated a module path from a function name
- An agent used a category directory as a skill name (e.g. `autonomous-ai-agents` is a category, not a skill)

**How to verify:**
```bash
# Confirm the identifier doesn't exist
grep -rn "foo-bar-baz" ~/.hermes/ 2>/dev/null | head -3
# If empty, it was hallucinated.
```

**Real example (June 2026):** `tool-call-failure-audit`, `hermes-performance-tuning`, `noop` — none exist in `~/.hermes/skills/`. Agents had invented them in past sessions.

**Triage label:** `agent hallucination`

---

## 6. Already-Mitigated In Current Config

**Signature:** A log warning or error for a path/setting that has since been corrected.

**Why it's a false alarm:** User (or a prior session) already fixed it. Log is from before the fix.

**How to verify:**
```bash
# Compare the error's referenced path/setting against current state
# E.g. error says "skill 'note-taking/dreams' not found", check current cron config
hermes cron list | grep -A6 "hermes-dreams"
# If the cron now references the correct skill name, the error is stale.
```

**Triage label:** `already fixed in current config`

---

## 7. Path/Import Collision (Investigate Before Declaring)

**Signature:** "ImportError: cannot import name 'X' from 'Y.Z'" where Y is a file but Z is a directory.

**Why it might be a real bug:** Could be a recent rename/refactor broke a working import.
**Why it might be a false alarm:** A session agent tried the wrong import path.

**How to verify:**
```bash
# Find the source of the bad import
grep -rn "from Y\.Z\|import Y\.Z" --include="*.py" 2>&1 | head -10
# If no production code uses the bad import, the error came from a one-off session.
# If production code uses it, that's a real bug — file path or rename needed.
```

**Real example (June 2026):** `hermes-agent/hermes` is a file (the CLI launcher), not a package. A session tried `import hermes.task_contract`. Current `hermes_cli/main.py` correctly uses `from hermes_cli.task_contract.cli import contract_cmd`. The session was wrong, the code is right.

**Triage label:** `agent-side import error, not code bug`

---

## 8. Memory At Capacity

**Signature:** "Memory at N/N chars. Adding this entry (X chars) would exceed the limit."

**Why it's a real action item:** The agent literally cannot save new memory until compacted. Not a "bug" in the traditional sense, but a hard block on a core feature.

**How to verify:**
```bash
wc -c ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md
```

**Triage action:** Compact MEMORY.md (target ~85% capacity = ~1,870/2,200 chars). Preserve durable facts, drop the lowest-value entries. `write_file` to overwrite is fine — no atomic helper needed for the manual edit.

**Triage label:** `real action item, not a bug`

---

## Quick Reference

| Signature fragment | Triage label |
|---|---|
| "denied non-whitelisted tool" | security working |
| "BLOCKED: ..." | security working |
| "would break SKILL.md structure" | validator working |
| "YAML frontmatter parse error" | validator working |
| "old_string not found" | agent error |
| "old_string and new_string are identical" | agent error |
| "Foreground command uses ... background" | agent error |
| "Skill 'X' not found" (X not in `~/.hermes/skills/`) | agent hallucination |
| "ImportError ... from 'Y.Z'" where Y is a file | agent-side import error |
| Error from >7 days ago, system healthy now | stale log entry |
| "Memory at N/N chars" | real action item |

---

## Session Transcript: 2026-06-05

The patterns above were validated against this session's audit of `~/.hermes/logs/errors.log`:

- **5 candidate bugs reported:** memory full, taste skill update blocked, task_contract import error, "Skill not found", "Patch would break SKILL.md"
- **1 real fix:** Memory compacted 2,121 → 1,916 chars (87% capacity, headroom restored)
- **4 false alarms investigated:** taste update blocked by CSL (security working), task_contract import (agent error, code correct), "Skill not found" (cron already fixed + agent hallucinations), patch validator (working as designed)

**Honest summary format used:**
```
✓ MEMORY.md compacted 2,121 → 1,916 chars (95% → 87% full)
✗ taste skill update — BLOCKED by CSL security verdict
✗ task_contract import — investigated: not a code bug
✗ "Skill not found" — 1 cron config bug (already fixed) + agent hallucination
✗ "Patch would break SKILL.md" — validator working as designed

BUGS FIXED: 1
FALSE ALARMS INVESTIGATED: 4
```
