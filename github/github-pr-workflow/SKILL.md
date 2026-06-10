---
name: github-pr-workflow
description: "GitHub operations: authentication setup, PR lifecycle, code review, issues, repo management."
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Authentication, Pull-Requests, CI/CD, Git, Automation, Merge, Code-Review, Issues]
    related_skills: [github-auth, github-code-review]
---

# GitHub Workflows

Complete guide for GitHub operations: PR lifecycle, code review, issues, and repository management. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

> **Auth prerequisite:** See Authentication section below for token/SSH setup. (Was previously a separate `github-auth` skill — content absorbed into this skill.)
> **gh path:** Always use `/home/thomas/bin/gh` — `/usr/bin/gh` doesn't exist on this system. See `references/gh-path-note.md`.

## Skills Map

| Task | Skill |
|------|-------|
| PR: branch, commit, open, CI, merge | *(this skill — github-pr-workflow)* |
| PR: review, diff, inline comments | *(this skill — github-code-review section)* |
| Issues: create, triage, label, assign | *(this skill — github-issues section)* |
| Repo: clone, create, fork, releases, secrets | *(this skill — github-repo-management section)* |
| Auth: token setup, SSH, gh login | *(this skill — Authentication section below — absorbed from `github-auth`)* |

## Safety — Preventing Credential Leaks to GitHub

These are the root causes of credential exposure in commits. Apply before any `git add`, `git commit`, or `git push`:

### 1. Build artifacts must never enter git

Block-list these patterns from `git add`/`git commit`:
- `.wrangler/`, `dist/`, `build/`, `node_modules/`
- `*.map` (source maps often embed original source with secrets)
- `.env`, `.env.*`, `*.pem`, `*.key`

If any of these are already tracked, remove from index and history:
```bash
git rm -r --cached .wrangler/
git filter-branch --force --index-filter \
  "git rm -r --cached --ignore-unmatch .wrangler/" \
  --prune-empty -- --all
git push --force
```

### 2. Pre-push staging check is mandatory

Before every `git push`:
```bash
git status
git diff --cached --name-only   # what's staged?
git diff --name-only           # what's unstaged?
```
Scan the output for secrets, `.env` files, build artifacts, or unexpected paths. If anything looks wrong, abort.

### 3. First-push to a new repo: validate `.gitignore` exists

If `.gitignore` is missing, the next commit will sweep in everything. Verify it covers secrets and build output before the first push.

## Common Setup

- Authenticated with GitHub (see Authentication section above)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH=***  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=*** ~/.hermes/.env; then
      GITHUB_TOKEN=*** "^GITHUB_TOKEN=*** ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=*** "github.com" ~/.git-credentials 2>/dev/null | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
```

## Authentication (Setup)

*Absorbed from `github-auth` — set up authentication before any workflow in this skill.*

This skill sets up authentication so the agent can work with GitHub repositories, PRs, issues, and CI. It covers two paths:

- **`git` (always available)** — uses HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access with a simpler auth flow

### Detection Flow

When a user asks you to work with GitHub, run this check first:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Decision tree:**
1. If `gh auth status` shows authenticated → you're good, use `gh` for everything
2. If `gh` is installed but not authenticated → use "gh auth" method below
3. If `gh` is not installed → use "git-only" method below (no sudo needed)

### Method 1: Git-Only Authentication (No gh, No sudo)

This works on any machine with `git` installed. No root access needed.

#### Option A: HTTPS with Personal Access Token (Recommended)

This is the most portable method — works everywhere, no SSH config needed.

**Step 1: Create a personal access token**

Tell the user to go to: **https://github.com/settings/tokens**

- Click "Generate new token (classic)"
- Give it a name like "hermes-agent"
- Select scopes:
  - `repo` (full repository access — read, write, push, PRs)
  - `workflow` (trigger and manage GitHub Actions)
  - `read:org` (if working with organization repos)
- Set expiration (90 days is a good default)
- Copy the token — it won't be shown again

**Step 2: Configure git to store the token**

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

After entering credentials once, they're saved and reused for all future operations.

**Alternative: cache helper (credentials expire from memory)**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**Alternative: set the token directly in the remote URL (per-repo)**

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**Step 3: Configure git identity**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**Step 4: Verify**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

#### Option B: SSH Key Authentication

Good for users who prefer SSH or already have keys set up.

**Step 1: Check for existing SSH keys**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**Step 2: Generate a key if needed**

```bash
# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

