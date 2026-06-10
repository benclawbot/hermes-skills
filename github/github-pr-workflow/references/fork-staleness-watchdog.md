# Fork Staleness via Watchdog Auto-Commits

**Class of problem:** A fork's `main` branch silently drifts far behind upstream because a cron / watchdog script auto-commits and pushes to the fork without ever `git fetch`ing from the upstream remote. The fork keeps accepting writes, so the push *succeeds*, but the fork's `main` is increasingly meaningless.

## Symptoms

- `git status` on a clone of your fork shows:
  ```
  Your branch and 'origin/main' have diverged,
  and have 4 and 328 different commits each, respectively.
  ```
  (Some commits ahead of *your* local, hundreds of commits behind upstream.)
- Opening a PR from this fork's `main` works — the diff is *correct* — but the fork's `main` is so stale that any other developer who clones it will see a misleading picture.
- Multiple `chore: auto-commit from watchdog` commits accumulate on the fork, often with little to no actual code change — just timestamp churn.

## Root Cause

A watchdog / cron script (e.g. `project-health-watchdog` auto-pushing uncommitted changes) does:

```python
# Anti-pattern — DO NOT USE
git add .
git commit -m "chore: auto-commit from watchdog"
git push https://user:TOKEN@github.com/USER/REPO.git HEAD:main
```

Two compounding mistakes:

