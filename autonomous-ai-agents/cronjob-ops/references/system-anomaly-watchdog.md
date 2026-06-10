---
name: system-anomaly-watchdog
description: Watchdog that monitors Hermes cron health, gateway status, disk/memory anomalies and alerts proactively. Runs as no_agent cron job — outputs alert text or "NO_ANOMALIES". Silent when healthy.
version: 1.0.0
---

# System Anomaly Watchdog

Monitors Hermes cron jobs, gateway service, disk and memory — delivers alerts to Telegram when something needs attention.

## How it works

- `watch_anomalies.py` runs as no_agent cron job every 30 min
- Silent when all checks pass → nothing sent
- Alert when: cron job failed, gateway down, disk ≥90%, memory ≥90%

## Alert conditions

| Check | Threshold | Condition |
|-------|-----------|-----------|
| Cron job status | — | Any job with last_status ≠ ok/running |
| Gateway | — | systemctl --user is-active hermes-gateway ≠ active |
| Disk | 90% | df -h on / or /home |
| Memory | 90% | free -m Mem used_pct |

## Cron job setup

```bash
# Create wrapper (already done in ~/.hermes/scripts/)
cat > ~/.hermes/scripts/watch_anomalies.sh << 'EOF'
#!/bin/bash
exec python3 /home/thomas/.hermes/scripts/watch_anomalies.py
EOF
chmod +x ~/.hermes/scripts/watch_anomalies.sh

# Create cron — name only, no spaces (scheduler prepends ~/.hermes/scripts/)
hermes cron create "*/30 * * * *" \
  --script "watch_anomalies.sh" \
  --name "system-anomaly-watchdog" \
  --deliver origin \
  --no-agent
```

## Test manually

```bash
python3 /home/thomas/.hermes/scripts/watch_anomalies.py
# Expected: "NO_ANOMALIES" (healthy)
```

## Files

- `~/.hermes/scripts/watch_anomalies.py` — main script
- `~/.hermes/scripts/watch_anomalies.sh` — wrapper for cron scheduler
