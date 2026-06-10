# Push Authentication Troubleshooting

Complete guide for diagnosing and fixing `git push` authentication failures when HTTPS is broken or credentials are unavailable.

---

## The Core Problem

`git push` via HTTPS uses the credential helper system. When that system is broken or unavailable, pushes fail even with a valid token. This is distinct from API authentication (which `gh api` or `curl -H "Authorization: ..."` use successfully).

**Symptoms:**
- `git push` → `fatal: could not read Username for 'https://github.com': No such device or address`
- `gh auth status` passes, `gh auth token` returns a valid token, API calls work
- `gh api user` returns 200, but `git push` fails

---

## Auth Method Priority (in order)

### 1. SSH (recommended when available)

```bash
ssh-keygen -t ed25519 -C "benclawbot@users.noreply.github.com" -f ~/.ssh/id_ed25519 -N ""
gh ssh-key add ~/.ssh/id_ed25519.pub  # or user adds manually at github.com/settings/keys
git remote set-url origin git@github.com:OWNER/REPO.git
git push origin main
```

**Bypasses HTTPS credential system entirely.** Most reliable when HTTPS is broken.

> **Note:** If `gh ssh-key add` fails with scope error, the PAT lacks `admin:public_key`. User must add the key manually at github.com/settings/keys.

### 1b. gh auth git-credential (recommended when gh is installed)

When `gh auth status` passes but `git push` fails with `could not read Username for 'https://github.com': No such device or address`, and `gh auth git-credential` exists as a command:

```bash
# Find gh path first — may not be in PATH from git's perspective
GH_PATH=$(which gh 2>/dev/null)
echo "gh at: $GH_PATH"

git config --global credential.helper "$GH_PATH auth git-credential"
cd /path/to/repo && git push origin main
```

**Why this works:** `gh auth git-credential` is gh's built-in credential helper that reads from the gh-managed keyring. It bypasses broken system credential helpers (keyring, cache, store) while keeping credentials out of the remote URL. Works even for rebases that change commits since the token is read fresh each time.

**Post-push:** verify remote URL is clean:
```bash
git remote -v | grep "github.com" | grep -v "@" && echo "Clean ✓"
```

**If gh is not at the expected path** (`/home/thomas/bin/gh` vs `/usr/bin/gh`):
```bash
# Diagnose which gh is being used
which gh && gh --version | head -1
# Use the full path in the credential helper
git config --global credential.helper "/path/to/gh auth git-credential"
```

### 2. Embedded URL Token (fallback, temporary)

When SSH is not available and `gh auth git-credential` is not an option:

```bash
# Verify token first — critical step
TOKEN=YOUR_PAT_HERE
STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/OWNER/REPO")
echo "Token status: $STATUS"  # Must be 200
```

Then push with embedded token:
```bash
git remote set-url origin "https://TOKEN@github.com/OWNER/REPO.git"
git push origin main
```

**Post-push cleanup** (credentials are visible in `git remote -v`):
```bash
git remote set-url origin "https://github.com/OWNER/REPO.git"
git remote -v  # verify no credentials visible
```

### 3. git-credential with explicit helper script (advanced)

```bash
cat > /tmp/cred-helper.sh << 'SCRIPT'
#!/bin/bash
while IFS= read -r line; do
  [ -z "$line" ] && break
done
echo "username=x-access-token"
echo "password=$TOKEN"
SCRIPT
chmod +x /tmp/cred-helper.sh
git config --local credential.helper "/tmp/cred-helper.sh"
git push origin main
```

Reliable but requires TOKEN env var to be set.

---

## Token Scope Traps

### `workflow` scope is NOT sufficient for git push

A PAT with only `workflow` scope works for GitHub Actions API calls but fails for git push with `invalid credentials`. Even if API calls return 200.

**Fix:** Create a PAT with `repo` full scope (or at minimum `gist` + `workflow` + `read:user` won't work either — git push needs `repo`).

### `gh auth setup-git` does not fix HTTPS auth

`gh auth setup-git` configures gh to act as a git credential helper (for SSH git operations via GitHub). It does **not** fix broken HTTPS credential helpers or broken git-credential stores. If HTTPS is broken, `gh auth setup-git` silently does nothing useful.

**The fix is SSH or embedded URL, not `gh auth setup-git`.**

---

## Diagnostic Sequence

Run this when push fails:

```bash
# Step 1: What auth method is configured?
echo "=== Git auth config ==="
git config --global --list | grep -i "cred\|helper"
echo "=== gh auth status ==="
gh auth status 2>&1
echo "=== gh auth token (check scope) ==="
gh auth token 2>&1 | head -c 20
echo "..."
echo "=== Testing token via API ==="
TOKEN=$(gh auth token 2>/dev/null)
curl -s -o /dev/null -w '%{http_code}' \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/OWNER/REPO"
echo ""
echo "=== git-credentials ==="
cat ~/.git-credentials 2>/dev/null | head -1 || echo "No git-credentials"
echo "=== netrc ==="
cat ~/.netrc 2>/dev/null | head -3 || echo "No netrc"
echo "=== SSH keys ==="
ls -la ~/.ssh/ 2>/dev/null
echo "=== SSH config ==="
cat ~/.ssh/config 2>/dev/null | head -10 || echo "No SSH config"
```

---

## Validating Push Access Pre-Flight

Always run before making commits on a branch meant for a PR:

```bash
git push --dry-run origin HEAD 2>&1
PUSH_OK=$?

if [ $PUSH_OK -ne 0 ]; then
  echo "Push check failed — fix auth before continuing"
  # Run diagnostic sequence above
fi
```

If push fails, **do not make commits on that branch**. Either fix auth first or push to a fork.

---

## Handling Token Refresh Failure

`gh auth refresh -h github.com` can hang indefinitely (exit 124 timeout) if there are network issues or the token is invalid.

**Workaround:** Use the token directly — `gh auth token` still works even if `gh auth refresh` hangs.

```bash
TOKEN=$(gh auth token 2>/dev/null)
# Use TOKEN for all subsequent operations
```

---

## When Git Repo Disappears Between Sessions

If `/tmp/repo-name` from a previous session no longer exists (cleaned up or session expired), re-clone:

```bash
git clone https://github.com/OWNER/REPO.git /tmp/repo-name
cd /tmp/repo-name
```

Then re-apply changes and push. Do not assume the cloned repo persists across sessions.

---

## Cleanup Checklist After Using Embedded URL Token

After a successful push with an embedded token, always run:

```bash
# Remove embedded credentials from remote URL
git remote set-url origin "https://github.com/OWNER/REPO.git"

# Verify
git remote -v | grep -v "github.com" && echo "WARNING: credentials still visible"
git remote -v | grep "github.com" | grep -v "@" && echo "Clean ✓"
```

Leaving credentials embedded in the remote URL exposes them in `.git/config` and in every `git remote -v` output.