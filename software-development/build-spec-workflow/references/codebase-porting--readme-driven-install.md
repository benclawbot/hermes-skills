# README-Driven Install Implementation

Companion to the main `codebase-porting` SKILL.md. Use this when the user points at a repo's README and says "implement what's needed for [target platform], check it works locally." The README is the spec; the actual repo is the implementation; you close the gaps.

## The full workflow

```
0. Confirm repo is reachable (gh auth + gh api)
1. Pull README, audit against actual tree → gap table
2. For each gap, fix in the smallest correct way
3. Build a one-shot installer that matches the README's "Quick start" section
4. Verify end-to-end with REAL synthetic data (not just "script exits 0")
5. Update README in the same commit
6. Commit + push (gh auth setup-git if HTTPS push fails)
7. Summarize the commit (sha + files + verification artifacts)
```

Steps 0-1 are the audit. Steps 2-3 are the build. Steps 4-5 are the verification + docs. Steps 6-7 are the ship.

## Step 0: Confirm the repo is reachable

Three failure modes here:
- **404** — repo is private, renamed, or typo'd. `gh api /repos/owner/repo` returns the JSON error. Try `gh api /users/<owner>/repos --jq '.[].name'` to list their repos and ask which one.
- **401** — gh token expired. `gh auth status` shows "token in default is invalid". `gh auth login` re-auths, then retry.
- **gh CLI not installed** — `brew install gh` (mac) / `apt install gh` (Linux). `gh auth login` follows.

Once reachable: `gh api /repos/owner/repo --jq '{name, default_branch, description, private, language, pushed_at, size}'` gives you the lay of the land. Then `gh api /repos/owner/repo/contents/README.md --jq '.content' | base64 -d > /tmp/readme.md` gets the file.

## Step 1: The audit table

Walk the README, section by section. For each claim about the system, find the corresponding code in the tree and check if reality matches. Output a gap table:

| README claim | Reality | Gap type | Fix |
|---|---|---|---|
| `cd ~/repo/hub && npm install` | `run-hub.sh` hardcodes `$HOME/legacy-path` | Path contradiction | Rewrite the script to derive paths from `$BASH_SOURCE` |
| Exports are `Omni-Memory/exports/{device}/` | Hub scanner only reads top-level `manifest_*.json` | Layout assumption | Recursive walker in the hub |
| "Hub ingest has 0 events" troubleshooting: `cat .../exports/*/manifest.json` | Actual filenames are `manifest_*.json` | Wrong glob in docs | Fix the README |
| "Manual: run the pipeline, schedule cron" | No one-shot installer | Missing artifact | Build `install-<target>.sh` |
| "If env file doesn't exist, dies" | First-run scenario | Missing recovery | ENOENT is a clean skip, not a fatal exit |

The "Gap type" column helps you triage: **path contradiction** = fix the script, **layout assumption** = fix the scanner, **wrong glob in docs** = fix the README, **missing artifact** = build it.

## Step 2: Fix gaps in the smallest correct way

Three rules:
- **Don't refactor while you're closing gaps.** A bugfix is a bugfix. A rewrite is a separate PR.
- **For "two scripts doing similar things with different paths":** the one NOT in the README is legacy. Either fix it to match the README's paths or delete it. Carrying dead scripts is worse than deleting them.
- **For layout mismatches:** the canonical layout should be the one in the README (or the one the hub expects). Fix the OTHER side. Don't try to support both layouts forever — pick one and update the docs.

## Step 3: The install script

The shape that works:

