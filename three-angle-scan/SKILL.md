---
name: three-angle-scan
description: >
  First-pass analysis protocol that catches what a single-pattern scan misses. [BRANCH-TEST-MARKER]
  Use when the user asks for comprehensive audit, cleanup, removal, or "everything
  related to X". This is a thin pointer to the full protocol — load the canonical
  reference at `~/.hermes/skills/hermes-housekeeping/references/three-angle-scan.md`
  for the worked example and the 8-item blind-spots checklist. Trigger when user
  says "all", "everything", "entirely", "completely", "no link to it", "anything
  that doesn't belong", "find all", or any cleanup/audit request.
---

# Three-Angle Scan

A single `find` or `grep` misses things by construction. Run three independent
angles and cross-reference before reporting findings.

## Where the full protocol lives

The canonical content for this protocol — including the worked example, the
8-item blind-spots checklist, and the verification script — is in the
`hermes-housekeeping` umbrella:

```
~/.hermes/skills/hermes-housekeeping/references/three-angle-scan.md
```

This skill exists so you can invoke the protocol directly via
`/three-angle-scan` without depending on `hermes-housekeeping` loading first.

## The three angles (summary)

1. **By name (path-based)** — `find -iname "*X*"`. Catches files, cron IDs,
   skill names. Misses content mentions and nested-dir structures.
2. **By content (text-based)** — `grep -rIl "X"`. Catches SKILL.md bodies,
   config values, log entries. Misses JSONL/SQLite, false-positive substrings.
3. **By relationship (state-based)** — `hermes cron list`, `hermes skills list`,
   `.hub/lock.json`, running services. Catches wiring, not just files.

## When to run

- Emphatic-scope words in the request: "all", "everything", "entirely",
  "completely", "no link to it either way"
- Cleanup / audit / purge / sweep / remove
- First-look analysis of an unfamiliar directory
- After a previous audit was pushed back on ("I still see X")

**Don't run** for: "is X installed?", "show me X", "where is X?" — those are
single-angle questions.

## How to run

Either:
- Load this skill, then read the reference at
  `~/.hermes/skills/hermes-housekeeping/references/three-angle-scan.md`
- Or just `skill_view(name="hermes-housekeeping", file_path="references/three-angle-scan.md")`
  directly

Both paths converge on the same content. If they ever drift, the
hermes-housekeeping reference is authoritative.