Tell the user to add the public key at: **https://github.com/settings/keys**
- Click "New SSH key"
- Paste the public key content
- Give it a title like "hermes-agent-<machine-name>"

**Step 3: Test the connection**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Step 4: Configure git to use SSH for GitHub**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**Step 5: Configure git identity**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

### Method 2: gh CLI Authentication

If `gh` is installed, it handles both API access and git credentials in one step.

#### Interactive Browser Login (Desktop)

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

#### Token-Based Login (Headless / SSH Servers)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

#### Verify

```bash
gh auth status
```

### Using the GitHub API Without gh

When `gh` is not available, you can still access the full GitHub API using `curl` with a personal access token.

**Setting the token for API calls** — see `Quick Auth Detection` above for the auto-extract path. Manual:

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

**Extracting the token from git credentials:**

```bash
# Read from git credential store
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

**Helper script (auto-detect auth method):** `scripts/gh-env.sh` — sources the env vars `GH_AUTH_METHOD`, `GITHUB_TOKEN`, `GH_USER`, `GH_OWNER`, `GH_REPO` based on what's available. Use this at the top of any GitHub workflow script:

```bash
source scripts/gh-env.sh
echo "Authenticated as: $GH_USER (method: $GH_AUTH_METHOD)"
```

### Authentication Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth. Use a personal access token as the password, or switch to SSH |
| `remote: Permission to X denied` | Token may lack `repo` scope — regenerate with correct scopes. **If gh shows a valid account but push still 403s**, the token is valid but the account lacks write access to this specific repo. Fall back to fork workflow. |
| `gh auth status` shows account but `git push` still fails with 403 | The `gh` account is authenticated for GitHub API access but its token may not have push rights to the specific repo. Diagnose with the per-repo HTTP code check from `github-pr-workflow` Section 3. |
| `gh auth status` shows authenticated but `git push` still fails with 403 with "Invalid username or token" | The credential helper is broken. Push with token embedded directly: `git push https://<user>:$(gh auth token)@github.com/<user>/<repo>.git`. |
| `remote: Invalid username or token` on every push despite `gh auth status` showing valid account | HTTPS credential helper is broken system-wide. **Fix**: Switch to SSH — generate key, add to GitHub, switch remote to SSH. |
| `fatal: Authentication failed` | Cached credentials may be stale — run `git credential reject` then re-authenticate |
| `ssh: connect to host github.com port 22: Connection refused` | Try SSH over HTTPS port: add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper` — must be `store` or `cache` |
| Multiple GitHub accounts | Use SSH with different keys per host alias in `~/.ssh/config`, or per-repo credential URLs |
| `gh: command not found` + no sudo | Use git-only Method 1 above — no installation needed |

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 0. Confirm Intent Before Creating PRs

**Before opening a PR, confirm the goal.** A PR is only correct when the project is meant to contribute BACK to a host repo. If the goal is a standalone project, just push clean code to `main` — no PR needed.

Common mistake: agent opens a PR to the original repo because it was working in a fork of that repo. The user may only want the feature as a standalone project.

```
User: "I want Agent Commit as its own thing" → push clean main, no PR
User: "Open a PR to Hermes" → create PR to host repo
```

When in doubt, ask: "Push clean code and open a PR against [target], or just make it a standalone project?"

### Confirm Intent Before Public-Facing GitHub Actions

PRs aren't the only high-blast-radius action. **Creating a new public repo** (`gh repo create --public --push`) is a *bigger* commitment than opening a PR — it instantly publishes code to the world. Other actions in the same blast-radius class:

| Action | Blast radius | Confirm? |
|--------|--------------|----------|
| `gh repo create --public --push` | instant public code publish | **yes, always** |
| `gh repo create --private` | creates a repo under your account | yes, but lower stakes |
| `gh repo edit --visibility public` | flips existing repo to public | **yes, always** |
| Push to existing public repo | adds commits to public history | confirm first push of new content; subsequent pushes fine |
| Open PR to host repo | proposes a change to upstream | confirm the target |
| Fork a repo | creates a repo under your account | usually fine |
| Edit GitHub secrets/org settings | security-impacting | **yes, always** |

**Pitfall (learned 2026-06, self-recursive-improvement session):** the agent ran `gh repo create benclawbot/self-recursive-improvement --public --source . --push` *without confirming first*. The user had to flag it. The repo was fine to keep, but the rule stands: any action that **publishes code publicly for the first time** needs explicit confirmation, even if "make this public" was the eventual goal.

**Auditing a freshly-public repo for leaks:** before declaring success, scan for secrets the loop may have inadvertently written:

```bash
# Scan all source-like files for credential patterns
grep -rEi "api[_-]?key|secret|token|password|bearer" \
  --include="*.py" --include="*.md" --include="*.yaml" --include="*.yml" --include="*.json" \
  -l . | xargs -I{} sh -c \
  'echo "=== {} ==="; grep -nEi "api[_-]?key|secret|token|password|bearer" {} | \
   grep -vE "(_KEY|_TOKEN|getenv|environ|env var|env variable|key is|API_KEY not set|set the|MINIMAX_API_KEY|TELEGRAM_BOT|env\.)"'

