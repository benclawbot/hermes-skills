# Inline-Keyboard Decisions — Full Protocol

Added 2026-06-08 after the weekly digest was reworked to attach
`inline_keyboard` markup to the Telegram message. The 5-stage loop is
now `propose → judge → DECIDE → apply → grade`, with the DECIDE stage
implemented as a Telegram-button poller running on a separate cron.

## Why a separate stage (not a flag on the existing apply cron)

The apply step and the decision step have different concerns:

- **Apply** is "write a file based on a proposal's diff." It needs
  the proposal in `status='merged'` to know what to do, and it's a
  pure file-write.
- **Decide** is "thomas said yes/no from a Telegram button." It
  needs the proposal in `status='pending'` to know what to update,
  and it's a UI ↔ DB bridge (callback_query → SQL UPDATE → message
  edit).

Two crons with two cadences. The apply cron runs daily (cheap, no
LLM). The decide cron runs every minute (cheap, no LLM, just polls
Telegram). They don't share state besides the DB. If the decide
cron goes down, the apply step still works — thomas can fall back
to `approve #N | reject #N` text replies parsed by the next cycle.

## callback_data schema

```
sri:approve:<id>     # marks proposal as 'merged' (apply picks it up)
sri:reject:<id>      # marks proposal as 'rejected' + writes feedback
sri:modify:<id>      # signal intent only; thomas still replies with note
```

Telegram caps `callback_data` at 64 bytes. `sri:approve:999999999`
is ~22 bytes. Plenty of headroom for a future `sri:approve:<id>:<note_hash>`
if you want a one-tap modify-with-preset — don't use it for free-form
text, the 64-byte cap won't fit.

## The poller (handle_decision.py)

```python
def _process_callback(query, token, dry_run):
    # 1. Lazy reload allowed users from env (NOT a module-level cached list)
    if query["from"]["id"] not in _load_allowed_users():
        return answer(token, query["id"], "🚫 not authorized")

    # 2. Parse sri:<action>:<id>
    action, pid = parse(query["data"])

    # 3. DB transition FIRST. Telegram network calls are best-effort.
    if action == "approve":
        updated = _mark_merged(pid)
    elif action == "reject":
        updated = _mark_rejected(pid)
    elif action == "modify":
        return answer(token, query["id"], "✏️ reply with your note")

    # 4. Best-effort: edit the digest message + answer the callback.
    try: _edit_message(token, chat, msg_id, _stamp_decision(text, pid, "✅"))
    except: pass
    try: _answer_callback(token, qid, "✅ approved #57")
    except: pass
```

**The state machine is one-way:** receive callback → DB write →
best-effort Telegram call. NOT the other way around. Reason: a
network failure (404 on stale callback_query_id after a server
restart, rate limit, etc.) must NOT roll back the DB. If thomas
sees the toast fail, the proposal is still in `merged` status and
apply.py will still write the file. The Telegram-side failures
are cosmetic.

## Persistence: data/decision_state.json

