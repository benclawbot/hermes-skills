# grades: heuristic reference for grade_outcomes.py
#
# Outcome ladder, cheapest to most expensive:
#
# 1. UNKNOWN — too fresh (< 7 days). Don't grade yet; insufficient time
#    for a re-correction to surface. Default state for new rows.
#
# 2. REVERTED — strongest negative. The current file content matches a
#    backup in data/backups/ with mtime > applied_at. This means someone
#    (human, another apply run, or the apply-failure restore path) put
#    the file back. Cost: 1 stat + 2 reads. Reliable.
#
# 3. RECORRECTED — weak negative. A later applied_outcomes row to the
#    same target_path has a diff that overlaps our diff on at least one
#    12+char line. Means the change went out but had to be patched.
#    Detection: set-intersection on stripped (header-less, +/- stripped)
#    diff lines. Cost: 1 SQL query + set ops. Fuzzy.
#
# 4. RECORRECTED (alt) — also weak negative. A lessons_learned row with
#    category 'correction' or 'gap' was created after applied_at AND
#    references the target_path in its content. Means the same problem
#    resurfaced. Cost: 1 SQL query + LIKE match. Cheap.
#
# 5. NEUTRAL — 7+ days old, no negative signal. Absence of evidence is
#    not proof of help, but it's the best proxy we have. Conservative
#    default; bias toward "we don't know" rather than "this helped."
#
# 6. HELPED — currently UNSETTABLE by the grader. Needs an explicit
#    human mark (e.g. thomas says "this helped" in Telegram) or a real
#    eval harness. Help ratio's denominator is therefore
#    (helped + reverted + recorected) which under-counts positives —
#    this is acceptable. The ratio still detects drift.
#
# 7. HELPER INVARIANTS:
#    - DONE_<id>_<path> markers in data/backups/ are NOT backups; skip
#      them in the revert scan.
#    - Apply's failure-restore path creates a backup-then-copy. If the
#      apply failed AND restored, we still have a backup, but the
#      applied_outcomes row never gets created (record_applied_outcome
#      is only called on success). So this case doesn't reach the
#      grader.
#    - The same file can be applied to multiple times. Iterate by id
#      order so each row only checks "later" rows for the recorrected
#      signal.

def grade_ladder_summary():
    """Return a short summary string for the digest."""
    return (
        "Outcome ladder: unknown (fresh) → reverted | recor | "
        "neutral (7d+ no signal). 'helped' requires explicit mark."
    )
