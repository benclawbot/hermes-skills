# Telegram Bot Setup

## Token

Add to `~/.hermes/.env`:
```
TELEGRAM_BOT_TOKEN=<token>
```

The gateway reads `.env` at startup and auto-enables Telegram when the token is present.

## Dependency

The gateway requires `python-telegram-bot`. Install it into the hermes venv using `uv`:

```bash
# Preferred — always targets the correct Python (use the venv's python path):
uv pip install --python /path/to/.venv/bin/python3 python-telegram-bot

# Common venv paths on this machine:
uv pip install --python ~/Desktop/hermes-agent/.venv/bin/python3 python-telegram-bot
```

**Why `--python`?** Without it, `uv pip install` targets the current `PATH` python (system Python, not the venv). The venv may also lack `pip` entirely (no `.venv/bin/pip`), making `python -m pip install` unavailable. The `--python` flag bypasses both issues.

**After install, verify** the library is in the venv:
```bash
ls ~/.hermes/venv/lib/python*/site-packages/ | grep telegram
```

Then restart the gateway:
```bash
systemctl --user restart hermes-gateway
```

If `.venv/bin/pip` doesn't exist, `uv pip install --python <venv_path>` always works.

## Restart

After installing the library or changing `.env`, restart the gateway:
```bash
systemctl --user restart hermes-gateway
```

Note: `hermes gateway restart` from a Telegram chat triggers a graceful drain (waits up to 180s for agents to finish) and can hang if a long request is in flight. Use systemd directly for reliable restarts.

## Voice Messages & STT

Voice messages are auto-transcribed if Whisper is installed in the Hermes venv:

```bash
uv pip install --python ~/Desktop/hermes-agent/.venv openai-whisper
```

Without it, voice files are received and cached (at `/home/thomas/.hermes/cache/audio/`) but not transcribed — the message arrives as empty text.

## Allowlisting Users

By default all Telegram users are **denied**. To allow yourself:

1. DM the bot — your denied request logs your user ID
2. Extract the ID from logs:
   ```bash
   grep -i "denied\|telegram.*id\|user.*id" ~/.hermes/logs/gateway.log | tail -20
   ```
3. Add to `~/.hermes/.env`:
   ```
   TELEGRAM_ALLOWED_USERS=your_numeric_id_here
   ```
   Or for open access during testing:
   ```
   GATEWAY_ALLOW_ALL_USERS=true
   ```

4. Restart: `hermes gateway restart`
