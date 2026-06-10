# Rebasing a PR Branch After Fork/Local Sync

**Class of problem:** You opened a PR from `myfork:fix/my-branch` based on an old commit of `origin/main`. Then you (or the watchdog) rebase your local `main` against current upstream. The PR is still open and the diff is still correct, but the branch on the fork is now at a stale SHA. The fork's `main` and your local `main` are in sync, but the *PR branch* is not.

**Why this matters:** Reviewers see a PR diff between the branch tip and `upstream:main`. If the branch tip is on an old base, the diff still shows the right files (the branch's changes) — but any new commits on the branch after the original push will be missing, and force-pushes from the user's local will silently fail or create a non-fast-forward. Worse, the SHA on the PR page no longer matches the SHA the user just committed locally.

## Symptoms

- You ran `git rebase origin/main` on your local main and pushed to the fork
- The PR is still open at the old URL but the local main is on a new SHA
- `gh pr view <N> --json headRefName,sha` shows a SHA that doesn't match `git rev-parse <branch>`
- Subsequent edits to the branch locally don't appear in the PR

## The Fix: Force-Push the Branch (Not main) After Rebase

**Important distinction:** When you have a feature branch with an open PR, **never rebase and push `main`**. You rebase the *feature branch* and force-push the *feature branch* to the fork. The PR's diff is computed against `main` on the upstream repo, so the diff content (the branch's changes) stays correct.

### Step-by-step

```bash
# 1. Local main was rebased; local feature branch is now based on old main.
#    Rebase the feature branch onto the new local main.
git checkout fix/my-branch
git rebase main
# If no conflicts: success. If conflicts: resolve, git rebase --continue.

# 2. Verify the diff content is unchanged
git diff main...HEAD --stat
# Should show the same file changes as before the rebase

# 3. Force-push the branch to the fork (NOT main)
git push fork fix/my-branch --force
# Use --force-with-lease if you want a safety check:
git push fork fix/my-branch --force-with-lease

# 4. Verify the PR is now at the new SHA
gh pr view <N> --json headRefName,headRefOid --jq '"\(.headRefName) @ \(.headRefOid[0:7])"'
# Compare to:
git rev-parse --short fix/my-branch
# Should match.
```

### Why --force and not just --force-with-lease

`--force-with-lease` checks that the remote branch tip matches what you last saw (in `origin/<branch>` or your last fetch). If you rebased the branch and have a newer SHA locally, the lease check will fail unless you also `git fetch fork` and update the local ref. For a solo workflow where you're the only one pushing, `--force` is fine. If collaborators exist on the branch, `--force-with-lease` is safer.

## The "Diff Is Byte-Identical" Property

**Surprising observation:** When none of the 79 (or N) upstream commits touch any of the files in your local feature commit, the rebase produces a **byte-identical diff**:

- Before rebase: `git diff <old_base>..HEAD` = +1035/-13 across 8 files
- After rebase: `git diff <new_base>..HEAD` = +1035/-13 across 8 files (same 8 files)
- The PR's "+1035/-13 across 8 files" stays the same on the PR page

**Why:** A rebase replays your commit on top of a new base. If the new base is a pure superset of the old base (no overlapping changes), the rebase is a no-op for the diff content. Git rewrites the SHA (because parent changed) but the *patch* is identical.

**Implication:** This is a strong pre-flight signal. Before force-pushing, run:
```bash
git diff <old_base>..HEAD --stat > /tmp/before.txt
git diff <new_base>..HEAD --stat > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
# If empty: byte-identical. Safe to force-push.
```

**Pre-rebase proof technique (cheap, run this FIRST):** Before even attempting the rebase, prove that no upstream commit touches any of your files. Faster than doing the rebase and checking the diff after.

```bash
# After fetching origin/main, for each file in your feature commit, ask: did any
# upstream commit touch it since my base?
BASE_SHA=$(git merge-base HEAD origin/main)
HEAD_SHA=$(git rev-parse HEAD)
FILES=$(git diff-tree --no-commit-id --name-only -r "$BASE_SHA".."$HEAD_SHA")

for f in $FILES; do
  # Count upstream commits touching this file in the behind range
  upstream_hits=$(git log "$BASE_SHA"..origin/main --oneline -- "$f" | wc -l)
  if [ "$upstream_hits" -gt 0 ]; then
    echo "CONFLICT RISK: $f — $upstream_hits upstream commit(s) since base"
  fi
done
# If no "CONFLICT RISK" lines: byte-identical rebase is guaranteed (modulo whitespace).
# If conflict-risk lines: rebase may need manual resolution.
```

**Real example (June 2026):** A feature commit touched 8 files. Ran the loop above against 79 upstream commits. Zero conflict-risk lines. The rebase that followed produced a byte-identical diff in <1 second with no manual intervention, and the force-push updated the PR's SHA without changing the diff. ~30-second investment that catches 90%+ of rebase risk before you commit to the rebase.

## When the PR Branch Doesn't Exist Locally

If you lost the branch (cleaned up, new clone) but the PR is still open:

```bash
# Restore the branch from the PR
gh pr checkout <N>
# This creates the branch locally tracking origin/<branch>

# Now you can rebase and force-push as normal
git rebase main
git push fork HEAD --force
```

## Common Pitfalls

### Pushing main instead of the branch

```bash
# WRONG — this would update fork/main, breaking other PRs and the watchdog's assumptions
git push fork main --force

# RIGHT — only the feature branch
git push fork fix/my-branch --force
```

### Forgetting the rebase produces a new SHA

The new SHA after rebase is *not* the same as the old SHA. If you have downstream tooling that pins to the old SHA (e.g. a "chore: rebase PR #N" line in a commit message), update those references.

### "But the diff is the same — do I really need to force-push?"

Yes, because GitHub's PR page records the SHA. If the SHA on the page is `abc123` but your local is `def456`, GitHub will still show the diff, but:
- New commits you add to the branch won't appear in the PR
- A reviewer running `git fetch origin pull/N/head` will get the old SHA
- A bot that posts "outdated" check on SHA will be confused

## Preflight: Verify Fork Health Before Opening PR

The mistake that creates the need for this whole reference is opening a PR without checking the fork's health first. Add this to your pre-PR checklist:

```bash
# Quick: how far behind is the fork's main?
gh api repos/OWNER/REPO/compare/main...UPSTREAM:main \
  --jq '{ahead: .ahead_by, behind: .behind_by}'
# If behind > 25, sync the fork BEFORE opening the PR.

# Or use the existing script:
python3 ~/.hermes/skills/github/github-pr-workflow/scripts/check-fork-staleness.py \
  FORK_OWNER REPO UPSTREAM_OWNER/UPSTREAM_REPO
```

If the fork is stale, fix it first (see `references/fork-staleness-watchdog.md`). Then open the PR. This avoids the "I opened a PR from a stale fork and now the diff is on a non-current base" scenario entirely.

## Related

- `references/divergent-branch-strategy.md` — soft-reset squash for `main` branch (different scenario: no PR open)
- `references/fork-staleness-watchdog.md` — diagnosing/fixing the underlying fork health problem
- `references/fork-workflow.md` — opening PRs from a fork in general
- `scripts/check-fork-staleness.py` — automated fork health check