The poller must persist:
- `offset`: highest `update_id` seen (so a restart picks up where
  it left off, doesn't replay old updates)
- `handled_ids`: set of already-processed `callback_query.id`s
  (so a restart that resumes from a lower offset doesn't
  double-apply the same tap)

```json
{
  "offset": 12345,
  "handled_ids": ["cb_001", "cb_002", ...]
}
```

Cap `handled_ids` to last 1000 entries (the LRU window of
Telegram-side retention is ~24h anyway; older ids won't be
re-delivered). Gitignored — it's runtime state.

## The Modify button: not a terminal state

`Modify` is the trickiest of the three. Telegram inline keyboards
can only fire fixed `callback_data` strings, not free-form text.
So a Modify tap is *not* "apply this note" — it's "thomas wants to
modify, please wait for the note."

The current protocol:
1. Tap Modify → toast says "✏️ noted — reply with your note for #N
   (e.g. 'modify #N: <your note>')"
2. Proposal stays `status='pending'` (NOT rejected)
3. Thomas replies with text; the next cycle / human handles the
   actual note (the loop's proposer is the natural place to feed
   the note in as a new proposal)
4. If thomas never sends a note, the proposal times out as
   `pending` and shows up in the next digest's button row

**Why not mark it rejected with a placeholder note?** Because the
operator might want to approve or reject the same proposal after
thinking about the modification, and the original proposal should
still be selectable. A "rejected with intent" status would be
hard to recover from.

## Multi-chunk digests: where do the buttons go?

Telegram `sendMessage` returns a single `message_id` for the first
chunk and a chain of follow-ups. The `reply_markup` (inline
keyboard) only attaches to the first chunk by spec. The pending
proposals always appear in the first chunk of the digest (it's
the topmost section), so buttons land with them by construction.
If a future digest reorders the sections, verify with:

```bash
python3 -c "from digest import _build_digest; print(_build_digest()[:500])"
```

…and confirm the first chunk ends with the pending-proposal
section. If it doesn't, the buttons land in the wrong chunk and
thomas taps them on a message that doesn't show the proposal.

## The two apply.py bugs that the e2e test exposed (and fixed)

When wiring the button→apply path end-to-end, two pre-existing
`apply.py` bugs surfaced:

### Bug 1: rollback crash on missing target file

`apply_proposal()` calls `shutil.copy2(backup, target_p)` on apply
failure. If the target file was already missing when the apply
started (e.g. a test fixture's SKILL.md got deleted but the
proposal is still `status='merged'`), the rollback raises
`FileNotFoundError`. **The exception propagates out of `run()` and
kills the whole iterator** — every subsequent `merged` proposal
in the same `apply.py` call is silently skipped.

**Fix:** wrap the rollback in try/except, check `target_p.exists()`
before copying. Now a missing-target apply failure logs
`! target <path> did not exist; nothing to restore` and the
iterator continues to the next proposal.

```python
try:
    if backup.exists():
        if target_p.exists():
            shutil.copy2(backup, target_p)
        else:
            _log(f"    ! target {target_p} did not exist; nothing to restore")
except Exception as e:
    _log(f"    ! rollback failed: {e}")
```

### Bug 2: bare-markdown diffs hit the patch fallback

`_apply_unified_diff()` accepts:
- Unified diffs (`--- a/...`)
- `APPEND:<text>`
- `REPLACE_ALL:<text>`
- `<<<\nOLD\n===\nNEW\n>>>` block format

A bare markdown fragment (e.g. `## Safety — Preventing Credential
Leaks\n...`) hits the last-resort `_apply_patch()` which calls the
`patch` shell command. The `patch` command rejects the input as
malformed (`Only garbage was found in the patch input.`). Failure
is not silent (the apply step logs + writes a `gap` lesson), but
the proposal never applies.

**Fix:** add a heuristic fallback before the `_apply_patch`
fallback — if the diff has no recognized markers and no `---` /
`<<<` on the first line, treat it as `APPEND:`:

```python
if diff.strip() and not any(
    diff.startswith(p) for p in ("--- ", "APPEND:", "REPLACE_ALL:")
) and "<<<" not in diff.splitlines()[0]:
    _log("  diff has no recognized markers; defaulting to APPEND")
    if target.exists():
        with open(target, "a") as f:
            f.write("\n" + diff.lstrip("\n"))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(diff)
    return True
```

The **better long-term fix** is to teach the proposer to emit
`APPEND:` explicitly (option 1 in the SKILL.md pitfall). The
heuristic is robust against any m3 output but it means the loop
isn't carrying its own diff format. Do both: heuristic as a
safety net, prompt as the primary contract.

## Verification recipe (synthetic callback)

```python
import sys, os
sys.path.insert(0, "/home/thomas/Recursive-Self-Improvement/src")
os.environ["TELEGRAM_BOT_TOKEN"] = "fake"
os.environ["TELEGRAM_ALLOWED_USERS"] = str(THOMAS_TELEGRAM_ID)

from handle_decision import _process_callback

fake = {
    "id": "cb_test_001",
    "from": {"id": int(THOMAS_TELEGRAM_ID)},
    "data": "sri:approve:57",
    "message": {"chat": {"id": int(THOMAS_TELEGRAM_ID)}, "message_id": 9999,
                "text": "  #57 skill_patch ... target: /path/to/SKILL.md"},
}
result = _process_callback(fake, "fake", dry_run=False)
# 404 errors on answerCallbackQuery/editMessageText are EXPECTED with fake token
# The DB transition is what you're verifying:
import sqlite3
con = sqlite3.connect("/home/thomas/Recursive-Self-Improvement/data/loop.db")
assert con.execute("SELECT status FROM proposals WHERE id=57").fetchone()[0] == "merged"
assert con.execute("SELECT COUNT(*) FROM thomas_feedback WHERE proposal_id=57").fetchone()[0] >= 1
```

If either assertion fails, the DB write path is broken — fix
`_mark_merged` / `_record_override_feedback` before the cron goes
live.

## Cron prompt rules

- **`sri-decision-handler`** (job id `528939a24ce7`): the LLM
  prompt is a thin wrapper. Invoke `handle_decision.py --once`,
  report exit code + how many callbacks were processed. Deliver
  nothing on empty polls (`[silent]`). Do NOT regenerate the
  digest or re-query the DB beyond what the script reports.

- **`sri-weekly-digest`** (job id `b547febcb362`): the LLM prompt
  invokes `digest.py` and reports the `[digest] Sent N-char
  digest` line. Do NOT process button taps — that's the
  handler's job. Do NOT touch the DB directly. The script is the
  source of truth for the digest's content and format.

If the cron prompts ever drift (LLM starts interpreting the DB
output, regenerating messages, or rolling back DB writes based on
network errors), restore the verbatim instructions from this
file. The "LLM tries to be helpful" failure mode is the most
common cause of digest corruption in this loop.
