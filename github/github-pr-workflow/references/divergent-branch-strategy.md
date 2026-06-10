# Handling Divergent Branches (Upstream Moved)

When upstream pushed changes to the same files you modified locally, `git rebase` produces deep nested conflicts on every attempt. This reference documents the reliable pattern.

---

## The Problem

```
You: modify word.rs, excel.rs
Upstream: modify word.rs, excel.rs (different changes)
Result: rebasing produces nested <<<<<<< HEAD conflicts
Every rebase attempt hits the same conflicts
```

**Symptom:** `git rebase origin/main` fails with conflict, you resolve it, `git rebase --continue`, same files conflict again. Repeat indefinitely.

---

## The Fix: Soft-Reset Squash

When the goal is to land your changes *as a clean overlay* on the new upstream base (not to preserve a merge commit):

```bash
# 1. Confirm what your branch has that origin/main doesn't
git log --oneline origin/main..HEAD
git diff origin/main..HEAD --stat | head -20

# 2. Reset onto origin/main — this UNSTAGED your commits, keeping file content intact
git reset --soft origin/main

# 3. Commit as a single clean squashed change
git commit -m "feat: your feature description"
# Now git diff against origin/main = your exact changes, zero conflicts

# 4. Push directly (fast-forward only)
git push origin main
```

**Result:** One new commit on top of `origin/main`, no conflict resolution needed.

---

## Why This Works

| Approach | What happens |
|----------|-------------|
| `git rebase origin/main` | Git replays each commit. Each commit may conflict on the same files. Nested conflicts. |
| `git merge origin/main` | Git tries to 3-way merge. Conflicts on same files. Manual resolution needed. |
| `git reset --soft origin/main && git commit` | Git moves HEAD to origin/main. All your changes are in the index (unstaged commit). Commit = clean overlay. No merge algorithm runs. |

The soft-reset approach treats your changes as "a patch I want to apply to the new base" rather than "commits I want to replay". It's a pure content overlay.

---

## When to Use Each Strategy

| Situation | Approach |
|-----------|----------|
| Upstream changed different files than you | `git rebase` or `git merge` — no conflicts likely |
| Upstream changed same files as you | `git reset --soft` — bypass conflict resolution |
| You want to preserve commit history (e.g., signed commits) | `git merge` with manual resolution |
| You want a clean, single commit overlay | `git reset --soft` |
| Upstream is empty (brand new repo) | `git push --force` — no rebase/merge needed |

---

## When Unstaged Changes Block the Pull

When you have unstaged changes (e.g. a partially modified file from a failed `git commit` attempt) and the branch is divergent:

```bash
# Unstaged changes block `git pull --rebase`
git stash       # save unstaged work (and stashed commits if any)
git pull --rebase origin main   # now works
git stash pop   # restore unstaged work
```

**Common scenario:** You have a committed change on top of origin/main, but also uncommitted changes in working tree. `git pull --rebase` fails with "You have unstaged changes." — stash, rebase, pop.

**After `git stash pop`:** if there are conflicts from the stashed changes, resolve and `git add . && git commit` or `git stash drop` if clean.

---

## Pre-Flight Before the Reset

Always verify before doing the reset — once done, the intermediate commits are dangling until you commit:

```bash
# See exactly what you're about to lose (they become dangling, not deleted)
git log --oneline origin/main..HEAD

# Verify the file content you want is actually in the working tree
git diff origin/main --stat | head -10
```

---

## If You've Already Done a Failed Rebase

```bash
# Abort the rebase first
git rebase --abort

# Then proceed with soft-reset
git reset --soft origin/main
git commit -m "feat: ..."
git push origin main
```

`git rebase --abort` always restores the pre-rebase state cleanly.

---

## After a Successful Push with Soft-Reset

```bash
# Verify you're on origin/main with a clean history
git log --oneline -3
# Expected: new commit, then origin/main commit, then upstream commits

# Verify the diff is what you expect
git diff origin/main
# Should be empty (origin/main == HEAD)

git diff origin/main^..HEAD --stat | head -10
# Should be your changes
```
