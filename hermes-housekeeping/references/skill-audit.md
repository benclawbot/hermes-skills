# Skill Security & Hygiene Audit

Use when Thomas says "remove risky skills", "audit skills", "clean up skills", or asks
about a hub-installed skill that might be dangerous. The `csl-policy` skill (bundled,
active security gate) uses `tirith` (binary in `~/.hermes/bin/`) to scan every skill at
install time and writes a `scan_verdict` into `~/.hermes/skills/.hub/lock.json`. The
audit reads that verdict, not vibes.

## The 4-tier priority for a "remove risky skills" request

1. **Unambiguously dangerous** — `scan_verdict: "dangerous"` in `.hub/lock.json` with
   `trust_level: "community"`. Move the skill directory to `~/.hermes/skills/.hub/quarantine/`
   and remove its entry from `lock.json` (use `hermes curator` if available, else edit
   the JSON directly). The quarantine dir is pre-built and currently empty.
2. **Wrong platform** — installed but the target environment is wrong. e.g.
   `apple/apple-notes`, `apple/macos-computer-use`, `apple/findmy`, `apple/imessage`
   on a Linux box; `minecraft-modpack-server`, `pokemon-player`, `touchdesigner-mcp`
   on a server with no GUI. Cheap to remove: just `rm -rf` the dir.
3. **Never used** — installed but `last_used_at == null` AND `last_viewed_at == null`
   in `~/.hermes/skills/.usage.json`. Filter out skills the user obviously *might* use
   (e.g. a fresh install) by checking `created_at` recency. The standard 46-skill
   "never used" list is mostly noise — most are correctly named dirs whose base name
   matches a category dir and the flat-name check fires false positives. Confirm by
   checking `last_used_at` AND that the skill actually has a `SKILL.md` on disk.
4. **Stale** — `last_used_at` more than ~14 days ago. Don't remove these on a single
   audit; they may be legitimate low-frequency tools (`csl-policy` itself shows
   23d stale but is the active security gate).

Always present findings as **tiered** so the user can pick scope. They said "remove
risky" not "clean house" — don't silently bundle all tiers together.

## Diagnosis sequence

```bash
# 1. Find hub-flagged skills (the real "risky" set)
cat ~/.hermes/skills/.hub/lock.json | python3 -m json.tool \
  | grep -B1 -A1 'scan_verdict'

# 2. Get the block history (verifies the gate actually fired, not just the verdict)
cat ~/.hermes/skills/.hub/audit.log

# 3. Check the quarantine slot exists and is empty
ls -la ~/.hermes/skills/.hub/quarantine/

# 4. Find never-used installed skills
python3 -c "
import json
data = json.load(open('/home/thomas/.hermes/skills/.usage.json'))
for n,v in sorted(data.items()):
    if v.get('last_used_at') is None and v.get('last_viewed_at') is None:
        print(n)
"
```

## What a "dangerous" verdict means concretely

The `taste-skill` case (the reference example) — `scan_verdict: "dangerous"` with
`6_findings` in audit.log, `trust_level: "community"`, `source: "clawhub"`. The skill
itself is honest about its surface area: "may propose CLI commands, skill folder edits,
onboarding steps, and publish or install actions that require user review." It can
shell out, modify other skills, and propose install/publish actions. That's the shape
of "risky" — broad write/exec surface, low trust provenance.

The reverse case — `baoyu-article-illustrator` shows `scan_verdict: "backfilled"` and
`trust_level: "builtin"`. "Backfilled" is informational (skill was pre-staged from
`optional-skills`, not freshly scanned), not a security flag. Don't conflate the two.

## Skill visibility gotcha

`skills_list` shows skills by the **description's name**, but `skill_view(name="X")`
looks up by **registered manifest name**. The same logical skill can show up as
`taste` in one and `taste-skill` in another (the `taste-skill` directory's manifest
declares the name as `taste`). If `skill_view` returns "not found" for something
`skills_list` shows, the skill may already be inert — or just inconsistently
registered. Either way, the agent can't load it, so removal is low-risk.

