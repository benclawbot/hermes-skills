---
name: hermes-housekeeping
description: "Self-maintenance tasks for the local Hermes Agent install — health checks, config migration, toolset cleanup, provider/router troubleshooting, and lightweight infrastructure audits. Use when Thomas says 'check hermes', 'hermes health', 'is everything ok', 'clean up hermes', 'any improvements', 'audit hermes', or asks about config versions, missing API keys, broken toolsets, gateway logs, or cron health. Also triggers on 'cron is active but nothing happens' / 'pipeline broken silently' / 'watchdog silent' / 'cron ok but no output' (see references/cron-silent-failure.md). Covers hermes doctor / doctor --fix, hermes tools list / enable / disable, hermes cron list, systemctl --user status hermes-gateway, and the canonical quiet-restart procedure. Does NOT cover feature work or new tool creation — that lives in hermes-agent."
triggers:
  - check hermes
  - hermes health
  - is hermes ok
  - audit hermes
  - clean up hermes
  - any improvements
  - what can be improved
  - hermes doctor
  - missing API keys
  - toolsets not working
  - cron active but nothing happens
  - watchdog silent
  - pipeline broken silently
  - cron ok but no output
  - sessions not appearing
  - remove risky skills
  - audit skills
  - clean up skills
  - find any bug
  - find missing logic
  - anything that doesn't belong
  - remove all
  - remove entirely
  - remove completely
  - sweep .hermes
  - first look at
---

# Hermes Housekeeping

Lightweight, agent-driven maintenance for the local Hermes install. Thomas leans slim — every disabled toolset, every "system dependency not met" warning, every doctor issue that's actually noise should be triaged, not just listed.

**Loaded skill territory note:** `hermes-agent` is the bundled umbrella for full Hermes configuration, providers, and skill management. This skill is the **operational / housekeeping** overlay — quick health sweeps, fix-the-noise cleanups, and the canonical audit sequence. It does NOT duplicate the `hermes-agent` reference library; load `hermes-agent` for provider setup, gateway install, plugin authoring, etc.

## Canonical Audit Sequence

Run in this order — each step's output feeds the next:

```bash
hermes doctor                                    # 1. Overall health
hermes doctor --fix                              # 2. Auto-fix what can be auto-fixed
hermes cron list                                 # 3. Verify all jobs: last_status == ok
hermes tools list                                # 4. Inventory toolsets (enabled vs broken)
systemctl --user status hermes-gateway --no-pager # 5. Gateway alive?
grep -iE "error|warning|traceback" ~/.hermes/logs/gateway.log | tail -25   # 6. Recent log noise
df -h ~ | tail -1                                # 7. Disk pressure
du -sh ~/.hermes/sessions/                       # 8. Session store size
```

**Step 9 (silent-pipeline check):** if any cron job's output looks stale despite `last_status: ok`, the cron layer is fine but the script is broken. Quick check: `python3 ~/.hermes/skills/hermes-housekeeping/scripts/diagnose_watchdog.py --source-dir <src> --state-file <state> --watcher-script <script> --skill-md <skill>` — exit 0 healthy, exit 1 stale state, exit 2 SKILL.md/code drift, exit 3 both. For full debugging, see `references/cron-silent-failure.md` (5 patterns: Sandy silent no-op, writer/watcher format mismatch, missing source of truth, paused cron, SKILL.md/code drift). The classic tell: newest entry in the watcher's state file is older than the newest file in its source dir.

After the sweep, **always restart the gateway** to apply any `hermes doctor --fix` or `hermes tools disable` changes:

```bash
systemctl --user restart hermes-gateway
sleep 3
systemctl --user is-active hermes-gateway       # confirm active
```

## Triage Rules (verified live)

