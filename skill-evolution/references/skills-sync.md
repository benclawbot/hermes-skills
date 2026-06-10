## Skill Creation Path Routing — Delegation Bug (May 2026)

When a sub-agent creates skills via `skill_manage(action='create', category='pm')` with only a category parameter, skills land at `~/.hermes/skills/<category>/` — NOT at the intended umbrella subdirectory.

**Pattern observed:** `category='pm'` creates top-level dir `~/.hermes/skills/pm/`, ignoring any intended subdir nesting.

**Consequence:** Early pm-sub-skill batches scattered skills into `~/.hermes/skills/pm/` instead of `~/.hermes/skills/productivity/pm-command-center/pm-skills/`. Required manual consolidation after each batch.

**Workaround:** Always use `file_path` with the full absolute target path and omit `category`, OR post-creation consolidate with `mv` to the correct location.

**Fix needed:** `skill_manage` should support `file_path` as a subdirectory path relative to skills root, not just as a file target within an existing skill dir.