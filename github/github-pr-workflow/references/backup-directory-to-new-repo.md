# Backing Up a Directory to a New GitHub Repo

When the task is "snapshot a directory into its own GitHub repo" — a config backup, skill dump, vault copy, etc. — the workflow differs from a feature extraction. You're not removing things; you're preserving everything in a single commit.

## When to use this pattern

- "Backup my X to GitHub in a new private repo"
- "Snapshot this directory as its own repo"
- "Mirror the contents of /path to a fresh repo"

The umbrella skill `github-pr-workflow` covers the extraction-from-existing-repo case (see `references/new-repo-first-pr.md`). This reference covers the **content-backup** case.

## The pattern (verified 2026-06-10)

```bash
# 1. Stage in /tmp so a failed push doesn't leave the source mutated
DEST=/tmp/<backup-name>
rm -rf "$DEST" && mkdir -p "$DEST" && cd "$DEST"

# 2. Copy content (preserve dotfiles)
cp -r /path/to/source/. ./

# 3. Add .gitignore for the things that shouldn't be in a backup:
#    pycache, venv, .env, OS cruft, build artifacts
#    (whatever is appropriate for the source's ecosystem)

# 4. Init git, commit, push
git init -q -b main
git config user.email "you@users.noreply.github.com"
git config user.name "your-github-username"
git add .
git status -s | wc -l    # sanity check the file count
git commit -q -m "Backup of /path/to/source (date, file count)"
```

## Create the repo and push

```bash
# Create — private by default for personal backups
gh repo create "<repo-name>" --private --description "..." --disable-wiki 2>&1 | tail -3

# Add remote and push
git remote add origin https://github.com/<user>/<repo-name>.git
git push -u origin main
```

## Verify (do NOT use `gh repo view` immediately after create)

`gh repo view <user>/<repo>` can trigger a confirmation modal the first time, blocking on user input and appearing to hang. **Use the REST API instead.**

```bash
# Confirm repo exists and is private
curl -s -H "Authorization: token $(gh auth token)" \
  https://api.github.com/repos/<user>/<repo-name> | python3 -c "
import json,sys
d=json.load(sys.stdin)
print({k:d[k] for k in ['name','private','default_branch','html_url']})"

# Verify files actually landed — count tree entries
curl -s -H "Authorization: token $(gh auth token)" \
  "https://api.github.com/repos/<user>/<repo-name>/git/trees/main" | python3 -c "
import json,sys
t=json.load(sys.stdin).get('tree',[])
types={}
for e in t: types[e['type']]=types.get(e['type'],0)+1
print(f'top-level entries: {len(t)}  {types}')"
```

## Hidden state files in "plain" directories

`ls` doesn't show what's in a directory before you copy. Common surprises in backup scenarios:

- **Application state dirs** contain JSON, log paths, curator metadata, machine-specific absolute paths
- **Vault/data dumps** may include `.DS_Store`, `Thumbs.db`, `*.swp`, large media caches
- **Skill/plugin directories** often have manifest files (`.bundled_manifest`, `.hub/`, `.usage.json`)
- **Hermes skill directories specifically** have `.curator_state`, `.curator_suppressed`, `.curator_backups/` (dated cron snapshots), `.usage.json`, `.usage.json.lock`, `.hub/`, `.archive/`

### Decision matrix: include or strip?

| Content type | Backup choice | Reason |
|--------------|---------------|--------|
| Source code, docs, configs | Include | That's the point |
| Build artifacts (`__pycache__/`, `node_modules/`, `dist/`) | Exclude via `.gitignore` | Re-creatable, bloats repo |
| Local env (`.env`, `*.pem`, `id_*`) | Exclude via `.gitignore` | Secrets — even in private repos |
| Personal paths (`/home/user/...`) in JSON state | Include IF private repo on your own account | Fine for private backup, but document in README so you remember if it ever becomes public |
| Internal app state (usage tracking, curator metadata) | Include IF private | Restores the app to its captured state; exclude if you want content-only |
| `.curator_backups/` (cron job snapshots) | Include IF private, exclude for public | Contains cron prompts, schedules, job names — workflow fingerprint, not credentials |

## Privacy scan before first push

```bash
# Find absolute paths leaking into JSON/MD
grep -rE "^\s*\"[^\"]*\":\s*\"(/home|/Users|/root)" --include="*.json" -l .
grep -rE "/home/[a-z]+/" --include="*.md" -l .

# Find credential patterns
grep -rEi "api[_-]?key|secret|token|password|bearer" \
  --include="*.py" --include="*.md" --include="*.yaml" --include="*.json" \
  -l . | xargs -I{} sh -c 'echo "=== {} ==="; grep -nEi "api[_-]?key|secret|token" {} | \
   grep -vE "(getenv|environ|env var|_KEY not set|set the)"'
```

If matches are just skill content ABOUT handling secrets (security-audit, github-pr-workflow, etc.), they're safe to push. If you find actual leaked values, scrub them and amend the commit before pushing.

## Cleanup

Always remove the staging directory after a successful push:

```bash
rm -rf /tmp/<backup-name>
```

A failed `rm` here is harmless — but if you `cd` back into the deleted dir afterwards, the next shell will throw a "cannot access parent directories" error. Don't.

## README template for personal backups

The repo should explain **what** it is, **when** it was captured, and **how** to restore. Don't rely on memory — you'll forget.

```markdown
# <Repo Name>

Backup of <source path> on <machine>, captured <date>.

## Contents

- N skills / configs / files
- X MB

## Restoring

\`\`\`bash
git clone https://github.com/<user>/<repo>.git <destination>
\`\`\`

## Origin

<One paragraph: what the source is, who owns it, why this backup exists.>

## License

Mixed. Each file retains its own license (see frontmatter / headers).
```

## Pre-flight checklist

- [ ] Privacy scan ran (no leaked secrets or paths in public-facing way)
- [ ] `.gitignore` covers pycache, venv, .env, OS cruft for this ecosystem
- [ ] `git status -s` count matches expected (no surprise massive dump)
- [ ] `gh repo create` succeeded with `--private` and a meaningful description
- [ ] Push landed (verify with API tree call, not `gh repo view`)
- [ ] README documents capture date, source path, restore command
- [ ] Staging directory cleaned up
