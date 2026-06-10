# Three-Angle Scan Protocol

A single `find` or `grep` misses things by construction. When the user asks for
a comprehensive audit, cleanup, removal, or "everything related to X" — especially
with emphatic-scope words like "all", "entirely", "completely", "no link to it
either way" — run three independent angles and cross-reference before reporting.
Skipping any one of them guarantees gaps.

This is the audit protocol for `~/.hermes/` and any directory where Thomas is
asking for completeness. Lives here (and as a standalone `three-angle-scan`
skill) so the `hermes-housekeeping` triggers can surface it.

## The three angles

### Angle 1: By name (path-based)
What files, dirs, or entries have X in their identifier?

```bash
find <scope> -iname "*X*"
ls -la <scope> | grep -i X
hermes skills list | grep -i X
```

**Catches:** files, directories, symlinks, cron job IDs, skill names with X in them.

**Misses:** content that mentions X without naming it; jobs/services that reference
X in their payload but use a different name; structures nested under a category
dir you didn't enumerate; classes/identifiers with a substring of X.

### Angle 2: By content (text-based)
What mentions X regardless of path?

```bash
grep -rIl "X" <scope> --exclude-dir=node_modules
```

**Catches:** skill SKILL.md bodies, README references, comments, config values,
log entries, comments inside scripts.

**Misses:** SQLite/JSONL/binary files unless you extract them; substrings that
look like X but aren't (e.g., "iAgent" vs "aiagent" vs "AIAgent"); case
sensitivity.

**Sub-filter:** when X is ambiguous, use stricter patterns first
(`X-specific-term`), then broaden. `grep "foo-bar-v2"` is more reliable
than `grep "foo"`.

### Angle 3: By relationship (state-based)
What's actively wired to X — what would break, fire, or load if X is gone?

```bash
hermes cron list                       # scheduled jobs
hermes skills list                     # installed skills
ls <scope>/.hub/lock.json              # hub installs
systemctl --user list-units            # services
ps aux | grep -i X                     # running processes
ls /etc/systemd/system/*.service      # system services
```

**Catches:** cron jobs named after X, skills that import or shell out to X,
services depending on X, environment variables pointing at X, scripts with X
in their path that aren't in the main scripts dir.

**Misses:** historical state in snapshots/backups; references in active
config that haven't been exercised yet.

## After running all three

**Cross-reference:** for each finding, mark which angle caught it. If all
three angles produced the same set, you're done. If only one or two caught
something, that thing is your blind spot — flag it explicitly.

**Stale-state check:** when removing something, check each angle for
residue. Cron output dirs, log files, lock files, backup snapshots, archive
copies — all of these are state that the active removal may not clean up.

## Worked example: iAgent removal (2026-06-07)

User said: "iAgent should not be in Hermes at all and there should be no link
to it either way."

**Angle 1 (path):** found 4 files — 2 scripts, 2 reference docs in the
`ambient-agent-architecture` skill. Missed: cron job named "iAgent-windows
Weekly Digest", SKILL.md bodies with iAgent-as-example, the hub lock entry.

**Angle 2 (content):** added 11 more files — 4 in `github-pr-workflow`,
2 in `cronjob-ops`, 3 in `no-replay`, 1 in `skill-evolution`, 1 in
`three-angle-scan`. Plus the 4 from angle 1.

**Angle 3 (relationship):** added 3 more — the cron job (had to use
`hermes cron list`, not `find`), the `.hub/lock.json` cache, and a
`cron/output/git-push.log` orphan. 15 files total vs the 4 that angle 1
returned. The first pass would have been 73% incomplete.

**Critical sub-question surfaced:** "iAgent" meant two different things — the
*machinery* (the iAgent-windows skill + cron + scripts) and the *project
context* (iAgent-windows as Thomas's active build, mentioned as canonical
example in 4 skills). The user wanted the first, kept the second. Removing
both would have been hard to reverse.

**Lesson:** angle 1 returns 4 files and feels complete. It isn't. Always run
all three. And when the user uses emphatic-scope words, ask which "X" they
mean before bulk semantic removal.

## Common blind spots this catches

1. **Cron job names** — `hermes cron list` may show jobs that don't appear
   in any `find` of `scripts/` or `output/`.
2. **Hub-installed skills** — appear in `skills/.hub/lock.json`, may not
   be in the main skills dir if hub install path differs.
3. **Stale log files** — orphan `.log` files in `cron/output/` or elsewhere
   that aren't picked up by directory-based scans.
4. **Empty state files** — `.lock`, `.state`, `.pid` files left behind by
   crashed processes. Often zero-byte.
5. **Config backups** — `*.bak`, `*.old`, `*.prev` files from previous
   configs.
6. **Nested category dirs** — `apple/apple-notes` vs `apple-notes` at root;
   basename filters miss the former.
7. **References in skill bodies** — `references/X.md` content can be a
   container for the thing you're removing, even when the skill itself
   has a different name.
8. **JSONL / SQLite** — `find` skips them silently. `grep` on them treats
   them as text, which works for some files (skill-memory.json) but not
   others (binary blobs). Check explicitly.

## Verification step (run before reporting "X is gone")

```bash
# Replace X with the thing being removed
grep -rIl "X" <scope> 2>/dev/null | \
  grep -v "node_modules" | \
  grep -v "\.archive" | \
  grep -v "\.git/" | \
  grep -v "/log"
```

If this returns files in ACTIVE locations (not archives, not backups,
not vendor), the removal is incomplete. Cross-reference against
`hermes cron list` and `hermes skills list` for the relationship check.

## When to trigger this protocol

- User says "all", "everything", "entirely", "completely", "no link to it"
- User says "remove X from Y" where X is a project/tool/skill name
- User says "audit", "cleanup", "purge", "sweep"
- User pushes back on a "X is gone" report with "I still see X"
- You're about to report findings on a directory you haven't worked with
  before in this session

## When NOT to trigger

- "Is X installed?" — angle 1 only
- "Show me X" — angle 1 only
- "Where is X?" — angle 1 only