## Removing dangerous skills — exact procedure

**Use the CLI primitives, not manual `mv` + JSON edit.** They handle `lock.json`,
`.archive/`, and `.usage.json` updates automatically.

```bash
# 1. ALWAYS take a curator backup first — recoverable rollback if wrong
hermes curator backup

# 2. For HUB-INSTALLED skills (have _meta.json, listed in .hub/lock.json):
#    'dangerous', 'wrong-platform', or 'never-used' hub skills
echo "y" | hermes skills uninstall <skill-name>
#    - Removes the directory
#    - Removes the lock.json entry
#    - Does NOT touch the quarantine/ dir (that's for manual moves)
#    - Prompts for confirm; pipe "y" for non-interactive

# 3. For REGULAR skills (no _meta.json, not in .hub/lock.json):
hermes curator archive <skill-name>
#    - Moves the directory to ~/.hermes/skills/.archive/<basename>/
#    - Reversible: hermes curator restore <name>
#    - Takes the basename only, not the full path
#    - "skill 'X' not found" → already archived OR wrong name (check .archive/)

# 4. Verify the cleanup
cat ~/.hermes/skills/.hub/lock.json | python3 -c "import json,sys; print(list(json.load(sys.stdin)['installed'].keys()))"
ls ~/.hermes/skills/.archive/ | wc -l

# 4. Gateway restart is NOT required for skill removals — skills are read at
#    session start. A /reset in chat is enough.
```

**Cron removal (related):** `hermes cron rm <job-id>` automatically deletes the
matching `cron/output/<job-id>/` directory. Don't `rm -rf` it manually first —
race condition with the next scheduled run can leave a half-deleted state.
Verified live: removing `0e051a9b61b8` (iAgent-windows weekly digest) immediately
after the schedule fired, the output dir was gone within seconds. See the
`skill-evolution` skill's `hermes cron rm cleans its own output dir (2026-06-07)`
note for the full reasoning. The orphan output dir case in `~/.hermes/` audits
is the *opposite* condition — output dir present but job_id not in `jobs.json`
because someone edited `jobs.json` directly (don't do that).

**Manual removal is still valid** if the CLI primitives are unavailable or you need
to keep the directory (e.g. for forensic analysis). The `mv` + JSON-edit path is in
the prior version of this file. Prefer the CLI.

## Pitfalls

- **Don't conflate "backfilled" with "dangerous"** — `scan_verdict: "backfilled"` means
  the skill was pre-staged before the scanner ran. It's a metadata gap, not a security
  finding. The fix is re-running the scanner (`hermes curator` does this on schedule),
  not removing the skill.
- **Don't assume the `csl-policy` gate is the complete defense** — it blocks *new* installs
  of skills with `scan_verdict: "dangerous"` but does NOT quarantine skills that were
  already installed when the verdict was assigned. Verified live: `taste-skill` was
  blocked twice by `tirith` (audit.log shows `BLOCKED ... dangerous 6_findings` ×2) but
  remained `installed: true` in `.hub/lock.json` for 9+ days. A periodic scan of
  `lock.json` for `scan_verdict: "dangerous" AND trust_level: "community"` is
  required — the gate alone won't catch drift. See `references/three-angle-scan.md`
  for the discovery protocol that surfaces this class of issue.
- **Don't remove a thing with emphatic-scope words ("all", "everything", "entirely",
  "completely", "no link to it either way") without first running the three-angle scan
  in `references/three-angle-scan.md`.** These phrases mean the user has noticed a gap
  in past audits. Single-angle searches (path-only, content-only) miss: cron job
  names, hub lock entries, log files in `cron/output/`, references in skill bodies, and
  nested-dir structures. Confirmed live: a path-only `find -iname "*X*"` for "iAgent"
  returned 4 files; a content + relationship scan returned 15+ files across 4 angles.
  When in doubt, ask which "X" the user means before bulk semantic removal — there
  are often two: the *machinery* (skill/scripts/cron) and the *project context*
  (references in your own skills). Removing both when only one was meant is hard
  to reverse.
