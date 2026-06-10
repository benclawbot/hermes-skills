# Hermes Venv Management

## Finding the venv

The hermes-gateway systemd service defines the venv path:
```bash
grep ExecStart ~/.config/systemd/user/hermes-gateway.service
```

This venv is managed by the hermes install at `~/Desktop/hermes-agent/` (not at `~/.hermes/hermes-agent/` which doesn't exist).

## Installing packages

**`.venv/bin/pip` often doesn't exist** in hermes-managed venvs. Use uv:

```bash
uv pip install --python /path/to/.venv python-telegram-bot
```

uv is at `~/.local/bin/uv` and is always available.

Alternative if uv unavailable — use the venv python directly:
```bash
/path/to/.venv/bin/python -m pip install <package>
```
This only works if the venv was created with pip support.

## Key packages for Telegram

```bash
uv pip install --python ~/Desktop/hermes-agent/.venv python-telegram-bot
```

## Installing Whisper (STT / voice transcription)

For voice message transcription (STT), Whisper needs to be in the Hermes venv. This is needed when voice messages arrive but aren't transcribed.

```bash
uv pip install --python ~/Desktop/hermes-agent/.venv openai-whisper
```

- System pip is externally-managed — `--break-system-packages` fails inside the venv
- `.venv/bin/pip` doesn't exist in hermes-managed venvs — `uv` is the correct tool
- After install, verify: `python3 -c "import whisper; print('ok')"`
- Voice messages cache to: `/home/thomas/.hermes/cache/audio/`
