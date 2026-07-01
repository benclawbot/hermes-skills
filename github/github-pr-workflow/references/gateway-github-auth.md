---
name: gateway-github-auth
description: How the Hermes gateway (Telegram bot, Discord bot, etc.) obtains GitHub credentials — separate from the user's `gh` CLI auth. Symptom, root cause, and the exact fix recipe.
---
# Gateway GitHub Auth — Separate from `gh` CLI

## Symptom
Telegram (or Discord) bot reports "reauthenticate" or returns 404 / permission errors on a private repo, **but `gh auth status` shows a healthy login** on the same machine.

## Root cause
The gateway does **not** read from `gh`'s keyring. It sources GitHub credentials from one place only:

  `GITHUB_TOKEN` in `~/.hermes/.env`

If that env var is missing, empty, or stale, the bot hits GitHub anonymously → 404 on private repos → "please reauthenticate" message. The user's `gh` auth state is irrelevant to the bot.

## Diagnosis (1 minute)

```bash
# 1. Is GITHUB_TOKEN set in the gateway's env file?
grep -q '^GITHUB_TOKEN=*** ~/.hermes/.env && echo "set" || echo "MISSING"

# 2. Is the value actually valid?
set -a; . ~/.hermes/.env; set +a
curl -s -o /dev/null -w "private repo: %{http_code}\n" \
  -H "Authorization: Bearer *** "
  "https://api.github.com/repos/<owner>/<private-repo>"

# 200 = working.  404 = wrong token, no scope, or no access to that repo.
```

## Fix recipe

```bash
# Get the live token from the gh keyring
gh auth token > /tmp/gh_token.txt

# Replace GITHUB_TOKEN in the env file (do NOT print the value)
python3 - <<'PY'
tok = open('/tmp/gh_token.txt').read().strip()
path = '/home/thomas/.hermes/.env'
lines = [l for l in open(path) if not l.startswith('GITHUB_TOKEN=*** 'w').writelines(lines)
import os; os.chmod(path, 0o600)
PY
printf 'GITHUB_TOKEN=*** "$(cat /tmp/gh_token.txt)" >> ~/.hermes/.env
shred -u /tmp/gh_token.txt

# Restart the gateway so it re-reads the env
systemctl --user restart hermes-gateway.service
```

## Pitfalls

- **Never use f-strings with `***` in shell commands.** The terminal/execute_code redaction layer substitutes `***` with a directory listing of the cwd, corrupting the curl Authorization header. Always source the token from a file (`$(cat /tmp/gh_token.txt)`) and never embed the literal value in a Python f-string that gets passed to a shell.
- **The .env line `GITHUB_TOKEN=*** is what you get if the redaction layer mangled the write. Verify with `grep -n GITHUB_TOKEN ~/.hermes/.env` — the value should be 40 chars starting with `gho_` (or `ghp_` / `github_pat_`).
- **Don't restart the gateway with `kill <pid>`.** It's supervised by `systemd --user` and will be respawned under the same PID. Use `systemctl --user restart hermes-gateway.service` to pick up the new env cleanly.
- **No `GITHUB_TOKEN` in `.env` ≠ token doesn't exist.** The user may have authenticated `gh` an hour ago — the token is in the keyring, just not exposed to the gateway. Always check `.env` first before making the user re-run `gh auth login`.

## When the fix doesn't work

| Symptom | Cause |
|---------|-------|
| Bot still 404s after restart | Token was overwritten in flight — re-run the fix; check `systemctl --user status hermes-gateway.service` for env-load errors |
| `403` instead of 404 | Token is valid but fine-grained and lacks the specific repo in its allow-list → regenerate at github.com/settings/tokens with the right repo access |
| Token works for `curl` but not the bot | Bot may be running in a different systemd context — check `systemctl --user show hermes-gateway.service -p Environment` and confirm `GITHUB_TOKEN` is in the inherited env |
