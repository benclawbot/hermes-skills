# New Repository — Extracting a Feature as Standalone Repo

Common traps when pulling a feature from an existing project (e.g., Hermes fork) into its own GitHub repo.

## The default branch trap

When creating a new GitHub repo via `gh repo create` and immediately pushing to it, the **first branch to reach the remote becomes the default branch automatically** — even before the push returns.

- Push `feat/my-feature` first → `main` doesn't exist on the remote yet
- `gh pr create --base main` fails with "Base sha can't be blank"
- Fix: always check first: `gh api repos/owner/repo --jq '.default_branch'`
- If wrong branch is default, push main explicitly:
  ```bash
  git push newremote $(git rev-parse upstream/main):refs/heads/main
  ```

## The README persists trap

Even after pushing clean code, the original README can survive on the remote because:
1. `git rm file` only stages deletion — doesn't remove from index until commit
2. If deletion never committed, the old blob still exists on the remote

## The correct extraction sequence

Do NOT copy into the old repo directory and try to clean it up. Build clean from scratch:

```bash
# 1. Create clean destination
mkdir -p /tmp/feature-standalone && cd /tmp/feature-standalone

# 2. Audit imports BEFORE copying — check for host project dependencies
grep -rn "^from \|^import " /path/to/feature-src/ \
  | grep -v "^from \." | grep -v "^import typing" | grep -v "^import json"
# Any matches against the host project = rewrite required first

# 3. Build clean content with rsync (excludes foreign files)
rsync -a --exclude '__pycache__' --exclude '.pytest_cache' \
  --exclude '*.pyc' --exclude '__pycache__/' \
  /path/to/feature-src/ .

# 4. THEN init git — not before copying
rm -rf .git && git init
git add -A && git commit -m "Initial commit — feature-name v0.1.0"
git branch -M main

# 5. Verify what will be pushed
git log --oneline -3    # confirm only feature commits
git status              # confirm no stale files

# 6. Push (use token in URL if no ssh access)
git push -f https://TOKEN@github.com/owner/feature-repo.git main
```

**Why this order matters:**
- `rm -rf .git` + `git init` = zero foreign commit history
- `rsync` before init = no git operations touch source during copy
- Force push to fresh git init state = no residual blobs from the fork

## Fix README via GitHub API (if already persisted on remote)

```bash
SHA=$(gh api repos/owner/repo/contents/README.md?ref=main --jq '.sha')
gh api repos/owner/repo/contents/README.md \
  -X PUT \
  -f message="docs: replace with feature README" \
  -f content="$(base64 -w0 < /path/to/new/README.md)" \
  -f sha="$SHA"
```

## Always verify after push

```bash
# Check actual remote content
gh api repos/owner/feature-repo/git/trees/main?recursive=true \
  --jq '.tree[] | .path' | head -20

# Confirm README content
gh api repos/owner/feature-repo/contents/README.md?ref=main \
  --jq '.content' | base64 -d | head -10
```

Should show only the feature's files — no host project artifacts.

## Confirm intent: PR vs standalone

Only open a PR if contributing back to the host repo. If the goal is a standalone project, just push `main` — no PR needed. Opening a PR against a nonexistent or unrelated target fails.

```
User: "make X its own thing" → clean push to main, no PR
User: "open a PR to [host]" → create PR to host repo
```

When in doubt, ask before opening a PR.