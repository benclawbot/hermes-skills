---
name: session-continuity
description: On gateway restart, automatically summarize last session topics and write to Obsidian. Hooked via systemd ExecStartPost so it runs immediately when Hermes comes back up.
version: 1.0.0
---

# Session Continuity

When Hermes gateway restarts, this script runs automatically and writes the last session's topics to Obsidian, so the next conversation has context without the user re-explaining.

## How it works

```
Gateway restart → systemd ExecStartPost → session_continuity.sh
→ session_continuity.py → reads sessions.json
→ finds last session for this chat
→ extracts last 3 user message topics
→ appends "### Reconnection HH:MM" block to Obsidian daily note
→ logs to /tmp/session_continuity.log
```

## Files

- `~/.hermes/scripts/session_continuity.py` — main script
- `~/.hermes/scripts/session_continuity.sh` — wrapper for systemd
- `~/.config/systemd/user/hermes-gateway.service.d/override.conf` — systemd hook

## Manual test

```bash
python3 /home/thomas/.hermes/scripts/session_continuity.py
cat /tmp/session_continuity.log
```

## After gateway restart

Check the Obsidian daily note for a `### Reconnection HH:MM` block with the last session's topics.

## Requirements

- `sessions.json` must have a valid `session_id` for the target chat
- Obsidian vault at `~/Dropbox/memory/Obsidian`
- systemd user daemon reload after changes: `systemctl --user daemon-reload`
