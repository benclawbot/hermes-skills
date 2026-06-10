#!/usr/bin/env python3
"""
Diagnose a cron-watched pipeline in one shot.

Compares the newest entry in a watcher's state file against the newest
file in the watcher's source directory. If the state is older than the
source, sessions are piling up unprocessed — the pipeline is silently
broken (typically: glob patterns don't match a new file format the
writer started producing).

Also cross-checks the SKILL.md's "supported formats" / "patterns"
table against the actual glob() calls in the watcher script when
both paths are provided. Drift between the two is the most insidious
silent-failure variant.

Usage:
    python3 diagnose_watchdog.py \\
        --source-dir ~/.hermes/sessions \\
        --state-file ~/.hermes/sessions/.session_watchdog_state \\
        --watcher-script ~/.hermes/skills/note-taking/save-session-to-obsidian/scripts/watch_sessions.py \\
        --skill-md ~/.hermes/skills/note-taking/save-session-to-obsidian/SKILL.md

Exit codes:
    0  pipeline healthy
    1  state is stale (state mtime < source mtime beyond threshold)
    2  format-pattern drift detected between SKILL.md and script
    3  both
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Common "looks like a session file" extensions to consider as the source dir's universe
SESSION_EXTS = (".json", ".jsonl")

# Patterns that, if present in the source dir, suggest session-shaped files
NOISE_PREFIXES = ("sessions.", "request_dump_", ".jsonl.gz", ".tmp")


def newest_mtime(directory: Path, exts=SESSION_EXTS):
    """Return the mtime of the newest session-shaped file in `directory`."""
    try:
        return max(
            (f.stat().st_mtime for f in directory.iterdir()
             if f.is_file() and f.suffix in exts and not f.name.startswith(NOISE_PREFIXES)),
            default=0.0,
        )
    except OSError:
        return 0.0


def newest_state_mtime(state_file: Path, source_dir: Path):
    """Resolve the state file's listed filenames back to source-dir mtimes.

    Backfill markers (`db:<id>`) are skipped because they don't correspond
    to a file the watcher would have processed.
    """
    try:
        state = json.loads(state_file.read_text() or "[]")
    except (OSError, json.JSONDecodeError):
        return 0.0
    out = 0.0
    for name in state:
        if name.startswith("db:"):
            continue
        p = source_dir / name
        try:
            if p.exists():
                out = max(out, p.stat().st_mtime)
        except OSError:
            pass
    return out


def check_drift(skill_md: Path, watcher_script: Path):
    """Detect SKILL.md ↔ script glob-pattern drift.

    Extracts file-pattern claims from the SKILL.md (extensions and
    prefixes) and globs from the watcher script, and reports any
    substantial mismatch.
    """
    if not skill_md.exists() or not watcher_script.exists():
        return []
    try:
        md = skill_md.read_text()
    except OSError:
        return []
    try:
        py = watcher_script.read_text()
    except OSError:
        return []
    findings = []
    # Pull all glob() / .suffix == calls from the script
    globs = set(re.findall(r'glob\(["\']([^"\']+)["\']', py))
    suffixes = set(re.findall(r'suffix\s*==\s*["\']([^"\']+)["\']', py))
    # Pull all .ext / .json / .jsonl mentions from the SKILL.md
    md_exts = set(re.findall(r'`\.([a-z]+)`', md))
    md_patterns = set(re.findall(r'`([\w*.?[\]^${}+()|\\-]+\.[\w*]+)`', md))
    if globs and suffixes:
        script_exts = {s.lstrip(".") for s in suffixes}
        md_exts_only = {e for e in md_exts if e in {"json", "jsonl", "yaml", "toml"}}
        if md_exts_only and not md_exts_only.issubset(script_exts | {"json", "yaml", "toml"}):
            findings.append(
                f"SKILL.md mentions extensions {md_exts_only} but the script "
                f"only matches on suffixes {script_exts}. Possibly stale doc."
            )
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source-dir", required=True, type=Path)
    ap.add_argument("--state-file", required=True, type=Path)
    ap.add_argument("--watcher-script", type=Path, help="optional: for drift check")
    ap.add_argument("--skill-md", type=Path, help="optional: for drift check")
    ap.add_argument("--gap-threshold", type=int, default=86400,
                    help="seconds; default 24h. State-vs-source gap above this is a warning.")
    args = ap.parse_args()

    if not args.source_dir.exists():
        print(f"FAIL: source dir {args.source_dir} does not exist", file=sys.stderr)
        return 1
    if not args.state_file.exists():
        print(f"FAIL: state file {args.state_file} does not exist", file=sys.stderr)
        return 1

    newest_src = newest_mtime(args.source_dir)
    newest_st = newest_state_mtime(args.state_file, args.source_dir)
    gap = newest_src - newest_st if newest_src and newest_st else 0

    src_str = datetime.fromtimestamp(newest_src).isoformat() if newest_src else "(none)"
    st_str = datetime.fromtimestamp(newest_st).isoformat() if newest_st else "(none)"

    print(f"newest source file:  {src_str}")
    print(f"newest state entry:  {st_str}")
    print(f"gap:                 {int(gap/3600)}h ({int(gap)}s)")

    rc = 0
    if newest_src and (not newest_st or gap > args.gap_threshold):
        print(f"\nSTALE_STATE_WARNING: source is {int(gap/3600)}h newer than state. "
              f"Pipeline is silently dropping sessions.", file=sys.stderr)
        rc |= 1

    if args.watcher_script and args.skill_md:
        drift = check_drift(args.skill_md, args.watcher_script)
        if drift:
            for finding in drift:
                print(f"DRIFT_WARNING: {finding}", file=sys.stderr)
            rc |= 2

    if rc == 0:
        print("\nPIPELINE HEALTHY")
    return rc


if __name__ == "__main__":
    sys.exit(main())
