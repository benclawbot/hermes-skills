# Clarify Tool Pitfalls

The `clarify` tool is the agent's structured way to ask the user a
multiple-choice or open-ended question. It looks simple. It isn't.

These are gotchas learned the hard way — load this reference when
you are about to call `clarify` for the first time in a session, or
when a previous `clarify` call produced unexpected output.

## Schema is `List[str]`, not `List[dict]`

**Symptom:** Your options render as literal Python dict reprs in
Telegram:

```
1. {'value': 'Split into two jobs (propose / judge separately)'}
2. {'value': 'Shorten urllib timeouts (30s) and let it fail fast'}
3. {'value': 'Both — split jobs AND shorten timeouts'}
```

**Root cause:** The `clarify` tool's schema declares
`choices: {"type": "array", "items": {"type": "string"}}`. The gateway
at `gateway/platforms/telegram.py` does `str(choice).strip()` on each
item to build button labels. If you pass a dict, you get the dict
repr as the button text.

**Fix — pass plain strings:**

```python
# WRONG — dicts render as literal {'value': '...'}
clarify(question="...", choices=[
    {"value": "Option A"},
    {"value": "Option B"},
])

# RIGHT — strings only
clarify(question="...", choices=["Option A", "Option B"])
```

The user picks by tapping a numbered button (1, 2, 3, …) or the
"Other" button. The gateway's `render_clarify_prompt`
(`telegram.py:2778-2844`) builds the keyboard.

## Buttons show the choice text, not numbers (June 2026+)

Telegram inline-keyboard buttons for `clarify` show the choice text
itself, truncated to 30 chars with a `…` suffix. Long choices fall
back to a numeric label (`1.  choice text…`) so the message body
remains the source of truth.

If you see a "1" / "2" / "3" button layout in older screenshots, the
gateway is running pre-June 2026 hermes-agent. Update
`gateway/platforms/telegram.py` to the version that uses
`_btn_label()` (see commit `b8e15bd81` in the benclawbot fork).

## The 10-minute silence

If the user doesn't respond within ~10 minutes, the gateway
delivers a `[user did not respond within 10m]` sentinel to the
clarify callback. The agent receives that as the response string
and should re-ask or move on. Don't assume the question was lost
in transit.

**Observed response patterns (2026-06-07):** users respond to
`clarify` with ordinals, full sentence answers, or short
phrases — not just button taps. Working variants seen in the
wild:

- "All the Three" (user picked the 3rd option by ordinal)
- "All" / "Both" (user picked the multi-select option)
- "yes" / "sure" / "ok" (user accepted the recommended option)
- A custom "Other" response with a different framing

The 10-minute timer does NOT start over when the user types
something. It's a one-shot window. Plan your question phrasing
so a one-word or one-sentence answer is enough.

**The auto-Other 5th option:** the gateway appends a 5th button
labelled "Other (type your answer)" automatically. You only
pass 3-4 explicit choices. If you pass more, the gateway may
truncate or the keyboard may render weirdly on narrow Telegram
clients. Three explicit choices is the sweet spot for Telegram
button rendering; four is the hard cap.

## When the question never arrives

The gateway log distinguishes:

- `"Gateway intercepted clarify text response"` — user *did* respond
  (tap or text), and the gateway captured it. The question *was*
  sent.
- No log line at all for that clarify_id — the Telegram `sendMessage`
  call may have failed silently, or the adapter never invoked it.
  Check `~/.hermes/logs/gateway.log` for a `Clarify send failed`
  warning.

If the user says "I didn't receive any question," check the log
first. A failed send is more likely than a missing button.

## Gateway restart needed after patching

The `gateway/platforms/telegram.py` changes only take effect after
a gateway restart. Plain `systemctl --user restart hermes-gateway`
can hang (SIGTERM gets blocked by stuck subprocesses — the command
exceeds the 180s `terminal()` timeout and looks dead). Recovery
sequence when that happens:

```bash
# 1. 'restart' hung — wait it out or just move on; it'll finish eventually
# 2. Once it's clear, or if the gateway is in a weird state:
systemctl --user try-restart hermes-gateway    # only restarts if currently active
# 3. Verify
systemctl --user is-active hermes-gateway       # expect: active
```

**Confirmed in practice (2026-06-07):** `systemctl --user force-restart`
is **NOT** a valid verb. `systemctl` returns
`Unknown command verb 'force-restart', did you mean 'try-restart'?`.
The correct alternative is `try-restart`, which only acts if the
service is currently active — safe to use after a hung `restart`.

The canonical restart procedure in the main `hermes-housekeeping`
SKILL.md is `systemctl --user restart hermes-gateway` followed by
`sleep 3 && systemctl --user is-active hermes-gateway`. If that
first command hangs, don't kill it — let it complete in the
background and verify with `is-active`, or use `try-restart` to
force a clean restart.

## Your patch may have been refactored out from under you

A subtler failure mode observed in 2026-06-07: you patch
`gateway/platforms/telegram.py`, restart the gateway, verify the
fix works — but a watchdog or upstream pull later restarts the
gateway *again*, this time loading the source from a different
commit. The watchdog auto-commits (`chore: auto-commit from
watchdog`) can change the file from under you, and so can any
unattended `git pull` on the hermes-agent checkout.

**Detection:** if your fix is suddenly gone after a gateway
restart that you didn't initiate, check:

```bash
cd ~/.hermes/hermes-agent
git log --oneline -5 gateway/platforms/telegram.py
git diff HEAD~5 -- gateway/platforms/telegram.py | head -40
```

If the recent commits include any watchdog churn or upstream
merges that touched the clarify section (`send_clarify`,
`render_clarify_prompt`, inline-keyboard code), your patch is
probably stale relative to the current source. Re-apply it
against the new state, or wait for the refactor to settle and
re-test against the new code structure.

**Real incident (2026-06-07):** Patched the clarify button
labels (commit `b8e15bd81` in the local reflog). Force-restarted
the gateway, confirmed the fix worked. Then `git fetch fork`
showed the fork's `main` had been auto-committed to by the
watchdog — and the source no longer contained `send_clarify`
or the inline-keyboard code at all. The fix was "kept" only
in the running process's bytecode; the next restart would
revert it. No commit on the fork to roll back to.

**Mitigation for your own patches:** before pushing a gateway
patch, pause any watchdog cron jobs that touch the hermes-agent
checkout, apply the patch, restart, verify, then resume the
watchdog. Or use a worktree: develop the fix in a separate
branch, merge it onto main only when you're ready, and never
let a watchdog auto-commit on top of your WIP.