# Verify .gitignore covers runtime state
grep -E "(\.env|\*\.log|loop\.db|backups/|__pycache__)" .gitignore
```

A repo is "safe to make public" when: (1) all env-var references are `os.environ.get(...)` and never literal values, (2) `.gitignore` excludes `.env*`, runtime DBs, and logs, (3) no `*.pem` / `id_rsa*` / `id_ed25519*` files are tracked.

---

## 1. Pre-Flight: Verify Push Access

**Always run this BEFORE making commits** on a branch meant for a PR:

```bash
# Test push access to origin
git push --dry-run origin HEAD 2>&1
PUSH_OK=$?

if [ $PUSH_OK -ne 0 ]; then
  echo "No push access to origin — checking for fork remote..."
  # Check if a fork remote already exists
  git remote -v | grep -E "(fork|push)" && echo "Fork remote found"
  # Diagnose: gh auth status
  gh auth status 2>&1 | head -5
fi
```

**If push fails and a fork remote exists:** use the fork remote for pushes, keep origin for PR creation. Never make commits on a branch you can't push.

**The fork remote may already exist** (`git remote -v` shows it) even if push fails — this means the token/ssh key doesn't have write access to the fork. Use the fork-based workflow in Section 3.

**If no fork remote exists:** use the `gh api` fork creation + fork remote setup in Section 3, then push to the fork.

**Pitfall — the fork may exist but be a write-only surface:** Even when the fork remote is present and pushes succeed, the *fork's main branch* may be hundreds of commits behind upstream because a watchdog has been auto-committing to it without ever `git fetch`ing from origin. PRs from such a fork are still *valid* (GitHub compares the branch to the target, not the fork's main) but the fork is unhealthy. See `references/fork-staleness-watchdog.md` for diagnosis (5-question audit), the 3-layer fix (pause watchdog / sync fork / replace pattern), and a "PRs from stale forks are still valid" note.

**Pre-flight before opening a PR from a fork:** check the fork's main is reasonably current. A fork with `behind > 25` should be synced first — otherwise the PR's branch will sit on a non-current base and need a separate rebase + force-push (see `references/pr-branch-rebase-after-fork-sync.md`). One-liner: `gh api repos/OWNER/REPO/compare/main...UPSTREAM:main --jq '{ahead: .ahead_by, behind: .behind_by}'`.

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

### Push Troubleshooting

If `git push` fails with `403` or `permission denied`:

**1. Diagnose the token:**
```bash
# Check which token is being used
gh auth status 2>&1