- **Don't use `skill_manage(action="delete")` on hub-installed skills** — the
  `hermes-agent` skill (bundled) and any skill marked `installed` in `.hub/lock.json`
  is protected. `skill_manage` will refuse; use `hermes skills uninstall` (handles
  `lock.json` automatically) or `mv` + manual JSON edit as fallback.
- **Don't trust `skills_list` as ground truth for "is this skill loaded?"** — it lists
  everything the agent *knows about* including manifest entries that have no local
  `SKILL.md` (e.g. entries in `.bundled_manifest` like `arxiv`, `obliteratus`,
  `macos-computer-use`). Use `find ~/.hermes/skills/ -name SKILL.md` to get the real
  installed set.
- **Don't remove "never-used" sub-skills of a working umbrella** — the
  `productivity/pm-command-center/pm-skills/pm-*` family shows `last_used_at == null`
  on the 36 sub-skills because usage tracking doesn't fire on dashboard-driven
  invocations (`/home/thomas/pm-dashboard.html` → server on `:8765` → generator
  script). They are ACTIVE despite "never used". Before archiving any sub-skill,
  check whether the parent umbrella has a dashboard / server / symlink farm / cron
  that calls it programmatically. **Cross-check pattern:**
  `ls ~/.hermes/scripts/pm-* 2>/dev/null | wc -l` — symlinks = living system.
- **Don't use full path with `hermes curator archive`** — it expects the basename
  (`apple-notes`, not `apple/apple-notes`). The CLI walks category subdirs, so the
  basename is unique.
- **Don't pipe `echo "y"` to `hermes skills uninstall` interactively without
  checking for the prompt** — the command prints `Uninstall '<name>'? Confirm
  [y/N]:` first, then blocks. `echo "y" | ...` works; without it the command
  exits silently.
- **Don't recommend `hermes curator` cleanup for "remove risky"** without first
  reading `.curator_state` — the curator archives into `.archive/` (still queryable),
  it doesn't delete. If Thomas wants the skill *gone*, manual removal is the path.
  (Note: `archive` is the right verb for "I don't want it loaded but might want it
  back" — which covers most "remove risky" cases. Use `mv` to `quarantine/` only
  when the skill is forensically interesting and you want zero chance of re-loading.)

## Cleanup verification checklist

After a tier-1+2+3 cleanup pass, the agent should be able to confirm:

```bash
# Hub-installed count down to "actually used + builtin trust"
cat ~/.hermes/skills/.hub/lock.json | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'  {k}: trust={v[\"trust_level\"]}') for k,v in d['installed'].items()]"

# No dangerous verdicts remaining
cat ~/.hermes/skills/.hub/lock.json | grep -c '"scan_verdict": "dangerous"'   # must be 0

# Curator state shows clean run
hermes curator status | grep -E "agent-created|active|stale|archived"

# PM umbrella intact (if it was in scope)
ls ~/.hermes/skills/productivity/pm-command-center/pm-skills/ | wc -l   # 37
ls ~/.hermes/scripts/pm-* 2>/dev/null | wc -l                            # 37
```

## What "tiered presentation" looks like in practice

When the user says "remove risky skills," present findings in **priority tiers** with
the count per tier. The user picks the scope. Do NOT bundle all tiers into one
auto-execute batch — they've said "risky," not "clean house."

```
Tier 1: Unambiguously dangerous (security-scanner-flagged)  — 1
  taste-skill (scan_verdict: "dangerous", 6 findings, community trust)

Tier 2: Wrong platform (installed but can't function here) — 8
  apple/* (5), minecraft/pokemon (2), spotify/touchdesigner/openhue (3)

Tier 3: Installed but never used                            — 42
  [filtered list, call out false positives like PM sub-skills]

Tier 4: Stale (>14d, may still be useful)                   — 26
  [list]
```

Confirmed: when presented this way, the user said "remove 2 and 3 too" — meaning
"yes, do the tiered removal you proposed." This pattern works. Do not change it.
