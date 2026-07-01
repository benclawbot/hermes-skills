"""Initialize a swarm scratchpad.

A scratchpad is a JSON file at ``~/.hermes/swarms/<name>.json`` that
multiple agents write to and one aggregator agent reads from.
Provenance fields (created_at, agents) make it debuggable later.
"""
from __future__ import annotations

import argparse
import json
import re
import time
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


def init_scratchpad(
    swarm_name: str,
    agents: list[str],
    base_dir: Path | None = None,
) -> Path:
    _validate_swarm_name(swarm_name)
    base = base_dir or Path(get_hermes_home()) / "swarms"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{swarm_name}.json"
    if not path.exists():
        path.write_text(json.dumps({
            "swarm": swarm_name,
            "created_at": time.time(),
            "agents": agents,
            "entries": {},
        }, indent=2))
    return path


def main():
    p = argparse.ArgumentParser(description="Initialize a swarm scratchpad.")
    p.add_argument("swarm_name")
    p.add_argument("--agents", nargs="+", required=True,
                   help="Agent (job) names that will write to this scratchpad.")
    p.add_argument("--base-dir", type=Path, default=None)
    args = p.parse_args()
    path = init_scratchpad(args.swarm_name, args.agents, args.base_dir)
    print(f"Initialized: {path}")


if __name__ == "__main__":
    main()