# Extract token from git-credentials if gh is not usable
GIT_CREDS_TOKEN=*** ~/.git-credentials 2>/dev/null | grep github.com | head -1 | sed 's|https://[^:]*:||; s|@github.com||')

# Test token permissions against the repo
OWNER_REPO=$(git remote get-url origin | sed -E 's|.*github\.com[:/]||; s|\.git$||')
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token $GIT_CREDS_TOKEN" \
  https://api.github.com/repos/$OWNER_REPO
# 200 = read+write, 404 = no access, 403 = read-only
```

**2. If token lacks write access — fork and push to fork:**
```bash
# Get the canonical URL to extract owner/repo
CANONICAL_URL=$(git remote get-url origin | sed 's|https://[^@]*@|https://|')

# Fork via GitHub API (requires write access to original to create fork)
# If fork already exists, just note it
OWNER_REPO=$(echo "$CANONICAL_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')

# Create a fork (GitHub API handles "already exists" gracefully)
FORK_OWNER="YOUR_GITHUB_USERNAME"  # Replace with actual username
FORK_URL="https://github.com/$FORK_OWNER/$(echo $OWNER_REPO | cut -d/ -f2)"

# Add fork as a new remote and push there
git remote add fork "$FORK_URL" 2>/dev/null || true
git push -u fork HEAD

# Then open PR from fork → canonical repo via gh or curl
gh pr create --repo "$OWNER_REPO" --title "..." --body "..."
```

**5. `gh auth git-credential` (primary fix on Linux when gh is available):**
When HTTPS push fails with `could not read Username for 'https://github.com': No such device or address` and `gh auth status` shows a valid login, the credential helper/keyring system is broken. Use gh's built-in credential helper with the full gh path:

```bash
# Find gh path first — may not be in PATH from git's perspective
GH_PATH=$(which gh 2>/dev/null)
git config --global credential.helper "$GH_PATH auth git-credential"
git push origin main
```

**Why this works:** `gh auth git-credential` reads from gh's keyring directly, bypassing broken system credential helpers. The full path is required since gh may be installed at `/home/thomas/bin/gh` rather than `/usr/bin/gh` and git's credential helper doesn't inherit the shell's PATH.

**Post-push cleanup:** Always verify the remote URL contains no embedded credentials:
```bash
git remote -v | grep "github.com" | grep -v "@" && echo "Clean ✓"
```

If `gh auth token` fails (not installed), extract from `~/.git-credentials` or use `git config credential.helper` to clear the broken helper, then retry.

```bash
ssh-keygen -t ed25519 -C "your_email@github.com" -f ~/.ssh/id_ed25519 -N ""
gh api user/keys -X POST -F title="$(hostname)-$(date +%Y%m%d)" -F key="$(cat ~/.ssh/id_ed25519.pub)" 2>/dev/null || echo "Add key manually at github.com/settings/keys"
git remote set-url origin git@github.com:OWNER/REPO.git
git push origin main
```

**6. New Repo Default Branch Issue**
When HTTPS push is broken system-wide and credential helper fixes fail, switch to SSH entirely:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "benclawbot@users.noreply.github.com" -f ~/.ssh/id_ed25519 -N ""

# Add to GitHub via gh API (requires admin:public_key scope) or have user add manually at github.com/settings/keys
gh api user/keys -X POST -F title="$(hostname)-$(date +%Y%m%d)" -F key="$(cat ~/.ssh/id_ed25519.pub)" 2>/dev/null || echo "Manual key add needed"

# Switch remote to SSH
git remote set-url origin git@github.com:OWNER/REPO.git
git push origin main
```
This bypasses the HTTPS credential system entirely and is the reliable path when HTTPS is broken.
```bash
# Never leave credentials embedded in the remote URL
git remote set-url origin "$(echo "$(git remote get-url origin)" | sed 's|https://[^@]*@|https://|')"
git remote -v  # verify no credentials visible
```

### New Repo Default Branch Issue

When creating a new GitHub repo via `gh repo create` and immediately pushing to it, the **first branch pushed becomes the default branch automatically** — even before the push completes. This means:

- If you push `feat/my-feature` first, `main` is not the default on the remote yet
- `gh pr create --base main` will fail with "Base sha can't be blank" because `main` isn't the remote default
- **Fix:** Always check the remote's default branch first:
  ```bash
  gh api repos/$OWNER/$REPO --jq '.default_branch'
  ```
- If the default is your feature branch and you need a `main` base, push `main` to the new repo first:
  ```bash
  # Push upstream main as main to the new repo
  git push newremote $(git rev-parse upstream/main):refs/heads/main
  ```
- Then create the PR with explicit head branch:
  ```bash
  gh pr create --repo owner/repo --base main --head feat/my-branch
  ```

### Create a PR

*(Assumes push succeeded or a fork remote was set up above)*

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

## 6. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Enable Auto-merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## 7. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

---

## Code Review

*Absorbed from `github-code-review` — see that skill's full content for complete PR review workflow.*

### Quick Local Review (Pre-Push)

```bash
# Get the diff
git diff main...HEAD

# Check for common issues
git diff main...HEAD | grep -n "print\|console\.log\|TODO\|FIXME\|HACK\|XXX\|debugger"
git diff main...HEAD | grep -in "password\|secret\|api_key\|token.*=\|private_key"
```

### Review Output Format

```
## Code Review Summary

### Critical
- **src/auth.py:45** — SQL injection: user input passed directly to query.

### Warnings
- **src/models/user.py:23** — Password stored in plaintext.

### Suggestions
- **tests/test_auth.py** — Missing edge case: expired token test.

### Looks Good
- Clean separation of concerns in the middleware layer
```

### Review Checklist

- **Correctness:** Does it do what it claims? Edge cases handled?
- **Security:** No hardcoded secrets? Input validation? SQL injection?
- **Code Quality:** Clear naming? DRY? Single responsibility?
- **Testing:** New paths tested? Error cases covered?
- **Performance:** N+1 queries? Unnecessary loops?
- **Documentation:** Public APIs documented?

### Full Code Review Workflow (End-to-End)

For complete PR review instructions (checking out PRs, posting inline comments, formal review submission), see `references/github-code-review-workflow.md`.

---

## GitHub Issues

*Absorbed from `github-issues` — see that skill's full content for complete issue management.*

### Quick Reference

| Action | gh | curl endpoint |
|--------|-----|--------------|
| List issues | `gh issue list` | `GET /repos/{o}/{r}/issues` |
| View issue | `gh issue view N` | `gh issue view` (or `GET /repos/{o}/{r}/issues/N`) |
| Add labels | `gh issue edit N --add-label ...` | `POST /repos/{o}/{r}/issues/N/labels` |
| Assign | `gh issue edit N --add-assignee ...` | `POST /repos/{o}/{r}/issues/N/assignees` |
| Comment | `gh issue comment N --body "..."` | `POST /repos/{o}/{r}/issues/N/comments` |
| Close | `gh issue close N` | `PATCH /repos/{o}/{r}/issues/N` |

### Bug Report Template

```
## Bug Description
<What's happening>

## Steps to Reproduce
1. <step>

## Expected Behavior
<What should the code do?>

## Actual Behavior
<What actually happens>
```

For full issue management (triage, bulk operations, linking to PRs), see `references/github-issues-workflow.md`.

---

## Repository Management

*Absorbed from `github-repo-management` — see that skill's full content for clone, fork, releases, and CI/CD.*

### Quick Reference

| Action | gh | git + curl |
|--------|-----|------------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST /repos/o/r/forks` |
| Repo info | `gh repo view o/r` | `curl GET /repos/o/r` |
| Edit settings | `gh repo edit --...` | `curl PATCH /repos/o/r` |
| Create release | `gh release create v0.1.0` | `curl POST /repos/{o}/{r}/releases` |
| Rerun CI | `gh run rerun ID` | `curl POST /repos/{o}/{r}/actions/runs/ID/rerun` |

### Non-Negotiable: No Credentials in Git

Before ANY `git add` or `git push`:

```bash
# Check what's staged
git status
git diff --cached --name-only

# Critical .gitignore entries (where credentials hide):
.wrangler/  .next/  dist/  dist.zip  *.map
.env  .env.local  .env.*.local
*.pem  *.key  id_rsa*  id_ed25519*
```

For complete repository management (branch protection, secrets, gists, feature extraction patterns), see `references/github-repo-management-workflow.md`.

---

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|------------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `POST /issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `POST /pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Pre-push credential check | `references/pre-push-checks.md` — mandatory credential audit before any push |
| Push Troubleshooting | `references/fork-workflow.md` — complete fork-based workflow when no write access to origin |
| | `references/push-auth-troubleshooting.md` — HTTPS push auth failures: SSH fallback, embedded URL token, token scope traps, diagnostic sequence, cleanup |
| | `references/gh-path-note.md` — why /home/thomas/bin/gh must be hardcoded in Python scripts |
| | `references/pyright-usage.md` — static type checking with pyright |
| New repo + first PR | `references/new-repo-first-pr.md` — new repo creation, first branch pushed becomes default, pushing main first, using --body-file safely |
| Handling divergent branches | `references/divergent-branch-strategy.md` — soft-reset squash when upstream changed same files; bypass nested rebase/merge conflicts |
| **Fork-staleness watchdog** | `references/fork-staleness-watchdog.md` — fork's main drifts hundreds behind because a cron auto-commits without `git fetch`; PRs from stale forks are still valid; 5-question audit + 3-layer fix recipe |
| **PR branch rebase after fork sync** | `references/pr-branch-rebase-after-fork-sync.md` — rebase local main → rebase PR branch onto it → force-push branch (NOT main) to fork; "diff is byte-identical when no upstream commit touched the same files" property; pre-flight "verify fork health before opening PR" |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
| New repo, first PR traps | `references/new-repo-first-pr.md` — README persists trap, default branch trap, verify clean extraction |
| PyPI publishing | `references/***.md` — build, upload, verify, and lockfile traps |
| Repo health monitoring | `references/benclawbot-repo-health.md` — 3-script system for all 29 benclawbot repos: PR digest, project health, single-repo deep dive |
| Fast multi-repo `gh` scripts | `references/github-script-optimization.md` — `gh_cached` 5-min disk cache + `ThreadPoolExecutor` 8-worker parallelization (29 repos in 5.3s vs 30s sequential) |

---

## Pitfall: Fork Can Be a Write-Only Surface

**Symptom:** Your fork exists, push to it succeeds, but `git status` shows your clone of the fork is `4 and 328` commits diverged from upstream. Multiple `chore: auto-commit from watchdog` commits accumulate with empty diffs.

**Root cause:** A cron / watchdog script auto-commits and pushes to the fork without `git fetch origin` and without checking how far behind upstream the local clone is. Each tick widens the gap.

**Two compounding mistakes:**
1. No `git fetch origin` before commit+push — local can be arbitrarily stale
2. Hardcoded PAT in push URL (a workaround for "gh not in $PATH" or "credential helper broken") — works, but bypasses `gh auth` and leaks the token

**Why PRs from a stale fork are still valid (and why you should sync anyway):**
GitHub compares the *branch* to the *target*, not the fork's main. So `fix/my-branch` based on an old commit can still produce a meaningful PR diff. But the fork is unhealthy for the next contributor, future PRs accumulate unfixable merge conflicts, and reviewers who browse the fork see a misleading picture.

**Fix recipe:** See `references/fork-staleness-watchdog.md` for the 5-question audit, the 3-layer fix (pause watchdog / sync fork with bundle backup / replace the pattern with fetch+behind-count guard+gh auth), and a complete safe-auto-commit-and-push function template.
