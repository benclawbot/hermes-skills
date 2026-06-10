# Fork-Based PR Workflow

When you have read access to a repo but not write access, use a fork-based workflow.

## The Core Problem

`git push` to origin fails with `403 Permission denied`. This happens when:
- You're working on someone else's repo (e.g., NousResearch/hermes-agent)
- Your token/ssh key only has read access to the canonical repo

## Solution: Fork + PR

### Step 1: Create Fork via GitHub API

```bash
OWNER="NousResearch"
REPO="hermes-agent"

# Create fork (GitHub API handles "already exists" gracefully)
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/forks | python3 -c "
import sys, json
d=json.load(sys.stdin)
if 'full_name' in d:
    print('Fork created:', d['full_name'])
else:
    print('Fork exists or error:', d.get('message', d))
"
```

### Step 2: Add Fork as Remote

```bash
# Your GitHub username
FORK_OWNER="your-github-username"
FORK_REPO="hermes-agent"
FORK_URL="https://github.com/$FORK_OWNER/$FORK_REPO.git"

git remote add fork "$FORK_URL" 2>/dev/null || \
  git remote set-url fork "$FORK_URL"

git remote -v  # verify
```

### Step 3: Push to Fork

```bash
git push -u fork HEAD
```

### Step 4: Create PR from Fork to Origin

```bash
# gh way
gh pr create --repo "$OWNER/$REPO" --title "..." --body "..."

# git+curl way
BRANCH=$(git branch --show-current)
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"Your PR Title\",
    \"body\": \"Description\",
    \"head\": \"$FORK_OWNER:$BRANCH\",
    \"base\": \"main\"
  }"
```

Note: The `head` field must be `fork_owner:branch_name` format, not just `branch_name`.

### Step 5: Keep Fork Up-to-Date with Origin

```bash
# Add upstream remote if not present
git remote add upstream "https://github.com/$OWNER/$REPO.git" 2>/dev/null || true

# Fetch upstream and rebase your branch on main
git fetch upstream
git checkout your-branch
git rebase upstream/main

# Force push to fork (rebase rewrites history)
git push --force-with-lease fork HEAD
```

## Checklist Before Starting Fork Workflow

```bash
# 1. Test push access
git push --dry-run origin HEAD 2>&1 | grep -E "(Permission|denied|error)" && echo "NO_WRITE"

# 2. Check existing remotes
git remote -v

# 3. Check gh auth
gh auth status 2>&1 | grep -E "(Failed|X|Error)" && echo "GH_AUTH_INVALID"
```

## Common Error: Fork Already Exists

When creating a fork via API and it already exists, GitHub returns `202` (accepted) and the fork is just available. Parse the `full_name` from the response and use it — don't treat it as an error.

```python
# Safe fork creation pattern
response = requests.post(f"https://api.github.com/repos/{owner}/{repo}/forks",
                        headers={"Authorization": f"token {token}"})
if response.status_code in (200, 201, 202):
    fork_full_name = response.json()["full_name"]  # e.g. "benclawbot/hermes-agent"
    fork_owner, fork_repo = fork_full_name.split("/")
elif response.status_code == 401:
    raise Exception("Invalid token")
elif response.status_code == 403:
    raise Exception("No permission to fork")
```