```bash
#!/usr/bin/env bash
# install-<target>.sh — one-shot setup for <app> on <target>.
# Implements README §X. Re-runnable (idempotent).
set -euo pipefail

REPO_URL="https://github.com/owner/repo.git"
REPO_DIR="$HOME/<app>"
HUB_DIR="$REPO_DIR/<sub>"
DB_DIR="$HOME/.memory/<app>"
ENV_FILE="$HOME/.memory/.env"
LOG_DIR="~/Library/Logs/<app>"  # macOS; on Linux use ~/.local/share/<app>/logs

# ── Prereq checks (with version, not just command -v) ──
command -v gh >/dev/null    || die "gh CLI not installed"
command -v node >/dev/null  || die "node not installed"
NODE_VER=$(node -p "process.versions.node.split('.')[0]")
[[ "$NODE_VER" -ge "18" ]] || die "node $NODE_VER, need 18+"

gh auth status >/dev/null 2>&1 || die "gh not authenticated"

# ── Clone (idempotent) ──
if [[ -d "$REPO_DIR/.git" ]]; then
  ok "Already cloned"
else
  git clone "$REPO_URL" "$REPO_DIR" >> "$LOG_DIR/install.log" 2>&1
fi

# ── npm install (idempotent, --no-audit to skip noise) ──
(cd "$HUB_DIR" && npm install --no-audit --no-fund) \
  >> "$LOG_DIR/install.log" 2>&1

# ── Env file (idempotent: skip already-set vars) ──
touch "$ENV_FILE"
chmod 600 "$ENV_FILE"
# Use a write_if_missing function that respects $NONINTERACTIVE

# ── Network calls: ALWAYS with --max-time ──
curl -fsS --max-time 5 "$URL" > "$LOG_DIR/response.json" 2>/dev/null

# ── First run + cron install ──
bash "$HUB_DIR/run-<thing>.sh" 2>&1 | tee -a "$LOG_DIR/install.log"

# Cron line — only install if not already present
crontab -l 2>/dev/null > /tmp/cron || true
grep -Fq "$HUB_DIR/<cron-target>" /tmp/cron || echo "*/30 * * * * ..." >> /tmp/cron
crontab /tmp/cron
```

Key invariants:
- **Prereq checks fail LOUDLY** with `die "..."` not `echo "warning"`. A missing prereq should never silently result in a half-working install.
- **Network calls have `--max-time`**. Default 5s. DNS is slow on some networks, and a hanging curl is the #1 way an installer script "feels broken" even when it's actually working.
- **Env file is 600 perms** (contains secrets), `touch` before write, `chmod` after.
- **Idempotent re-runs**: every step checks for existing state and skips. Re-running should never break a working install.
- **Logs go to a known location** (`~/Library/Logs/<app>` on macOS, `~/.local/share/<app>/logs` on Linux), and the path is printed at the end.
- **Exit code reflects what actually happened.** `npm install` failed → exit 1. Cron install skipped (already present) → exit 0.

### The `write_if_missing` noninteractive pattern

The single most-rewritten function in install scripts. The shape that handles TTY, defaults, and CI:

```bash
write_if_missing() {
  local key="$1" prompt_text="$2" default="${3:-}"
  local current
  current=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- || true)
  if [[ -n "$current" ]]; then
    ok "$key already set (skipped)"
    return
  fi
  local val
  if [[ "${NONINTERACTIVE:-}" == "1" ]]; then
    if [[ -n "$default" ]]; then
      val="$default"
    else
      warn "$key not set and NONINTERACTIVE=1 — skipping"
      return
    fi
  elif [[ -n "$default" ]]; then
    read -r -p "$prompt_text [$default]: " val
    val="${val:-$default}"
  else
    read -r -p "$prompt_text: " val
    [[ -n "$val" ]] || die "$key is required"
  fi
  echo "${key}=${val}" >> "$ENV_FILE"
}
```

Order matters: **NONINTERACTIVE first** (skip if no default), then TTY-with-default, then TTY-required. The `[[ -t 0 ]]` check (fd 0 is a tty) is an alternative to the env-var gate but harder to override from CI; the env var is more flexible.

## Step 4: Verify with REAL data

"Script exited 0" is not proof. Proof is rows in the destination table.

