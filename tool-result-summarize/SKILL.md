---
name: tool-result-summarize
description: Summarize tool outputs before they enter context. Turn verbose dumps into 1-line signals.
triggers:
  - tool_result_large
  - tool_result_git
  - tool_result_grep
  - tool_result_terminal
---

# Tool Result Summarize

Replace verbose tool outputs with 1-line summaries before they hit context. The tools ran — you don't need to re-read their full output.

## What to Summarize

Summarize ALL of these automatically:

### git
```
git diff --name-only     → [git] N files changed
git diff                → [git] N files changed, +/-N lines
git status              → [git] clean / N files modified / N untracked
git log                 → [git] last: commit message on branch
git show               → [git] commit hash — N files, +/-N lines
git branch              → [git] N branches, current: branch name
```

### grep / search_files
```
N matches across M files → [grep] N hits in M files
                          → [grep] N hits in M files, worst: file:line
                          → [grep] no matches
```

### ls / find / search_files (file lists)
```
N files listed         → [ls] N files in dir
                        → [ls] N files — .py, .md, .json most recent
```

### read_file
```
file.py, N lines        → [read] file.py: N lines — what it contains in 1 clause
                        → [read] file.py: N lines — imports X, defines Y, main flow Z
```

### terminal (any command)
```
command output          → [cmd] one line summary of what the command produced
```

### pytest / test output
```
N failures             → [pytest] N failures: file:test_name:line
N passed               → [pytest] N passed
errors                 → [pytest] errors: type at file:line
```

## Format Rule

Every summary: `[tool] signal in N words`

Keep it to one line. If it fits in 10 words, use 10 words. If it needs 15, use 15. Never more.

## When NOT to Summarize

- Error tracebacks — keep the last 5 lines (error type + file + line + 1 cause line)
- File contents still being actively edited (read_file on files you're working on)
- Output explicitly requested by the user ("show me the full output")
- Very short outputs (< 3 lines) — these don't need summarizing

## How It Works

This is a mental habit: after every tool call, before moving on, replace the raw output with its summary in your reasoning. The raw output is already in the transcript — you're just deciding what to carry forward into the next turn.

Never say "the output shows..." — just act on the summary and move.
