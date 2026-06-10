# Gateway Debugging Reference

## Crash Loop Diagnosis

When the gateway is in a crash loop, systemd restarts it repeatedly. Find the actual error:

```bash
# 1. Check systemd status
hermes gateway status

# 2. Get the actual error from journal
journalctl --user -u hermes-gateway -n 200 | tail -80

# 3. Check request dumps (written on API failure)
ls -t ~/.hermes/sessions/request_dump*.json | head -1
cat ~/.hermes/sessions/request_dump_*.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d, indent=2))"
```

## "No Auxiliary LLM Provider Configured" — Misleading Warning

This warning appears in the gateway log as:

```
⚠ No auxiliary LLM provider configured — context compression will drop middle turns without a summary.
```

**This is a downstream symptom, not the root cause.** The real problem is that the main LLM API calls are failing. The auxiliary system can't initialize when the main provider is unreachable.

**Root causes to check in order:**
1. `MINIMAX_API_KEY` missing from `~/.hermes/.env` — request dump shows `"Authorization": "Bearer None"`
2. API endpoint unreachable (network/firewall)
3. Config has wrong `model` name

**Debug step:** Check the request dump for the actual API key state:
```bash
grep "Authorization" ~/.hermes/sessions/request_dump*.json | head -3
```

If it says `Bearer None`, the API key is not loaded. Fix:
```bash
printf 'MINIMAX_API_KEY=your_key_here\n' >> ~/.hermes/.env
hermes gateway restart
```

## Common Gateway Failures

| Symptom | Check | Fix |
|---------|-------|-----|
| Crash loop on startup | `journalctl --user -u hermes-gateway` | Missing env var or dependency |
| `Connection error` to API | `curl -s -o /dev/null -w "%{http_code}" https://api.minimax.io/anthropic` | Network or API key |
| Telegram silent | `journalctl --user -u hermes-gateway` + search "denied" | User not allowlisted |
| Gateway dies on logout | `loginctl enable-linger $USER` | Systemd linger not enabled |

## Restart Hangs / Drain Timeout

When you trigger a restart from Telegram (`/restart`), the gateway tries a **graceful drain** — it waits up to 180s for active agents to finish. If an agent is mid-long-API-call, the drain times out and the restart appears to hang.

**Symptoms:**
- Telegram bot stops responding to commands but `hermes gateway status` shows it as running
- `tail -f ~/.hermes/logs/gateway.log` shows `Gateway drain timed out after 180.0s`
- `hermes gateway restart` returns success but nothing actually restarts

**Why it happens:**
The drain timeout is 180s. If an API call is taking longer than that (MiniMax API issues, stuck agent loop, etc.), the gateway force-kills the agent but then gets stuck — systemd never picks up the restart because the service is already running under a stale PID.

**Fix — use systemd directly:**
```bash
systemctl --user restart hermes-gateway
```
This bypasses the graceful drain entirely and force-restarts the service immediately.

**Recovery checklist when this happens:**
1. `ps aux | grep hermes` — check for old/stuck processes
2. `kill -9 <stuck_pid>` if needed
3. `systemctl --user restart hermes-gateway`
4. `sleep 6 && tail ~/.hermes/logs/gateway.log` — verify new instance started
5. Confirm Telegram reconnects (look for `Connected to Telegram` in log)

**Prevention:** Trigger restarts at quiet times when no long requests are in flight. Alternatively, send `/stop` in the Telegram chat first to cancel any running agent, then restart.
