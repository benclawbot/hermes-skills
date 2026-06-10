# Git Pull Recovery — Diverged Forks

When `~/.hermes/hermes-agent/` is a git checkout and shows `Your branch and 'origin/main' have diverged`, the naive `git pull` will conflict. This is the safe recovery workflow.

## Symptom

```
On branch main
Your branch and 'origin/main' have diverged,
and have 1 and 339 different commits each, respectively.
  (use "git pull" if you want to integrate the remote branch into yours)

Changes not staged for commit:
        modified:   hermes_cli/main.py

Untracked files:
        hermes_cli/task_contract/
        scripts/validate_task_contract.sh
        tests/task_contract/
        website/docs/developer-guide/task-contract-layer.md
        website/docs/user-guide/task-contract.md
```

A 339-commit lead usually means you've been editing directly on main without pushing. A "modified" file + untracked files is a half-finished WIP.

## Why this matters

The hermes-agent checkout is the live source. If `hermes` is launched from `~/.hermes/hermes-agent/venv/bin/python` (the standard install), a `git pull --rebase` or `git pull` with conflicts will leave the working tree in a broken state and may cause the gateway to crash on next launch. A `git pull --ff-only` will refuse. A blind `git pull --rebase` may destroy uncommitted edits.

## The Recovery (2-3 steps)

### Step 1: Stash everything safely

```bash
cd ~/.hermes/hermes-agent
git stash push -u -m "wip: <short description> [pre-pull YYYY-MM-DD]"
```

The `-u` (include untracked) is critical — without it, untracked files stay in the working tree and `git pull` may fail or leave them in a weird state. The message makes the stash identifiable later.

Verify with `git stash list` — should show `stash@{0}: On main: wip: ...`.

### Step 2: Pull with merge (not rebase)

```bash
git pull --no-rebase
```

`--no-rebase` is the default but stating it explicitly makes the intent clear: merge upstream into local, don't rewrite local history. With a clean working tree and no ahead commits, this is a clean fast-forward.

If the upstream moved 339 commits, this will take a few seconds. Watch for `Auto-merging` lines — these indicate conflicts the merge resolver fixed automatically (no action needed).

### Step 3: Reapply the stash

```bash
git stash pop
```

If the stash contained edits to a file that ALSO changed in upstream, git will auto-merge it. If the auto-merge conflicts, git will leave conflict markers in the file — fix manually, then `git add` and `git commit` (or `git stash drop` to abandon).

Verify the result:

```bash
git status                    # should show your untracked files + possibly your modifications
git diff <file>               # eyeball the merge result
```

## What NOT to do

- **`git pull --rebase`** — rewrites your local commits, can lose WIP
- **`git pull --ff-only`** — refuses when there's any local divergence
- **`git reset --hard origin/main`** — DESTROYS uncommitted + untracked work
- **`git clean -fd`** — deletes untracked files before you have a backup
- **Force-push** — only relevant if you were going to push; usually you aren't

## After the pull

1. **Restart the gateway** — upstream may have changed Python code:
   ```bash
   systemctl --user restart hermes-gateway
   sleep 3
   systemctl --user is-active hermes-gateway    # should print "active"
   ```

2. **Check for new config version** — upstream may have introduced a new config schema:
   ```bash
   hermes doctor | grep "Config version"
   hermes doctor --fix                          # migrates if needed
   ```

3. **Verify your WIP still works** — load the module, run a command that uses it:
   ```bash
   ~/.hermes/hermes-agent/venv/bin/python -c "import hermes_cli.main; print('OK')"
   ```
   For new subcommands: `hermes <new-cmd> --help`.

## The "2 ahead" aftermath

After the merge, `git status` will show `Your branch is ahead of 'origin/main' by 2 commits`. These are merge artifacts from the upstream integration, not yours. **Do not push them** — they may not survive a round-trip cleanly. If you need to push, use `git push --force-with-lease` after rebasing onto a fresh origin/main, but generally you don't need to push from this checkout.

## When to use

- `git status` in `~/.hermes/hermes-agent/` shows diverged
- Before running any skill that edits files in that directory
- After a long stretch without pulling (multiple weeks)
- When the user says "update hermes" / "pull latest" / "sync with upstream"

## Diagnostic: was the local work intentional?

Before pulling, ask:

1. Are the local uncommitted files something the user was actively working on? If yes, this is a WIP — stash carefully, ask if they want it back.
2. Are the uncommitted files noise (test artifacts, scratch files)? If yes, you can `git clean -fd` instead of stashing.
3. Is the "1 commit ahead" the user's WIP commit, or a stale merge? `git log origin/main..HEAD` shows what's local-only.

For the standard case of "user has been editing the install directly with no plan to push," stash → pull → pop is the right answer.
