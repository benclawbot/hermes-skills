"""Read a swarm scratchpad (aggregator side)."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from hermes_constants import get_hermes_home

SWARM_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def _validate_swarm_name(name: str) -> None:
    if not isinstance(name, str) or not SWARM_NAME_RE.match(name):
        raise ValueError(
            f"Invalid swarm_name {name!r}: must match "
            f"{SWARM_NAME_RE.pattern} (lowercase, digits, hyphens, dots, "
            f"underscores; start with letter/digit; ≤64 chars)."
        )


def read_scratchpad(swarm_name: str, base_dir: Path | None = None) -> dict:
    _validate_swarm_name(swarm_name)
    base = base_dir or Path(get_hermes_home()) / "swarms"
    path = base / f"{swarm_name}.json"
    if not path.exists():
        return {"swarm": swarm_name, "entries": {}, "missing": True}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        # Corrupted scratchpad: don't crash the aggregator. Surface the
        # problem as a missing-style payload so callers can detect+re-init.
        return {"swarm": swarm_name, "entries": {}, "missing": True, "corrupt": True}


def main():
    p = argparse.ArgumentParser(description="Read a swarm scratchpad.")
    p.add_argument("swarm_name")
    p.add_argument("--base-dir", type=Path, default=None)
    args = p.parse_args()
    print(json.dumps(read_scratchpad(args.swarm_name, args.base_dir), indent=2))


if __name__ == "__main__":
    main()