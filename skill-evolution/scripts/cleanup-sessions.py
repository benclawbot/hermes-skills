#!/usr/bin/env python3
"""
cleanup-sessions.py — Prune old Hermes session files

Removes:
- request_dump_*.json files older than 48h
- session_*.json files (not .jsonl) older than 7 days
- Empty directories in sessions/

Keeps .jsonl files (they're the actual sessions used by session_search and mining).
"""

import os
import sys
import time
from pathlib import Path

SESSIONS_DIR = Path.home() / ".hermes" / "sessions"

# Thresholds
REQUEST_DUMP_MAX_AGE_HOURS = 48
SESSION_JSON_MAX_AGE_DAYS = 7

def age_hours(path: Path) -> float:
    """Return age of file in hours."""
    return (time.time() - path.stat().st_mtime) / 3600

def age_days(path: Path) -> float:
    """Return age of file in days."""
    return (time.time() - path.stat().st_mtime) / 86400

def cleanup_request_dumps() -> list[str]:
    """Remove request_dump_*.json files older than 48h."""
    removed = []
    for f in SESSIONS_DIR.glob("request_dump_*.json"):
        if age_hours(f) > REQUEST_DUMP_MAX_AGE_HOURS:
            size = f.stat().st_size / 1024
            f.unlink()
            removed.append(f"{f.name} ({size:.0f}KB)")
    return removed

def cleanup_session_jsons() -> list[str]:
    """Remove session_*.json files (not .jsonl) older than 7 days."""
    removed = []
    for f in SESSIONS_DIR.glob("session_*.json"):
        if age_days(f) > SESSION_JSON_MAX_AGE_DAYS:
            size = f.stat().st_size / 1024
            f.unlink()
            removed.append(f"{f.name} ({size:.0f}KB)")
    return removed

def cleanup_empty_dirs() -> list[str]:
    """Remove empty directories."""
    removed = []
    for d in SESSIONS_DIR.iterdir():
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
            removed.append(str(d.name))
    return removed

def get_stats() -> dict:
    """Return current session directory stats."""
    jsonl = list(SESSIONS_DIR.glob("*.jsonl"))
    request_dumps = list(SESSIONS_DIR.glob("request_dump_*.json"))
    session_jsons = list(SESSIONS_DIR.glob("session_*.json"))
    total_size = sum(f.stat().st_size for f in SESSIONS_DIR.iterdir() if f.is_file()) / 1024 / 1024
    return {
        "jsonl_files": len(jsonl),
        "request_dumps": len(request_dumps),
        "session_jsons": len(session_jsons),
        "total_size_mb": round(total_size, 1),
    }

def main():
    stats_before = get_stats()
    total_removed = 0

    req_removed = cleanup_request_dumps()
    json_removed = cleanup_session_jsons()
    dirs_removed = cleanup_empty_dirs()

    total_removed = len(req_removed) + len(json_removed) + len(dirs_removed)

    stats_after = get_stats()

    output_lines = []
    output_lines.append(f"Session cleanup run: {time.strftime('%Y-%m-%d %H:%M')}")
    output_lines.append(f"Stats before: {stats_before['jsonl_files']} sessions, {stats_before['request_dumps']} dumps, {stats_before['session_jsons']} jsons, {stats_before['total_size_mb']}MB")
    output_lines.append(f"Stats after:  {stats_after['jsonl_files']} sessions, {stats_after['request_dumps']} dumps, {stats_after['session_jsons']} jsons, {stats_after['total_size_mb']}MB")

    if req_removed:
        output_lines.append(f"\nRemoved {len(req_removed)} request dumps (>48h old):")
        for r in req_removed[:10]:
            output_lines.append(f"  - {r}")
        if len(req_removed) > 10:
            output_lines.append(f"  ... and {len(req_removed) - 10} more")

    if json_removed:
        output_lines.append(f"\nRemoved {len(json_removed)} session .json files (>7 days old):")
        for r in json_removed[:10]:
            output_lines.append(f"  - {r}")
        if len(json_removed) > 10:
            output_lines.append(f"  ... and {len(json_removed) - 10} more")

    if dirs_removed:
        output_lines.append(f"\nRemoved {len(dirs_removed)} empty directories")

    if total_removed == 0:
        output_lines.append("\nNo files to remove.")
    else:
        output_lines.append(f"\nTotal: {total_removed} files/dirs removed.")

    output = "\n".join(output_lines)

    # Only print if there's actual output (silent when nothing to do)
    if total_removed > 0 or "--verbose" in sys.argv:
        print(output)

    return 0 if total_removed > 0 else 0  # Always exit 0, silent is ok

if __name__ == "__main__":
    sys.exit(main())