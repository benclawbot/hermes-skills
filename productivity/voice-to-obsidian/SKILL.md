---
name: voice-to-obsidian
version: 2.0.0
description: >
  Auto-save every voice note sent via Telegram to the Obsidian vault inbox.
  Trigger on ANY incoming voice message (no user prompt required). Backstop:
  if the hook is broken, run the script manually. Covers the gateway
  pre_gateway_dispatch hook, the audio_cache scan pattern, the processed
  marker file, and the dedup rules. The hook script is
  ~/.hermes/scripts/voice-to-obsidian-hook.py and is wired in
  ~/.hermes/config.yaml under agent.hooks.pre_gateway_dispatch.
metadata:
  hermes:
    tags: [telegram, voice, obsidian, automatic, hook]
---

# Voice to Obsidian (automatic)

**Every voice note the user sends is auto-saved to Obsidian.** No command
required. No "save voice" prompt. The user just sends audio.

## How it works (current architecture)

1. Telegram gateway caches incoming voice in `~/.hermes/audio_cache/audio_*.{ogg,mp3,m4a}`
2. Gateway fires `pre_gateway_dispatch` shell hook on every inbound message
3. Hook (`~/.hermes/scripts/voice-to-obsidian-hook.py`) scans the audio cache
4. Compares files against `~/.hermes/state/voice-obsidian-processed.json`
5. For each new file: transcribe with Whisper (base model, local), append to
   `~/Desktop/Memory/Voice Notes/YYYY-MM-DD.md` (one file per day, all voices
   for the day appended)
6. Update marker with basenames of processed files

**Marker file location:** `~/.hermes/state/voice-obsidian-processed.json`
(simple list of basenames, not full paths).

**Note format (current):**

```markdown
# Voice Notes — 2026-06-07

## 11:49
<transcript>
Source: /home/thomas/.hermes/audio_cache/audio_xxx.ogg

## 18:04
<transcript>
Source: ...
```

No YAML frontmatter. The daily file uses H1 + H2 structure, all voices
for the day appended under their timestamps.

## Event-agnostic hook pattern (why it scans the cache, not the event)

The `pre_gateway_dispatch` shell-hook bridge does
`json.dumps(..., default=str)` on its event payload, which stringifies
the nested `MessageEvent` dataclass to its `__repr()` string. So fields
like `media_urls` and `media_types` are NOT at the top level of the JSON
the hook receives — they're inside `extra.event` as a repr blob.

If a hook script does `event_data.get("media_urls")` and gets `None`, the
"nothing to do" branch exits 0 cleanly and you get a **silent no-op**.
This is the classic shell-hook silent failure — see
`hermes-housekeeping/references/shell-hook-silent-failure.md` for full
details and the 3-angle diagnosis path.

**The fix is to make hooks event-agnostic:** scan filesystem state
(audio_cache, log dirs) for new files since the last successful run,
using a marker file. Works regardless of what the gateway passes in
the event payload.

## Hook configuration (canonical)

In `~/.hermes/config.yaml`:

```yaml
agent:
  hooks:
    pre_gateway_dispatch:
    - command: python3 /home/thomas/scripts/voice-to-obsidian-hook.py
      timeout: 120
```

`hooks_auto_accept: true` skips the per-invocation consent prompt
(required for fully-automatic operation).

**After any change to the hook script, restart the gateway:**

```bash
systemctl --user restart hermes-gateway
```

`force-restart` is NOT a valid `systemctl` verb — don't suggest it.
Verify with `systemctl --user is-active hermes-gateway` and check
`~/.hermes/logs/agent.log` for:

```
shell hook registered: pre_gateway_dispatch -> python3 .../voice-to-obsidian-hook.py
```

## Manual backstop (when the hook is broken)

If the auto-hook is misfiring (e.g. user reports "voice didn't save"):

