# Apply-and-Reject Handoff — Session Notes (2026-06-07)

The companion to `layered-llm-budget-fix-2026-06-07.md`. The budget
fix is about getting the **propose** call to complete. This file is
about the **operator-side hand-off** that happens after the
propose+judge cycle runs — the part `apply.py` does NOT do
automatically and that bites the first time you try to operate the
loop by hand.

## What `apply.py` does

`apply.py` reads `proposals WHERE status='merged'`, validates the
target path, backs up the existing file, applies the diff, and
records an `applied_outcomes` row. That's it.

It does NOT:

- Set `status='merged'` for you — you must `UPDATE` it manually
  before running apply.
- Create a `thomas_feedback` row when you apply a proposal.
- Handle rejections at all.
- Write a `negative_patterns` row when you reject a proposal.

## The 3-table side effect on rejection

When the operator rejects a proposal (whether the judge also
rejected it or not — i.e. whether `was_overrides_judge` is True or
False), the same action must write to three tables:

```python
# 1. The proposal status flips
UPDATE proposals SET status='rejected' WHERE id=?

# 2. The operator's verdict becomes the calibration signal
INSERT INTO thomas_feedback
  (proposal_id, feedback_at, verdict, note, was_overrides_judge)
VALUES (?, ?, 'reject', '<note>', <was_overrides_judge>)

# 3. The avoid-list grows — this is what stops m3 from proposing
#    the same class of bad idea on the next cycle
INSERT INTO negative_patterns
  (created_at, proposal_id, target_kind, target_path, reason,
   was_overrides_judge)
VALUES (?, ?, ?, ?, '<reason>', <was_overrides_judge>)
```

The `was_overrides_judge` derivation for #2 and #3:

```python
last_judge = last_judge_verdict_for(proposal_id)  # approve|reject|needs_work
was_overrides = (operator_verdict != last_judge)
```

Verified on 2026-06-07 with proposal #3:

- Judge's last call: `needs_work, score=0.45`
- Operator's call: `reject`
- `was_overrides_judge = True` (because `reject != needs_work`)

The next proposer cycle's system prompt will include the
`negative_patterns` row under "Patterns to AVOID" with the
`reason` text inline. That injection is what makes the
avoid-list work.

## The 2-table side effect on approval + apply

When the operator approves a proposal AND it's applied, the
side effect is:

```python
# 1. Proposal status flips
UPDATE proposals SET status='merged', merged_at=? WHERE id=?

# 2. The operator's verdict becomes the calibration signal
INSERT INTO thomas_feedback
  (proposal_id, feedback_at, verdict, note, was_overrides_judge)
VALUES (?, ?, 'approve', '<note>', <was_overrides_judge>)

# apply.py then:
#   3. Backs up the target file
#   4. Writes the new content
#   5. INSERTs an applied_outcomes row (proposal_id, target_path,
#      diff, applied_at) for the grader to read 7+ days later
```

There's no `negative_patterns` row on approval — the avoid-list
grows on rejection only.

The `was_overrides_judge` derivation is the same: compare operator
verdict against the judge's last call.

Verified on 2026-06-07 with proposal #1:

- Judge's last call: `approve, score=0.85`
- Operator's call: `approve`
- `was_overrides_judge = False` (operator agreed with judge)
- Override rate for that proposal: 0 — the operator call matched
  the judge call.

## The `apply.py` diff format gotcha

`_apply_unified_diff()` accepts four formats. **Raw markdown
fragments (no marker) are NOT one of them.** Specifically, a
proposal diff that begins with `## Pitfalls\n...` (a fragment
intended for appending) hits the `_apply_patch` shell-command
fallback, which rejects the input as malformed.

The fix is to set the proposal's `diff` to:

```
APPEND:<the markdown fragment, with leading newlines stripped>
```

Before running `apply.py`. Two options for the loop:

1. Add diff-format instructions to `prompts/proposer.md` so m3
   emits `APPEND:` for additive patches (cheaper, pushes complexity
   into the prompt).
2. Refactor `_apply_unified_diff` to detect "looks like markdown,
   not a diff" and treat it as `APPEND:` automatically (more
   robust against future m3 output shapes).

