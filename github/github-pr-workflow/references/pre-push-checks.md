# Pre-Push Credential Check

**Non-negotiable.** Every push to any GitHub remote goes through this checklist first.

## The Rule

If you can't verify the staging area, you can't push to GitHub.

## Checklist

### Before `git add`

```bash
# Confirm the staging area is clean for new work
git status
```

### Before `git commit`

```bash
# Review what's actually staged — never commit blind
git diff --cached --name-only

# If files look wrong, unstage with:
git reset HEAD <file>
```

### Before `git push`

```bash
# See what commits WOULD be pushed
git log --oneline origin/main..HEAD

# For each commit, verify no credentials or build artifacts
# especially if commits came from a third-party source (merge, cherry-pick, etc.)

# Final remote URL check — no embedded credentials
git remote -v
```

## High-Risk Patterns (stop and verify before pushing)

| Pattern | Why it's dangerous |
|---------|-------------------|
| `.wrangler/` in git | Build artifacts contain embedded source maps with real API keys |
| `dist/`, `.next/`, `out/` | Build output often contains credential files |
| `*.map` files | Source maps embed original source including secrets |
| `.env` files with real values | Direct credential commits |
| `*.pem`, `*.key`, `secrets.json` | Private key commits — rotate immediately if pushed |
| Commits from third-party branches | May contain credentials added by someone else |

## When You Discover a Secret Was Pushed

1. **Revoke the secret at the provider immediately** (GitHub can't undo a push)
2. **Remove from git history** with `git filter-branch`:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch PATH/TO/SECRET" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push** to overwrite history:
   ```bash
   git push --force https://user:$(gh auth token)@github.com/owner/repo.git --all
   ```
4. **Open secret scanning alerts** on GitHub and resolve them with resolution reason `revoked` or `false_positive`

## Historical Incidents (learned from)

- **complyscan**: `.wrangler/` directory committed with Stripe test keys embedded in source maps. Build artifacts had been added to git despite `.gitignore` entry. Fixed with filter-branch + force push.
- **agent-commit**: No `.gitignore`. Telegram bot tokens, OpenRouter API keys, and Google API keys committed directly to source. Tokens needed rotation.

## Essential `.gitignore` entries for every repo

```
# Build artifacts — #1 source of credential leaks
.wrangler/
.next/
dist/
*.map

# Credentials
.env
.env.local
.env.*.local
.env*.local
*.pem
*.key
secrets.json
credentials.json

# Logs
npm-debug.log*
yarn-debug.log*
```

The `.gitignore` only prevents *new* commits. It cannot remove secrets already in history. Prevention is the only reliable solution.