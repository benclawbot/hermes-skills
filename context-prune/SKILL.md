---
name: context-prune
description: Aggressively truncate context at 60% full before compression gets heavy. Drop boilerplate, keep signal.
triggers:
  - context_60_percent
  - context_heavy
  - session_long
---

# Context Prune

Hard truncate before context gets expensive. Fires at ~60% context usage and again at 80%.

## When to Fire

1. When the compression/context meter hits ~60%
2. After 20+ tool calls in a session
3. When session history exceeds ~30 turns

## What to Drop (in order)

Keep: last user message, last 2 assistant messages, anything still referenced.

Drop aggressively:
- Full tool result dumps (replace with 1-line summaries)
- Repeated system prompt re-injections (keep only the first)
- Verbose error traces (keep: error type + line number + 1-line cause)
- Tool call chains > 10 turns old that aren't referenced
- Repeated explanation of the same concept across turns
- Boilerplate from `git diff`, `ls -la`, `grep` — summarize to "N files changed, M new"

## How to Summarize Before Dropping

Use a single-pass reduction:

```
Tool: git diff --name-only (12 files)
→ [git] 12 files changed

Tool: grep -r "TODO" (47 matches across 8 files)  
→ [grep] TODO in 8 files, worst: auth.py:23, main.py:45

Tool: read_file 300 lines
→ [read] file.py: 300 lines — auth flow, 2 helper functions

Tool: terminal pytest output (50 lines)
→ [pytest] 2 failures: test_auth.py:12, test_main.py:8
```

## Output Format

When pruning fires, say nothing unless the user asks. Just silently compact.
If context is critically full (>85%), say: "Context compacting — summarizing older turns."

## Don't Drop

- Anything the last 2 user messages reference
- Active working file contents (still being edited)
- Memory facts
- User preferences or corrections
- Anything that would break continuity if dropped
