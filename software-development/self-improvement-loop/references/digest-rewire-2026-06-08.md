# Digest Rewire — 2026-06-08

The SRI weekly digest in Telegram was a 5127-char hallucination.
Cron agent `b547febcb362` (`sri-weekly-digest`) had a prompt that said
"do NOT regenerate the message yourself — digest.py is the source of
truth," and the agent did exactly that anyway. Symptoms in the user's
Telegram that morning:

- `🕳 gap: apply failed for proposal #4 (skill_patch ...)` repeated 16+ times
- `⚠ Pipeline errors (7d): 34 — propose: 21, judge: 0, apply: 13`
- `⏳ Pending your review (1): #57 ... judge: reject`
- `🪞 Self-incidents (7d): 4`
- `🌿 Branches: 21 active, 18 with applied changes (revertable via apply.py --revert)`

Three categories of wrong:

1. **Stale noise in the diff buffer.** Proposal #4 doesn't exist;
   only #57 was pending. The "caveman test marker" lines came from
   a prior cycle's `skill_patch` diff that had been re-quoted by the
   LLM without re-checking the DB. The LLM was working from cache,
   not from `proposals WHERE status='pending'`.

2. **Counting columns by intuition, not by schema.** The LLM read
   `merged` and reported it as `errors`. "34 applied" was actually
   34 merged proposals, of which **31 were the loop's own test
   fixtures** (`_sri_test_skill_`, `/tmp/sri_*/` paths). Real
   production activity was 3 proposals.

3. **Format drift with no schema.** No two sections had the same
   shape. The LLM was free to invent what "revertable" means, what
   the branch count actually represented, and what "pipeline errors"
   should look like.

## The fix (commit `d7e1e4b`)

`src/digest.py` was rewritten as a 5-section, schema-enforced digest
builder with its own Telegram-send logic. The new sections, in order:

1. **RULES PROPOSED** — pending proposals, awaiting thomas's decision.
2. **RULES REJECTED** — judge-rejected, FYI.
3. **JUDGE-OVERRIDES** — drift signal (thomas disagreed with judge).
4. **CONFIRM NEEDED** — things the system can't decide on its own.
5. **CONTEXT** — pipeline / incidents / branches, FYI only.

Each row carries the proposal id + kind + confidence + target + truncated
rationale. The reply template is one line at the bottom of section 1.

The script reads `data/loop.db` directly via `sqlite3` (not via the
existing `db.py` helpers, which carry schema assumptions that don't
match the v2 column set). It filters sandbox paths with
`SANDBOX_MARKERS = ("_sri_test_skill_", "/tmp/sri_")` so the "real
applied" count is honest. For `memory_add` rows with `target_path IS
NULL`, it falls back to the first 1-3 lines of the `diff` so the
target is human-readable.

## Cron prompt change (after the fix)

`b547febcb362`'s prompt is now a thin wrapper. The agent runs the
script, reads the `[digest] Sent N-char digest to <chat_id]` line,
and forwards that as its 1-line reply. It does **not** read the DB
or synthesize a digest. The script is the source of truth; the
agent is a transport.

```bash
bash -c 'set -a; source ~/.hermes/.env; set +a; python3 src/digest.py'
```

The `set -a; source; set +a` pattern is required (not bare
`source ~/.hermes/.env`) because `~/.hermes/.env` uses bare
`KEY=value`. See `cronjob-ops` → "Subtle gotcha: `source ~/.hermes/.env`
is NOT enough if the file uses bare `KEY=value`."

## Verification

```
[digest] Sent 1332-char digest to 7635598213
```

End-to-end test passed: 1332 chars, sent to thomas's home channel,
exit 0, no regeneration by the LLM cron. Five sections in the
expected order, sandbox filter applied, NULL target paths filled in
from the diff header.

## What to read next time

- The new format + decision-surface philosophy is in the SKILL.md
  body under "Thomas's digest format (consolidated 2026-06-08, …)".
- The "LLM regenerates digest from DB" anti-pattern is in
  `cronjob-ops` → "Companion rule: when the prompt says 'trust the
  script's output', do not regenerate the message from the DB."
- The `set -a; source; set +a` env-export pattern is in `cronjob-ops`
  → "Subtle gotcha: `source ~/.hermes/.env` is NOT enough…"
