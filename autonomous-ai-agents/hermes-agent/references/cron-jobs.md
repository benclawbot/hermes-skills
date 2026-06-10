# Cron Jobs — Scheduler Reference

## How the Scheduler Executes Scripts

The Hermes cron scheduler (`no_agent` mode) prepends `~/.hermes/scripts/` to the script path and **splits the command on spaces**. This has a critical implication:

❌ **Wrong** — any command with spaces breaks:
```
hermes cron create "* * * *" --script "python3 /home/user/.hermes/skills/my-skill/scripts/watch.py" ...
```
→ Scheduler runs: `/home/user/.hermes/scripts/python3 /home/user/.hermes/skills/my-skill/scripts/watch.py`
→ Result: `Script not found` (because `/home/user/.hermes/scripts/python3` doesn't exist)

✅ **Correct** — use a wrapper shell script with no spaces:
```bash
# Create wrapper in ~/.hermes/scripts/ (one-time)
cat > ~/.hermes/scripts/watch_sessions.sh << 'EOF'
#!/bin/bash
exec python3 /home/user/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions.py
EOF
chmod +x ~/.hermes/scripts/watch_sessions.sh

# Cron job — pass only the wrapper name
hermes cron create "* * * *" \
  --script "watch_sessions.sh" \
  --name "session-to-obsidian watchdog" \
  --no-agent
```

The wrapper lives in `~/.hermes/scripts/`, so the scheduler finds it at the prepended path. The wrapper then calls python3 with the full path inside.

## Verifying Cron Output

Cron job outputs land in `~/.hermes/cron/output/<job_id>/`. Each run produces a `.md` file. Check here for:
- `Script not found` → wrapper missing or still using spaced command
- `error` status → script ran but threw an exception
- `NO_NEW_SESSIONS` → clean, no-op run (normal for watchdogs)

## Restart Behavior

When the gateway restarts, the in-memory home channel mapping clears. The Telegram bot reconnects but Hermes forgets which chat is home. Run `/sethome` in the chat to re-establish. The home channel is persisted in `~/.hermes/channel_directory.json` after `/sethome` is called.

## Common Cron Failure Patterns

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Script not found: /home/user/.hermes/scripts/python3 ...` | Spaced command passed to scheduler | Use wrapper script in `~/.hermes/scripts/` |
| `last_status: error` but script runs manually fine | Env vars missing in cron context | Script must be fully self-contained or source `~/.hermes/.env` |
| Cron fires but nothing happens | `state` file prevents re-processing | Check `~/.hermes/sessions/.session_watchdog_state` |
| Gateway restart clears home channel | Expected — in-memory state lost | `/sethome` in the target chat |