```bash
# 1. List unprocessed files
python3 -c "import json,os; m=json.load(open(os.path.expanduser('~/.hermes/state/voice-obsidian-processed.json'))); cache=os.path.expanduser('~/.hermes/audio_cache'); done=set(m.get('processed', [])); print('\n'.join(sorted(f for f in os.listdir(cache) if f.endswith(('.ogg','.mp3','.m4a')) and f not in done)))"

# 2. Run hook manually (same script, same processing path)
python3 ~/.hermes/scripts/voice-to-obsidian-hook.py
# Takes ~5-10s per voice with whisper base. Catches up on the backlog.
# 120s hard timeout per invocation — if backlog > 10 voices, split runs.
```

## Pitfalls

- **Don't read `event_data.get("media_urls")` in a pre_gateway_dispatch
  shell hook.** Always None. The field is at `event_data["extra"]["event"]`
  as a repr string. Scan the filesystem instead. (See "Event-agnostic
  hook pattern" above.)
- **Don't change the hook script without restarting the gateway.**
  The shell-hook system loads the script into memory at gateway start
  and re-uses it for the lifetime of the process. The on-disk file is
  not re-read on each invocation.
- **Don't use a complex / pattern in create_new_note vs append_to_note.**
  Use the same H1+H2 structure for both. Mixed formats make daily notes
  unreadable. The current canonical format: H1 `# Voice Notes — YYYY-MM-DD`
  + one H2 `## HH:MM` per voice, with `Source: <path>` line after the
  transcript.
- **Don't store full paths in the processed marker.** Use basenames only
  (filename, not absolute path). Mixed entries from older versions of
  the hook cause false "unprocessed" matches. Normalize on write.
- **Don't store the script's `create_new_note` body when the file
  already exists.** Always check-then-append, never overwrite. The
  append path is the one that matters for steady-state operation.
- **Don't run `systemctl --user force-restart`.** It's not a valid verb.
  Use `restart` and confirm `Active: active (running)` after.
- **Don't add a daily "did you save your voice?" cron.** That's a
  crutch for a broken hook. Fix the hook, not the workflow. Voice
  transcription on inbound should be silent and automatic — if the
  user has to be reminded, the system is broken.
- **Audit existing crutches — the rule is often violated in earlier
  sessions.** A previous session may have added a "voice note
  reminder" job that fires daily/hourly, creates noise, and
  double-fires with the working hook. The rule against this is
  necessary but not sufficient; you also need a detection step.
  Run `python3 ~/.hermes/skills/voice-to-obsidian/scripts/audit_reminder_cron.py`
  (exit 0 = clean, exit 1 = crutch(es) found, exit 2 = config
  unreadable). It scans `~/.hermes/cron/jobs.json` for jobs whose
  name / prompt / script matches known crutch patterns and prints
  the offending job IDs. Pair with `hermes cron remove <job_id>`.
  Wire into `~/.hermes/scripts/nightly-audit.sh` if you want this
  on schedule. **Verified 2026-06-08:** a daily `Voice Note
  Reminder` cron (job `05ffc0b2d35e`) had been added by an
  earlier session, fired daily at 18:00 counting *any* `.ogg`
  modified in the last 24h as "captured today" — and nags the
  user about audio that's already in the Obsidian file via the
  working hook. The script caught it in one call.
- **Don't blindly transcribe when whisper isn't installed.** The hook
  should log `UNMATCHED_AUDIO_TRANSCRIBE_FAIL` to stderr and skip the
  file (don't mark it processed — retry next run). Auto-install:
  `pip install openai-whisper` then `python3 -c "import whisper; whisper.load_model('base')"`
  to warm the cache.

## Verification

A working voice-to-obsidian setup passes all of these:

1. `systemctl --user is-active hermes-gateway` → `active`
2. `grep "voice-to-obsidian-hook" ~/.hermes/logs/agent.log | tail -3` →
   shows recent registration (within last gateway restart)
3. Send a test voice note → within 10s, new H2 section appears in
   `~/Desktop/Memory/Voice Notes/<today>.md`
4. `python3 -c "import json; d=json.load(open(os.path.expanduser('~/.hermes/state/voice-obsidian-processed.json'))); print(len(d.get('processed', [])))"` →
   grows by 1 per voice
5. Hook mtime is fresh (`ls -la ~/.hermes/scripts/voice-to-obsidian-hook.py`)
   — if the script is older than the last gateway restart, the running
   version is the OLD code, not what's on disk
