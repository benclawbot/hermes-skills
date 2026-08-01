#!/usr/bin/env bash
# install-<TARGET>.sh — one-shot setup for <APP> on <TARGET_OS>.
#
# Implements README step N. Re-runnable (idempotent).
# Use NONINTERACTIVE=1 to skip prompts in CI / scripted deploys.
#
# Usage:
#   bash install-<TARGET>.sh
#   NONINTERACTIVE=1 bash install-<TARGET>.sh
#
set -euo pipefail

# ── Config (override via env if needed) ──────────────────────────────────────
REPO_URL="${REPO_URL:-https://github.com/<OWNER>/<REPO>.git}"
REPO_DIR="${REPO_DIR:-$HOME/<REPO_DIR>}"
HUB_DIR="$REPO_DIR/<SUBDIR>"
DB_DIR="$HOME/<APP_STATE_DIR>"
ENV_FILE="$HOME/<APP_STATE_DIR>/.env"
LOG_DIR="<LOG_DIR>"  # macOS: ~/Library/Logs/<app>  |  Linux: $HOME/.local/share/<app>/logs
NODE_MIN_MAJOR=<MIN_NODE_MAJOR>

# ── Helpers ─────────────────────────────────────────────────────────────────
bold() { printf '\n\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m! %s\033[0m\n' "$*"; }
die()  { printf '\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$*"; }

# ── 0. Prereqs ───────────────────────────────────────────────────────────────
bold "[0/<N>] Checking prereqs..."

command -v gh >/dev/null    || die "gh CLI not installed (<pkg manager install cmd>)"
command -v node >/dev/null  || die "node not installed (<pkg manager install cmd>)"
command -v npm >/dev/null   || die "npm not installed (comes with node)"

NODE_VER=$(node -p "process.versions.node.split('.')[0]")
[[ "$NODE_VER" -ge "$NODE_MIN_MAJOR" ]] \
  || die "node $NODE_VER detected — need $NODE_MIN_MAJOR+. <fix>"

gh auth status >/dev/null 2>&1 \
  || die "gh not authenticated — run: gh auth login"
ok "gh, node $(node --version), npm $(npm --version)"

mkdir -p "$LOG_DIR" "$DB_DIR" "$(dirname "$ENV_FILE")"

# ── 1. Clone ─────────────────────────────────────────────────────────────────
bold "[1/<N>] Cloning repo..."
if [[ -d "$REPO_DIR/.git" ]]; then
  ok "Already cloned at $REPO_DIR"
  (cd "$REPO_DIR" && git pull --ff-only) >> "$LOG_DIR/install.log" 2>&1 \
    || warn "git pull failed — continuing with local checkout"
else
  git clone "$REPO_URL" "$REPO_DIR" >> "$LOG_DIR/install.log" 2>&1 \
    || die "git clone failed — check network / gh auth"
  ok "Cloned to $REPO_DIR"
fi

# ── 2. Deps ──────────────────────────────────────────────────────────────────
bold "[2/<N>] Installing deps..."
(cd "$HUB_DIR" && npm install --no-audit --no-fund) \
  >> "$LOG_DIR/install.log" 2>&1 \
  || die "npm install failed — see $LOG_DIR/install.log"
ok "deps installed"

# ── 3. Env file (idempotent, supports NONINTERACTIVE) ────────────────────────
bold "[3/<N>] Configuring env..."
touch "$ENV_FILE"
chmod 600 "$ENV_FILE"

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

write_if_missing "<KEY_1>" "<Prompt for KEY_1>" ""
write_if_missing "<KEY_2>" "<Prompt for KEY_2>" "<optional_default>"
ok "env at $ENV_FILE (chmod 600)"

# ── 4. Sanity-check the network (ALWAYS --max-time) ──────────────────────────
bold "[4/<N>] Sanity check..."
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a
if [[ -n "${<TOKEN_VAR>:-}" ]]; then
  if curl -fsS --max-time 5 "https://api.<SERVICE>/<token-check-endpoint>" \
       > "$LOG_DIR/<check>.json" 2>/dev/null; then
    ok "<SERVICE> reachable"
  else
    warn "<SERVICE> check failed — token may be wrong"
  fi
else
  warn "<TOKEN_VAR> empty — <thing> will not start until set"
fi

# ── 5. First pipeline run ────────────────────────────────────────────────────
bold "[5/<N>] First pipeline run..."
bash "$HUB_DIR/run-<THING>.sh" 2>&1 | tee -a "$LOG_DIR/install.log"
ok "First run logged to $LOG_DIR/<run>.log"

# ── 6. Cron (idempotent) ────────────────────────────────────────────────────
bold "[6/<N>] Installing cron (every 30 min)..."
CRON_LINE="*/30 * * * * $HUB_DIR/<cron-target>.sh >> $LOG_DIR/<cron>.log 2>&1"
TMP_CRON=$(mktemp)
crontab -l 2>/dev/null > "$TMP_CRON" || true
if grep -Fq "$HUB_DIR/<cron-target>.sh" "$TMP_CRON" 2>/dev/null; then
  ok "Cron job already present"
else
  echo "$CRON_LINE" >> "$TMP_CRON"
  crontab "$TMP_CRON"
  ok "Installed: $CRON_LINE"
fi
rm -f "$TMP_CRON"

# ── Done ────────────────────────────────────────────────────────────────────
bold "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ok "Install complete."
echo "  Repo:    $REPO_DIR"
echo "  Hub:     $HUB_DIR"
echo "  DB:      $DB_DIR"
echo "  Env:     $ENV_FILE"
echo "  Logs:    $LOG_DIR"
echo ""
echo "Next steps:"
echo "  1. <thing 1>"
echo "  2. <thing 2>"
echo "  3. <thing 3>"