1. **No `git fetch origin` before commit+push.** The local clone (the source of the commits) may itself be N commits behind upstream. The watchdog happily piles more commits on top, widening the gap.
2. **Hardcoded PAT in the push URL.** This was likely a workaround for "gh not in cron $PATH" or "credential helper broken" — it works, but:
   - Leaks the token (it's now in the script file, in `git log` if the URL was ever echoed, in the process list at push time)
   - Bypasses `gh auth`, which is the supported, scoped, revocable path
   - Silently keeps working after the token is rotated, used elsewhere, or expires

The result is a fork that's a "write-only" surface — accepting whatever the watchdog shovels at it, never reflecting upstream.

## Diagnosis (5-Question Audit)

When you suspect a fork is stale:

```bash
# 1. Compare fork's main to upstream main
gh api repos/USER/REPO/compare/main...UPSTREAM:main --jq '{ahead: .ahead_by, behind: .behind_by, status: .status}'

# 2. Count commits on the fork that aren't in upstream
git fetch upstream  # (after adding it as a remote, if not present)
git log upstream/main..origin/main --oneline

# 3. Look for the smoking-gun commit pattern
git log origin/main --oneline | grep -E "(auto-commit|watchdog|chore: auto)" | head -20

# 4. Check if any commits have actual content vs. just metadata
git log origin/main --stat | head -50

# 5. Inspect the watchdog script itself for the anti-pattern
grep -nE "(ghp_|github.*TOKEN|git push.*https.*:.*@)" /path/to/watchdog.py
```

If 1+3+4 are positive, the fork is being polluted. If 5 matches, you've found the source.

## The Fix (3 Layers)

### Layer 1: Stop the Bleeding — Pause or Fix the Watchdog

```bash
# Pause the cron job
hermes cron pause <job_id>

# OR: fix the script before the next tick
```

If you choose to fix, replace the auto-commit+push pattern with a safer one (see Layer 3 below).

### Layer 2: Sync the Fork to Upstream

The fork's `main` is currently N commits ahead and M commits behind. To make it useful again:

```bash
# 1. Add upstream as a remote (if not present)
git remote add upstream https://github.com/UPSTREAM_OWNER/REPO.git

# 2. Fetch upstream
git fetch upstream

# 3. In your local clone of the FORK, force-sync main to upstream
git checkout main
git reset --hard upstream/main
git push --force-with-lease origin main
```

This nukes the polluted `chore: auto-commit from watchdog` history. **Back up first** if any of those commits contain real work:

```bash
# Before the reset, save the polluted state
git bundle create /tmp/fork-polluted-state.bundle origin/main --all
```

To check whether any "real" work is in the pollution:

```bash
git log origin/main --grep="auto-commit" --oneline
# If all of them are "chore: auto-commit from watchdog" with empty diffs → safe to nuke
# If any contain real file changes → review with `git show <sha>` and extract
```

### Layer 3: Replace the Watchdog Pattern

The replacement pattern has three guarantees:

```python
import subprocess

def run(cmd, cwd=None, timeout=15):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

MAX_BEHIND = 25  # refuse to push if local is more than this far behind upstream/main

def safe_auto_commit_and_push(repo_path, fork_repo):
    """Auto-commit+push with staleness guard and no hardcoded tokens."""
    # 1. ALWAYS fetch origin first
    rc, _, err = run("git fetch origin", cwd=repo_path, timeout=30)
    if rc != 0:
        return f"fetch failed: {err[:100]}"

    # 2. Count how far behind we are — refuse to push if too stale
    rc, out, _ = run("git rev-list --count HEAD..origin/main", cwd=repo_path, timeout=10)
    behind = int(out) if out.isdigit() else 0
    if behind > MAX_BEHIND:
        return f"refusing: local is {behind} commits behind origin/main (>{MAX_BEHIND})"

    # 3. Stage, commit, push — using gh auth, NOT a hardcoded token
    run("git add .", cwd=repo_path, timeout=10)
    rc, _, err = run('git commit -m "chore: auto-commit from watchdog"', cwd=repo_path, timeout=10)
    if "nothing to commit" in err.lower():
        return None  # not an error

    # gh auth handles the token — no URL-embedded credentials
    rc, _, err = run(
        f"git push https://github.com/{fork_repo}.git HEAD:main",
        cwd=repo_path, timeout=30
    )
    return None if rc == 0 else f"push failed: {err[:100]}"
```

**Key properties of this pattern:**
- `git fetch origin` runs first, every time, no exceptions
- Behind-count check refuses to push when local is too far behind upstream — surface as "needs attention" instead of polluting
- Push URL is `https://github.com/OWNER/REPO.git` — no token. Auth flows through `gh auth setup-git` (configured once) or the git credential helper
- "Nothing to commit" is treated as a no-op, not an error

## Lesson: PRs from a Stale Fork Are Still Valid

**A surprising property:** a PR opened from a stale fork is *correct* if the diff itself is correct. GitHub compares the *branch* to the *target*, not the fork's main to the target's main. So if you push `fix/my-branch` to a stale fork, that branch may be based on an old commit, but the PR diff against current `main` is still a meaningful diff.

**However:**
- Reviewers may be confused if they browse your fork
- Future PRs from the same fork may accumulate unfixable merge conflicts
- The fork becomes a write-only surface over time

**Action:** Sync the fork before opening PRs from it. The PR's diff is correct; the *hygiene* of the fork matters for the next contributor.

## When to Use This Skill

- Fork is showing "X ahead / Y behind" with Y being suspiciously large (hundreds+)
- A cron job is auto-committing to a GitHub repo and pushing to your fork
- You see repeated `chore: auto-commit` commits in `git log` with empty/meaningless diffs
- `gh api repos/USER/REPO` shows the fork's default branch is way behind the source

## Applying a Local Edit to a Stale Fork Cleanly

Different scenario: you've made a local edit, the fork is stale, and you need to push the edit to the fork. The naive flow loses the edit.

**Wrong order (loses the edit):**
1. Make the local edit (e.g. via `patch` tool)
2. Commit it locally → `git commit -m "..."` (commit `X` exists on local main)
3. `git push` to fork → fails because fork is behind upstream (`! [rejected] non-fast-forward`)
4. `git pull --no-rebase fork main` → conflicts in files you didn't touch (because the watchdog committed to the same lines)
5. Resolve conflicts by deletion of conflict markers → **destroys your original edit's content**
6. `git reset --hard fork/main` to clean up → your edit is now ONLY in the reflog as commit `X`
7. `git cherry-pick X` → conflicts again on the same lines
8. Hand-repair the patch by re-applying it from scratch

This is the "reset + cherry-pick + manual repair" loop. It works as recovery but it's not a flow.

**Right order (preserves the edit):**
1. Make the local edit
2. Commit it locally → `git commit -m "..."` (commit `X` exists on local main)
3. `git fetch fork main`
4. `git reset --hard fork/main` — *kills your working edit, but the commit is in the reflog*
5. `git cherry-pick <X>` — *now cherry-pick onto a clean fork/main*
6. Resolve any conflicts using your original commit as the source of truth (`git show <X>`)
7. `git push fork main`

**Or, even simpler — bypass the reflog dance entirely:**

1. Make the local edit
2. Save the patch: `git diff > /tmp/my.patch` (or `git format-patch -1` if already committed)
3. `git reset --hard fork/main` — clean state
4. `git apply /tmp/my.patch` — re-apply the edit on the clean tree
5. `git add -A && git commit -m "..."`
6. `git push fork main`

The diff-to-file-and-re-apply flow has two advantages: it doesn't require a local commit to exist before reset, and it works even if the working edit was never committed (only `git diff` can capture it).

**When this matters:** any time you're working on a fork that has a watchdog / auto-commit / parallel-writer. Don't try to merge or cherry-pick — reset to the fork's current main, then re-apply your work. The merge is what destroys the edit; the reset is what makes the re-apply clean.

**Recovery if you already did the wrong order:**
- The reflog has the lost commit. `git reflog | grep "<your commit message>"` finds the SHA.
- `git show <sha>` confirms the diff is intact.
- Then follow the "right order" steps starting at step 5.

## Related

- `references/fork-workflow.md` — creating a fork, opening PRs from it, keeping your *branch* up-to-date
- `references/push-auth-troubleshooting.md` — fixing HTTPS push auth failures (the reason people hardcode PATs in URLs in the first place)
- `autonomous-ai-agents/cronjob-ops` — cron-side view: "if your cron auto-commits, fetch first"
