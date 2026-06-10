# Shell-Hook Silent Failure

The shell-hook bridge can fire a registered hook with **empty or wrong-shaped event data**, and the hook script will run cleanly, exit 0, and produce no log line. The pipeline looks healthy in `last_status` while doing nothing.

**Use this file when** a `pre_gateway_dispatch` consumer (voice-to-obsidian, url-saver, custom bots) seems to never fire despite being registered + approved in config.

## The Bug

`agent.shell_hooks._serialize_payload` does:

```python
json.dumps(payload, default=str)
```

For nested dataclass objects (like `MessageEvent`), `default=str` calls `str(event)`, which returns the dataclass's `__repr__` — a string like `"MessageEvent(text='', media_urls=..., sender=...)"`. The hook script then reads the JSON, and **any field it expects at the top level is `None`**.

```python
# What the script reads
event_data = json.loads(sys.stdin.read())
media_urls = event_data.get("media_urls")  # None — field is at extra.event
media_types = event_data.get("media_types")  # None
```

The script's "no audio found" branch exits 0. No error. No log. The gateway proceeds to the agent. The agent receives the message and processes it. Everything looks fine.

**The script works when run manually** with the right shape (direct dict with `media_urls` at top level). That's why this bug hides in testing.

## Diagnosis Path

1. **Confirm the hook is registered** — `~/.hermes/logs/agent.log | grep "shell hook registered"`. Look for the script path + event name.
2. **Confirm the hook is approved** — check `~/.hermes/state/shell_hook_approvals.json` (or wherever the allowlist lives in current version).
3. **Look for the script's log output** — most hook scripts log to `~/.hermes/logs/agent.log` or to a state file. If there's no log line at all, the script ran but found nothing to do.
4. **Reproduce manually with the real gateway shape** — run the script with `echo '{}' | python3 script.py`. If it exits 0 with no log, that's the bug pattern. Then run with the actual data structure the bridge sends: `echo '{"hook_event_name":"pre_gateway_dispatch","extra":{"event":<event-repr>}}' | python3 script.py` — the `event` field will be a repr string, not a dict.
5. **Verify with `str(type(...))` check** — in the script, print the type of every field it reads. If `event_data.get("media_urls")` returns None but the field is at `event_data["extra"]["event"]`, you've found it.

## The Fix: Event-Agnostic Hooks

Don't depend on the event payload structure. Scan the filesystem for new state since last run. This works regardless of what the bridge sends.

**Pattern (worked example from `voice-to-obsidian-hook.py`):**

```python
# Old (broken — relies on event payload)
def run(self):
    event_data = json.loads(sys.stdin.read())
    media_urls = event_data.get("media_urls") or []
    if not media_urls:
        return  # silently exits 0
    for url in media_urls:
        process(url)

# New (event-agnostic — scans filesystem state)
def run(self):
    audio_cache = Path("~/.hermes/audio_cache").expanduser()
    state_file = Path("~/.hermes/state/voice-obsidian-processed.json")
    processed = {Path(p).name for p in json.loads(state_file.read_text()).get("files", [])}
    new_files = [f for f in audio_cache.glob("*.ogg") if f.name not in processed]
    for f in new_files:
        process(f)
        processed.add(f.name)
    state_file.write_text(json.dumps({"files": sorted(processed)}, indent=2))
```

**Why this works:**
- Fires on every `pre_gateway_dispatch` event (so it runs whenever any inbound message arrives — exactly the right cadence for a voice watcher)
- Idempotent: re-running does nothing if state matches filesystem
- Self-recovering: catches up on backlog if the hook was down for hours
- Robust to bridge schema changes: doesn't care what the event payload looks like

**Trade-off:** Only fires when a message arrives. If the gateway receives zero messages for 2 days, the hook also doesn't fire — but the same is true of the broken version, so this is no regression. If you need true periodic execution, use a cron job (separate `no_agent` watchdog) and don't try to wedge it into a hook.

## Other `pre_gateway_dispatch` Consumers Likely Affected

Search for hooks that read from stdin + parse event fields:

```bash
grep -lE "json\.loads\(sys\.stdin" ~/.hermes/scripts/*.py
```

For each match, check if the script reads fields at the top level. If yes, refactor to scan filesystem state.

## Verification

After the fix:

1. **Check registration is fresh** — `~/.hermes/logs/agent.log | grep "shell hook registered"` should show your updated script path with a recent timestamp (post-restart).
2. **Send a test trigger** — a new voice message, a new URL paste, whatever the hook watches.
3. **Check the side effect** — Obsidian note updated, URL file written, etc.
4. **Re-run with empty stdin** — `echo '{}' | python3 script.py` should now find and process any unprocessed files (catches up on backlog).

## Pitfalls

- **Don't add a `try/except` that swallows the empty-event case as "nothing to do."** The bug is in the bridge, not in the script's logic. Refactor to be event-agnostic instead.
- **Don't fix the bridge** unless you control upstream (you don't, on the hermes-agent fork boundary). The event-agnostic pattern is the right workaround.
- **Don't trust `script_mtime_at_approval` in the allowlist** to re-prompt on script change. The field is recorded but the existing approval carries through edits. The hook will run new code without re-approval.
- **Don't assume `json.dumps(..., default=...)` is a no-op for nested objects.** It silently breaks. Always check the actual JSON shape end-to-end.
- **Restart the gateway** after script changes — hooks are loaded into memory at gateway startup, not reloaded on file change.

## Related

- `references/cron-silent-failure.md` — the same "looks fine, does nothing" pattern but for cron-watched pipelines. The diagnostic shape is identical: state file mtime < source dir mtime, or the script's exit-0 path is the wrong path.
- `references/clarify-tool-pitfalls.md` — another "the wire protocol mangles what you send" gotcha. Different mechanism (gateway `str(c).strip()`) but same lesson: trust the on-the-wire shape, not the docs.
