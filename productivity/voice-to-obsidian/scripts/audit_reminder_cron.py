#!/usr/bin/env python3
"""
Audit cron jobs for "voice reminder crutches" that violate the
voice-to-obsidian auto-save contract.

Background: this skill's hard rule is that voice notes are saved
*silently and automatically* by the pre_gateway_dispatch hook. A
daily or hourly reminder cron ("you have voice notes — say 'save'
to transcribe") is a crutch for a broken hook and creates a
double-surface: the hook may be silently working AND the user
gets nagged about already-saved audio. This script scans the
active cron jobs and flags any that look like a voice reminder.

The detection is intentionally simple (substring + scheduled-time
heuristics) rather than perfect — false positives are cheap to
investigate and a missed crutch means the user gets nagged
forever. Run as part of `hermes-housekeeping` audit or directly:

    python3 ~/.hermes/skills/voice-to-obsidian/scripts/audit_reminder_cron.py

Exit codes:
  0 — no crutch detected (clean)
  1 — one or more crutches found (printed to stdout, JSON each)
  2 — config unreadable (likely missing jobs.json)

The script does NOT auto-delete; it surfaces findings and the
operator decides. Pair with the `hermes cron remove <job_id>`
manual step, or wire into `~/.hermes/scripts/nightly-audit.sh`
if you want this on a schedule.
"""
import json
import os
import re
import sys
from pathlib import Path

JOBS_FILE = Path(os.path.expanduser("~/.hermes/cron/jobs.json"))

# Substrings (case-insensitive) that suggest a voice-reminder crutch.
# Match against job name, prompt, and script path. Keep this list tight —
# false positives cost operator attention; missed crutches cost the user
# a nag per day, which is the failure mode we're trying to prevent.
CRUTCH_MARKERS = [
    "voice note reminder",
    "voice-reminder",
    "voice_reminder",
    "save voice notes",
    "save voice note",
    "voice to obsidian",
    "voice-to-obsidian reminder",
    "did you save",
    "transcribe your voice",
    "voice not saved",
    "unprocessed voice",
]

# Substring that *would* match a crutch but is actually a legitimate
# hook-driven job (e.g. the hook script run on schedule, not as a
# reminder). When we see these, we skip the match. Keep this list
# short and conservative.
LEGIT_OVERRIDES = [
    "voice-to-obsidian-hook.py",  # the real hook, run as a job
    "voice-to-obsidian-backfill",  # one-shot recovery script
]


def _load_jobs() -> dict:
    if not JOBS_FILE.exists():
        print(f"# jobs.json not found at {JOBS_FILE}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(JOBS_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"# failed to parse {JOBS_FILE}: {e}", file=sys.stderr)
        sys.exit(2)


def _is_crutch(job: dict) -> tuple[bool, str]:
    """Return (is_crutch, matched_marker). Empty marker = no match."""
    name = (job.get("name") or "").lower()
    prompt = (job.get("prompt") or "").lower()
    script = (job.get("script") or "").lower()
    blob = " ".join([name, prompt, script])

    # Skip if any legit override matches
    for legit in LEGIT_OVERRIDES:
        if legit in blob:
            return False, ""

    for marker in CRUTCH_MARKERS:
        if marker in blob:
            # A crutch that fires more than once per day is worse than
            # a daily nag — the user is on a tight loop. Surface the
            # cadence in the match reason.
            schedule = (job.get("schedule") or {}).get("display", "?")
            return True, f"matched '{marker}' in {name!r} (schedule: {schedule})"
    return False, ""


def main() -> int:
    data = _load_jobs()
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    if not isinstance(jobs, list):
        print("# unexpected jobs.json shape: 'jobs' should be a list", file=sys.stderr)
        sys.exit(2)

    findings = []
    for job in jobs:
        is_match, reason = _is_crutch(job)
        if is_match:
            findings.append({
                "job_id": job.get("id"),
                "name": job.get("name"),
                "schedule": (job.get("schedule") or {}).get("display"),
                "reason": reason,
            })

    if not findings:
        print("# clean: no voice-reminder crutches detected")
        return 0

    print(f"# {len(findings)} crutch job(s) detected:")
    print(json.dumps(findings, indent=2))
    print()
    print("# Recommended next step: hermes cron remove <job_id>")
    print("# (the pre_gateway_dispatch hook should already be saving these)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