**Either fix is fine. The unfixable outcome is silent failure** —
apply.py does fail loudly (logs `  ✗ apply failed, restoring
from backup`, writes a `category='gap'` lesson), but you only see
it if you check the apply log. The verification checklist now
includes a pre-apply diff-format check.

## Worked transcript — proposal #1, 2026-06-07

The proposal arrived with this diff:

```
## Pitfalls

- **Premortems are analysis, not implementation.** ...
- When findings suggest code changes, present them as a ...
```

Bare markdown. `apply.py` was run as-is and failed:

```
[apply] 1 merged proposal(s) to apply
  applying #1 (skill_patch) → /home/thomas/.hermes/skills/premortem/SKILL.md
    backup: /home/thomas/self-recursive-improvement/data/backups/20260607_130807_SKILL.md
    ✗ apply failed, restoring from backup
```

The fix: update the proposal's diff to the `APPEND:` form,
re-run apply:

```python
UPDATE proposals
SET diff = 'APPEND:\n## Pitfalls\n\n- **Premortems are...'
WHERE id=1
```

Then `python3 src/apply.py` succeeded:

```
[apply] 1 merged proposal(s) to apply
  applying #1 (skill_patch) → /home/thomas/.hermes/skills/premortem/SKILL.md
    backup: /home/thomas/self-recursive-improvement/data/backups/20260607_130807_SKILL.md
    ✓ applied
[apply] Done. 1 applied.
```

The live `SKILL.md` gained a `## Pitfalls` section at the end,
the original is preserved at
`~/self-recursive-improvement/data/backups/20260607_130807_SKILL.md`,
and the idempotency marker
`DONE_#1__home_thomas_.hermes_skills_premortem_SKILL.md` was
written so re-running apply is a no-op.

## The 4-step operator checklist for any decision

For every proposal the operator wants to act on:

1. **Read the diff.** If it's a `skill_patch` and the diff is bare
   markdown, reformat to `APPEND:` form before flipping status.
2. **Decide the verdict.** `approve` / `reject` / `modify`. If
   `modify`, write a new proposal — don't try to edit the existing
   diff in place.
3. **Record the verdict** in all three (reject) or two (approve)
   tables. Use the `was_overrides_judge` derivation above.
4. **For approvals:** set `status='merged'` BEFORE running
   `apply.py` — apply.py selects on `status='merged'`. After
   apply succeeds, the `applied_outcomes` row is created
   automatically. For rejections: the `negative_patterns` row
   takes effect on the next proposer cycle.

A single helper `db.record_thomas_decision(proposal_id, verdict,
note)` that does steps 3+4 in one transaction is the right
primitive. As of 2026-06-07 it does not exist.

## Worked transcript — proposal #3 (rejection), 2026-06-07

```sql
-- Last judge verdict on #3
SELECT verdict, score FROM judge_verdicts
WHERE proposal_id=3 ORDER BY id DESC LIMIT 1;
-- → needs_work, 0.45

-- Operator: reject. was_overrides_judge = ('reject' != 'needs_work') = True

INSERT INTO thomas_feedback
  (proposal_id, feedback_at, verdict, note, was_overrides_judge)
VALUES (3, <now>, 'reject',
        'Confirmed: single-session evidence does not meet the bar.
         Memory entry would be premature without a 2nd occurrence
         to confirm the pattern.',
        1);

UPDATE proposals SET status='rejected' WHERE id=3;

INSERT INTO negative_patterns
  (created_at, proposal_id, target_kind, target_path, reason,
   was_overrides_judge)
VALUES (<now>, 3, 'memory_add', NULL,
        'thomas rejected: single-session evidence only, no
         recurring pattern (2+ occurrences required)',
        1);
```

After this, the next proposer cycle's system prompt will include:

```
## Patterns to AVOID (from recent thomas rejections)

Thomas has recently rejected the following kinds of proposals. Do NOT
propose changes in the same shape unless you have strong new evidence
that the situation has changed. A 2-line list:

- [override] memory_add (no path): thomas rejected: single-session
  evidence only, no recurring pattern (2+ occurrences required)
```

That's the avoid-list working as designed.
