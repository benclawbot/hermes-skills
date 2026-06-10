#!/usr/bin/env python3
"""Diagnose fork-staleness for a given fork vs upstream.

Detects the pattern documented in references/fork-staleness-watchdog.md:
a fork that is dozens-to-hundreds of commits behind upstream because a
watchdog / cron has been auto-committing to it without `git fetch`ing.

Usage:
    python3 check-fork-staleness.py <fork_owner> <fork_repo> <upstream_owner>/<upstream_repo>
    # e.g. python3 check-fork-staleness.py benclawbot hermes-agent NousResearch/hermes-agent

Exit codes:
    0  — fork is healthy (< 25 commits behind, no auto-commit pollution)
    1  — fork is stale (>= 25 commits behind)
    2  — fork has auto-commit pollution (regardless of staleness)
    3  — fork is stale AND has pollution
    4  — argument error or API call failed
"""
import json
import subprocess
import sys
from typing import Tuple

GH_CLI = "/home/thomas/bin/gh"
STALENESS_THRESHOLD = 25
AUTO_COMMIT_PATTERN = r"(chore: auto-commit|auto-commit from watchdog)"


def gh_api(endpoint: str) -> Tuple[bool, dict | str]:
    """Call gh api <endpoint>, return (ok, parsed_json_or_error_message)."""
    try:
        result = subprocess.run(
            [GH_CLI, "api", endpoint],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return False, result.stderr.strip()
        return True, json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return False, str(e)


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 4

    fork_owner, fork_repo, upstream = sys.argv[1], sys.argv[2], sys.argv[3]
    full_fork = f"{fork_owner}/{fork_repo}"

    print(f"=== Fork staleness diagnostic ===")
    print(f"Fork:     {full_fork}")
    print(f"Upstream: {upstream}")
    print()

    # Q1: Compare fork's main to upstream's main
    ok, compare = gh_api(f"repos/{full_fork}/compare/main...{upstream}:main")
    if not ok:
        print(f"❌ API call failed: {compare}", file=sys.stderr)
        return 4

    ahead = compare.get("ahead_by", "?")
    behind = compare.get("behind_by", "?")
    status = compare.get("status", "?")

    print(f"Q1 — ahead/behind upstream main: {ahead} ahead / {behind} behind (status={status})")

    # Q2 + Q3: List auto-commit pollution
    ok, commits = gh_api(f"repos/{full_fork}/commits?per_page=100")
    if not ok:
        print(f"❌ commits API call failed: {commits}", file=sys.stderr)
        return 4

    import re
    auto_commits = [c for c in commits if re.search(AUTO_COMMIT_PATTERN, c.get("commit", {}).get("message", ""))]
    print(f"Q2 — auto-commit messages in last 100 commits: {len(auto_commits)}")

    # Q4: Are the auto-commits empty?
    empty_auto_commits = 0
    for c in auto_commits[:5]:  # spot-check first 5
        sha = c["sha"]
        ok, detail = gh_api(f"repos/{full_fork}/commits/{sha}")
        if ok and detail.get("files", []):
            # has actual file changes
            pass
        else:
            empty_auto_commits += 1
    print(f"Q4 — empty-diff auto-commits (spot-check of first 5): {empty_auto_commits}/5")

    # Q5: Check the watch_repos.py / similar script for hardcoded PAT (warn only)
    print()
    print("Q5 — manual checks (run separately):")
    print("    grep -E 'ghp_[a-zA-Z0-9]+' /path/to/watchdog.py     # should be 0")
    print("    grep 'git fetch origin' /path/to/watchdog.py        # should be > 0")
    print("    grep 'rev-list --count HEAD..origin' /path/to/watchdog.py  # should be > 0")

    # Verdict
    print()
    stale = isinstance(behind, int) and behind >= STALENESS_THRESHOLD
    polluted = len(auto_commits) > 0

    if stale and polluted:
        print(f"❌ Fork is STALE (>{STALENESS_THRESHOLD} commits behind) AND has auto-commit pollution.")
        print(f"   See references/fork-staleness-watchdog.md for the 3-layer fix.")
        return 3
    if stale:
        print(f"⚠️  Fork is STALE (>{STALENESS_THRESHOLD} commits behind) but no auto-commit pollution detected.")
        return 1
    if polluted:
        print(f"⚠️  Fork has auto-commit pollution but is not yet stale.")
        return 2
    print(f"✅ Fork looks healthy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