| Finding | Action |
|---------|--------|
| `hermes doctor --fix` says "Fixed N issue(s)" | Always run it — it migrates config versions and reapplies sane defaults. No downside. |
| Toolset shows `⚠ system dependency not met` AND no `.env` key configured | Safe to disable — clean up `hermes tools list` noise. |
| Toolset shows `⚠ missing X_API_KEY` | DON'T disable if user might fill the key later. Note as a manual-action item, not noise. |
| Telegram log shows 1-2 DNS retries ("Temporary failure in name resolution") | Self-heals. Do NOT act on transient blips — wait for repeats. |
| `! sync_full` showing 152k → 5k token compression | Working as designed. Don't "fix" it. |
| Cron job `last_status` = ok AND newest state entry is recent | Leave alone. |
| Cron job `last_status` = ok BUT output is stale (state < source dir mtime) | **Silent failure** — see `references/cron-silent-failure.md`. Don't assume cron is fine. |
| Cron job `last_status` ≠ ok | Run manually, apply 5 Whys (see `cronjob-ops` skill). |
| Browser toolset enabled but `agent-browser` has npm vulns | Disable browser (Thomas doesn't use it) — vulns become irrelevant. |
| `image_gen` shows "system dependency not met" | **False positive** if `POLLINATIONS_API_KEY` (or whichever provider's key) is in `~/.hermes/.env`. Pollinations only needs the key, no npm dep. Verify before "fixing". |

## Image Gen — Do NOT Route Through the Chat LLM

This is a recurring mental-model trap. When asked "can image gen be done by [main chat model]?" the answer is **no** — text LLMs don't generate images, they have vision only. The right path:

- `~/.hermes/config.yaml` → `image_gen.provider: pollinations` (or other dedicated provider)
- `~/.hermes/.env` → `POLLINATIONS_API_KEY=...` (free tier exists; full API key gets higher rate limits)
- Restart gateway to activate

Don't waste tokens suggesting the user switch chat models for image gen. Pollinations (or a dedicated provider like DALL-E / SD) is the answer.

## Lean Toolset Defaults for Thomas

Thomas's profile: Senior IT PM, prefers slim config, prunes unused skills regularly. The default `hermes tools list` includes several toolsets he'll never use. The lean set after a fresh audit:

**Keep enabled** (actually used):
- web, terminal, file, code_execution, vision, image_gen, tts, moa, skills, todo, memory, context_engine, session_search, clarify, delegation, cronjob, messaging, video, kanban (runtime-gated)

**Disable** (no backend / not used):
- browser, homeassistant, spotify, computer_use, video_gen, x_search, discord, discord_admin, hermes-yuanbao

**Platform-gated, not in CLI toolset** (no action needed, they're not enabled on the cli platform anyway):
- feishu_doc, feishu_drive (these are messaging platform adapters, not toolsets)

`hermes tools disable <name>` works for most. Some return "Unknown toolset" — those are platform-gated and can be ignored.

## RTK (Token Compression) — Always Verify, Don't Assume

RTK is the bash-alias-based CLI output compression layer. To verify it's actually active and not just installed:

```bash
rtk gain          # shows recent compression stats with % savings
```

Expected: 60-90% savings on common commands (ls, git diff, grep, find). If you see `< 30%` or `[warn] No hook installed` (Claude Code hook warning — expected for Hermes, ignore), something is wrong with the alias chain:

```bash
grep -nE "alias.*rtk" ~/.bash_aliases        # alias wrappers exist?
ls ~/.hermes/.hermes_env                      # preload file exists?
```

**Do NOT run `rtk init -g` blindly** — it installs Claude Code's hook, not Hermes's. Hermes already has RTK via bash aliases; no hook install is needed. If the user says "install the hook" without specifying, ask which system.

See `references/rtk-integration.md` (Path 1/2/3, hook contract, two-hook-systems pitfall) and `references/rtk-compress-plugin.md` (the working `transform_terminal_output` plugin source) for the full integration procedure.

## Reference Files

- `references/rtk-integration.md` — RTK (Rust Token Killer) install + 3 integration paths (bash aliases / `transform_terminal_output` plugin / `rtk init`), hook contract gotcha, two-hook-systems pitfall. Absorbed from the former `tool-output-compression` skill (archived 2026-07-25).
- `references/rtk-compress-plugin.md` — full source of the working `~/.hermes/plugins/rtk-compress/` plugin (filter map, safety nets, RTK CLI facts, measured 89.8% savings on 279 commands). Companion to `rtk-integration.md`.
- `references/rtk-verification-log.md` — 2025-05-08 verification log: rtk gain output format, expected vs actual savings, gateway restart recipe. Companion to `rtk-integration.md`.
- `references/image-gen-routing.md` — why image gen can't route through the chat LLM, Pollinations setup, and the "system dependency not met" false positive.
- `references/error-log-triage.md` — 4-step method for finding real bugs in `~/.hermes/logs/errors.log`. Quantify by tool, categorize by error string, find the actual bugs, verify against source. 99% of "ERROR" lines are noise (security/validator/agent mistakes). Use when `hermes doctor` shows unexpected issues or the user asks "any bug fixes" / "is anything broken".
- `references/git-pull-recovery.md` — safe stash → pull → pop sequence for a diverged `~/.hermes/hermes-agent/` checkout with uncommitted + untracked work. Use when `git status` shows "branch and origin/main have diverged" or when the user says "update hermes" / "pull latest".
- `references/cron-silent-failure.md` — debugging recipe for "cron job shows active and last_status=ok but the watched thing isn't happening." Covers 5 failure patterns (Sandy silent no-op, writer/watcher format mismatch, missing source of truth, paused cron, SKILL.md/code drift) with the 4-step diagnosis path and the defensive-warning pattern that makes the next silent break loud. Use when a pipeline is producing stale output or no output despite a healthy-looking cron. **This is the file to reach for when the user says "I don't see X happening" and the cron health check says everything's fine.**
- `references/shell-hook-silent-failure.md` — the `pre_gateway_dispatch` analog of cron-silent-failure: hook is registered + approved, fires on every event, but does nothing because the bridge's `json.dumps(..., default=str)` stringifies the nested `MessageEvent` dataclass to its repr. Fields at top level are `None`; script's "nothing to do" branch exits 0 cleanly. **Fix pattern: event-agnostic hooks that scan filesystem state, not the event payload.** Use when a `pre_gateway_dispatch` consumer (voice-to-obsidian, url-saver, custom bots) seems to never fire despite being registered. Worked example: 2026-06-07 voice-to-obsidian fix.
- `references/clarify-tool-pitfalls.md` — agent-side gotchas for the `clarify` tool. Schema is `List[str]` not `List[dict]` (gateway does `str(c).strip()` on each choice, so dicts render as literal `{'value': '...'}`). Buttons show choice text, not numbers (post-June 2026 gateway). 10-min silence sentinel. Gateway restart required after patching. Load before the first `clarify` call of a session.
- `references/three-angle-scan.md` — the 3-angle discovery protocol (name + content + relationship) for any "audit / cleanup / remove X" request with emphatic-scope words ("all", "entirely", "no link to it either way"). Use when a single-angle `find`/`grep` is likely to miss cron job names, hub lock entries, log files, or references in skill bodies. Worked example: the 2026-06-07 iAgent removal where angle 1 returned 4 files and the full 3-angle scan returned 15.
- `references/skill-audit.md` — security & hygiene audit pattern for `~/.hermes/skills/`. Read `scan_verdict` from `.hub/lock.json` (not vibes), tier findings as dangerous → wrong-platform → never-used → stale, use the pre-built `quarantine/` slot. Use when Thomas says "remove risky skills", "audit skills", "clean up skills", or asks about a hub-installed skill that might be dangerous.
- `scripts/audit_reminder_cron.py` (lives under `voice-to-obsidian/scripts/`) — detects voice-reminder cron crutches that violate the `voice-to-obsidian` auto-save contract. Substring + scheduled-time heuristics; exit 0 clean, exit 1 crutches found. **Verified 2026-06-08:** caught a `Voice Note Reminder` job (`05ffc0b2d35e`) firing daily at 18:00 that the working hook was already handling. Wire into nightly audit or run ad-hoc.
- `scripts/diagnose_watchdog.py` — one-shot diagnostic for any cron-watched pipeline. Compares newest source-file mtime against newest state-entry mtime, reports the gap, and (with `--watcher-script` + `--skill-md`) flags extension-pattern drift between the doc and the code. Exit codes: 0=healthy, 1=stale state, 2=drift, 3=both. Use this before reading the reference file when you need a fast yes/no.

## Report Format (Thomas's preference)

After a sweep, report in this shape — direct, ranked, no hype:

```
HEALTH — <GREEN|YELLOW|RED>
<one-line summary>

REAL FINDINGS (ranked by leverage)
1. <finding> — <one-line action>
2. ...

RECOMMENDED ORDER
A) <cheapest win>
B) <next>
...

Want me to run A + B? (or A only, or all)
```

Thomas will say "yes" / "all" / "A only" — be ready to execute. Don't ask clarifying questions for low-stakes cleanups.

## Pitfalls

- **Don't disable toolsets that are missing API keys** — user may be planning to fill them. Disable only those with NO working backend (no key, no system tool, no platform token).
- **Don't "fix" image_gen's "system dependency not met"** if Pollinations is the configured provider and the key is in `.env`. It's noise.
- **Don't restart the gateway for skill-only changes** — skills only need `/reset` in chat. Config and toolset changes need the systemd restart.
- **Don't act on a single Telegram DNS retry** — it's a known intermittent (Telegram polling hits fallback IPs). Wait for 3+ within 5 min before flagging.
- **Don't run `git pull` on a diverged fork** without checking `git status` first — if there are uncommitted + untracked files, you'll either lose work or get a conflict. Use the stash → pull → pop sequence in `references/git-pull-recovery.md`.
- **Don't use `terminal()` to interpolate a secret token into a config file** — shell variable expansion (`$(gh auth token)`, `$(cat ~/.secret)`) gets mangled or exposes the token in process listings. Use `execute_code` with `subprocess.run([...])` to read the value and `Path.write_text()` to write the config. Failed concretely when adding `GITHUB_TOKEN` to a systemd drop-in via `printf >> file << EOF` — the `$(gh auth token)` was either empty or the whole heredoc broke.
- **Don't run `rtk init -g`** for Hermes — wrong system. Hermes uses bash aliases, not Claude Code hooks.
- **Don't recommend `hermes setup` for missing keys** unless the user wants to fill them now. It's an interactive wizard — disruptive in a fast session.
- **Don't trust `last_status: ok` as proof a pipeline is working** — the cron layer can be perfectly fine while the script is silently misconfigured (Sandy wrapper pointing at wrong path, watcher globs not matching new writer format, paused job resumed without backfill). Cross-check: newest entry in the watcher's state file should be ≥ newest file mtime in its source dir. If not, the pipeline is silently broken — see `references/cron-silent-failure.md`.
- **Don't trust a skill's "supported formats" table blindly** — the writer's actual output is the truth. The skill doc lags. Always `ls -lt` the source dir and check extensions against the watcher's glob patterns before concluding the watcher is broken.
- **Don't write shell-hook scripts that read event-payload fields at the top level** — the bridge's `json.dumps(..., default=str)` stringifies nested dataclass objects to their repr, so `event_data.get("media_urls")` always returns `None` even though the field exists deep in `extra.event`. The script's "nothing to do" branch exits 0 cleanly and you get a silent no-op. **Make shell hooks event-agnostic: scan filesystem state for new files (audio_cache, log dirs, etc.) and idempotently process them. See `references/shell-hook-silent-failure.md`.**
- **Don't edit the gateway restart verb from memory** — `force-restart` is NOT a valid `systemctl` verb. Use `systemctl --user restart hermes-gateway` and confirm `Active: active (running)` after. Previous "force-restart" claim in memory was wrong; the actual hang was a stuck subprocess on a different day.

## Verification

A clean housekeeping pass ends with:
- `hermes doctor` shows ≤ 1 issue, and that issue is a missing key (user decision) or a vulns in a disabled toolset
- All cron jobs `last_status` = ok
- For each cron with a state file: state file's newest entry ≥ newest mtime in the source dir
- Gateway active, recently restarted if config changed
- Tool list is lean (≤ 20 enabled on cli platform)
