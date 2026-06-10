#!/usr/bin/env python3
"""
backup-memories.py — Backup Hermes memory files to timestamped archive.

Backs up ~/.hermes/memories/ (MEMORY.md, USER.md) to:
  ~/.hermes/backups/memories_<YYYYMMDD>_<HHMMSS>.tar.gz

Keeps last 4 backups, removes older ones.
"""

import os
import sys
import tarfile
import time
from pathlib import Path

MEMORIES_DIR = Path.home() / ".hermes" / "memories"
BACKUPS_DIR = Path.home() / ".hermes" / "backups"
MAX_BACKUPS = 4

def create_backup() -> str | None:
    """Create a tar.gz backup of memories directory."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    # Check if memories dir exists and has files
    if not MEMORIES_DIR.exists():
        print("No memories directory found.")
        return None

    files = list(MEMORIES_DIR.iterdir())
    if not files:
        print("No memory files to backup.")
        return None

    # Create backup filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_name = f"memories_{timestamp}.tar.gz"
    backup_path = BACKUPS_DIR / backup_name

    # Create tar.gz
    with tarfile.open(backup_path, "w:gz") as tar:
        for f in files:
            if f.is_file() and not f.name.endswith(".lock"):
                tar.add(f, arcname=f.name)

    size_kb = backup_path.stat().st_size / 1024
    return f"{backup_name} ({size_kb:.0f}KB)"

def prune_old_backups() -> list[str]:
    """Remove backups beyond MAX_BACKUPS, oldest first."""
    if not BACKUPS_DIR.exists():
        return []

    backups = sorted(BACKUPS_DIR.glob("memories_*.tar.gz"), key=lambda p: p.stat().st_mtime)
    removed = []

    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)
        size_kb = oldest.stat().st_size / 1024
        oldest.unlink()
        removed.append(f"{oldest.name} ({size_kb:.0f}KB)")

    return removed

def get_backup_stats() -> dict:
    """Return backup directory stats."""
    if not BACKUPS_DIR.exists():
        return {"count": 0, "total_mb": 0, "newest": None}

    backups = list(BACKUPS_DIR.glob("memories_*.tar.gz"))
    total_size = sum(b.stat().st_size for b in backups) / 1024 / 1024

    return {
        "count": len(backups),
        "total_mb": round(total_size, 2),
        "newest": max(b.stat().st_mtime for b in backups) if backups else None,
    }

def main():
    stats_before = get_backup_stats()

    new_backup = create_backup()
    removed = prune_old_backups()
    stats_after = get_backup_stats()

    output_lines = []
    output_lines.append(f"Memory backup run: {time.strftime('%Y-%m-%d %H:%M')}")
    output_lines.append(f"Backups before: {stats_before['count']}, total {stats_before['total_mb']}MB")

    if new_backup:
        output_lines.append(f"Created: {new_backup}")

    if removed:
        output_lines.append(f"Pruned {len(removed)} old backups:")
        for r in removed:
            output_lines.append(f"  - {r}")

    output_lines.append(f"Backups after: {stats_after['count']}, total {stats_after['total_mb']}MB")

    output = "\n".join(output_lines)

    if "--verbose" in sys.argv or new_backup or removed:
        print(output)

    return 0

if __name__ == "__main__":
    sys.exit(main())