```bash
# 1. Set up an isolated test home
export HOME=/tmp/test-home
mkdir -p $HOME/.memory/<app>

# 2. Seed a minimal real-shape export
node -e "
import json, hashlib, time, os
home = '$HOME'
export_dir = f'{home}/<repo>/exports/<device-id>'
os.makedirs(export_dir, exist_ok=True)
events = []
for source, msgs in [...]:
    for i, content in enumerate(msgs):
        h = hashlib.sha256(f'{source}:sess:{ts}:{content}'.encode()).hexdigest()
        events.append({...real schema fields...})
# Write JSONL + manifest
"

# 3. Run the pipeline manually
node <hub>/ingest/<thing>.mjs --export-dir $HOME/<repo>/exports

# 4. Assert rows landed
node -e "
const Database = require('<hub>/node_modules/better-sqlite3');
const db = new Database('$HOME/.memory/<app>/events.db', { readonly: true });
const totals = db.prepare('SELECT source, COUNT(*) as n FROM events GROUP BY source').all();
const grand = db.prepare('SELECT COUNT(*) as n FROM events').get().n;
console.log('Total:', grand);
console.log(totals);
"

# 5. Re-run, assert dedup works (skipped == N, ingested == 0)
node <hub>/ingest/<thing>.mjs --export-dir $HOME/<repo>/exports

# 6. Smoke-test the bot (with fake token, expect 401 clean exit)
TELEGRAM_BOT_TOKEN=*** timeout 3 node <hub>/telegram/bot.mjs 2>&1 | head -5
```

If any of steps 3-6 don't show what you expect, **stop and debug the real bug**. Don't move on with "well, the install worked" if the actual data flow is broken.

## Step 5: Update the README in the same commit

Every code change that closes a gap should also update the README:
- Reference the new installer: `bash hub/install-<target>.sh`
- Document non-obvious fixes (ENOENT recovery, recursive walker, dedup)
- Fix factual errors you found during the audit (wrong globs, outdated paths)
- Tick the "what works" checkboxes that are now true
- Note any deviations (e.g. "this version expects the manifest to live under `<device>/`, not at the top level")

## Step 6: Commit + push

```bash
# 1. Stage the changes
git add README.md hub/install-<target>.sh hub/<fix>.mjs

# 2. Commit with a descriptive message
git -c user.email=<email> -c user.name="<name>" commit -m "<subject>

<body explaining what + why + what was verified>"

# 3. Push (assumes gh is authed)
gh auth setup-git    # ONLY if git push fails with "could not read Username"
git push origin <branch>
```

The `gh auth setup-git` step is the gotcha. If your local clone was made before `gh auth login`, the git credential helper is not wired. `gh auth status` is ✓ but `git push` fails. `gh auth setup-git` is the one-shot fix.

Alternative one-shot for a single push:
```bash
git push "https://$(gh auth token)@github.com/owner/repo.git" <branch>
```

## Step 7: Verify the push landed

```bash
gh api /repos/owner/repo/commits --jq '.[0] | {sha: .sha[0:7], message: .commit.message[0:80]}'
gh api /repos/owner/repo/contents/<new-file> --jq '.size'
```

If the latest sha is your commit and the file size matches what you wrote, the ship is complete.

## The cross-machine ingestion pattern

Generic for any "collect from N sources, ingest to a central hub" system. Three failure modes to design for up front:

1. **Layout drift.** The collector and the hub don't agree on where files live. Fix: hub uses a recursive walker and accepts any layout (`flat`, `per-device/`, `per-source/`, whatever the collector produces).
2. **Absolute paths in manifests.** The collector writes its own absolute paths into a manifest, but those paths don't exist on the hub (different machine). Fix: hub resolves the manifest's `file:` paths against the manifest's own directory, with fallback to `<device>/<basename>` and `<source>.jsonl`. Multi-candidate lookup with a stat() check.
3. **Missing dir on first run.** Fresh hub install has no exports dir; the first ingest run shouldn't fatal-error. Fix: ENOENT on the exports dir is a clean skip with a "run a collector first" message.

```js
// Generic pattern: recursive manifest walker
const getManifests = async () => {
  const out = [];
  async function walk(dir, depth) {
    let ents;
    try {
      ents = await fsPromises.readdir(dir, { withFileTypes: true });
    } catch (err) {
      if (err.code === "ENOENT") {
        console.log(`[ingest] ${dir} not found — skipping`);
        return;
      }
      throw err;
    }
    for (const ent of ents) {
      const full = path.join(dir, ent.name);
      if (ent.isDirectory() && depth < 4) await walk(full, depth + 1);
      else if (ent.isFile() && ent.name.startsWith("manifest_") && ent.name.endsWith(".json")) {
        out.push(full);
      }
    }
  }
  await walk(EXPORT_DIR, 0);
  return out.sort();
};

// Generic file resolution (multi-candidate fallback)
const candidates = [
  file,                                              // manifest's literal path (probably wrong cross-machine)
  path.join(manifestDir, path.basename(file)),       // basename in manifest's dir
  path.join(manifestDir, device_id, path.basename(file)),  // per-device subdir
  path.join(manifestDir, `${source}.jsonl`),         // canonical name in manifest's dir
  path.join(manifestDir, device_id, `${source}.jsonl`),   // canonical in per-device
];
const resolved = candidates.find((p) => {
  try { return fs.statSync(p).isFile(); } catch { return false; }
});
if (!resolved) { console.log(`[${source}] not found, skipping`); continue; }
```

The 5-candidate fallback covers: literal path works, basename works, per-device layout works, canonical name in flat, canonical name in per-device. One of them will hit.

## Anti-patterns to refuse

- **"The install worked, ship it."** Without step 4 (real-data verification), you don't know if the code path actually works. The installer is the easy part — the data flow is what matters.
- **"I'll update the README later."** No. The README is the user-facing surface. A code change without a doc change is a half-ship.
- **"I'll just delete the dead script."** Verify first with `search_files` for any references (README, docs, cron jobs, skills). If nothing references it, delete. If something does, update the reference too.
- **"I'll push tomorrow when I have time."** Single commit, single push. The user is waiting for this artifact, not a future state.
- **Re-running with `--no-verify` to skip a pre-commit hook that caught a real bug.** Fix the bug.
- **"The exit code was 0, must be fine."** Exit code reflects the LAST command's status, not the pipeline's. Always tail the log and assert on the actual data, not the exit code.

## Quick recipe: full verification commands (copy-paste)

```bash
# Set up isolated test home
export HOME=/tmp/omni-verify
rm -rf $HOME && mkdir -p $HOME/.memory/<app>

# Pre-seed env (so the installer's "skip if set" path is tested)
printf 'TELEGRAM_BOT_TOKEN=*** > $HOME/.memory/.env
chmod 600 $HOME/.memory/.env

# Stage the repo
cp -r <repo-checkout> $HOME/<repo>

# Run the installer in non-interactive mode
cd $HOME/<repo> && NONINTERACTIVE=1 bash hub/install-<target>.sh 2>&1 | tail -30

# Confirm cron line was installed
crontab -l | grep <app>

# Seed a real-shape export
node -e "..."  # or python3 -c "..."

# Run pipeline manually
bash $HOME/<repo>/hub/run-<thing>.sh

# Query the DB to confirm rows
node -e "
const Database = require('$HOME/<repo>/hub/node_modules/better-sqlite3');
const db = new Database('$HOME/.memory/<app>/events.db', { readonly: true });
const totals = db.prepare('SELECT source, COUNT(*) as n FROM events GROUP BY source').all();
console.log('By source:', totals);
console.log('Total:', db.prepare('SELECT COUNT(*) as n FROM events').get().n);
"

# Re-run, confirm dedup
node $HOME/<repo>/hub/ingest/<thing>.mjs --export-dir $HOME/<repo>/exports 2>&1 | grep -E 'ingested|skipped'

# Smoke-test bot with fake token
TELEGRAM_BOT_TOKEN=*** timeout 3 node $HOME/<repo>/hub/telegram/bot.mjs 2>&1 | head -5
```

Each command's expected output is a checkbox in your verification. If 6/6 match, the install is verified.

## Related: the "git status lies about mode" gotcha

When you `chmod +x` a tracked file, `git status` shows it as "modified" even though content is identical. The diff is the mode (100644 → 100755), not the content. Three options:

- **Set `core.fileMode false` for the audit** (then `git status` only shows real content changes):
  ```bash
  git config core.fileMode false
  git status -sb
  ```
- **Only chmod the NEW files you create** (don't touch existing tracked files' perms). The new file gets the right mode from the start, and existing files keep their tracked mode.
- **After audit, reset perms on the changed ones** (if you accidentally chmod'd them):
  ```bash
  git diff --name-only | xargs -I{} git diff --stat {} | head
  # If all are mode-only, revert the mode with:
  git config core.fileMode true   # or chmod 644 on each
  ```
