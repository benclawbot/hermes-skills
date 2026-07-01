"""Write an entry to a swarm scratchpad (specialist side).

Kept separate from swarm_read.py so each specialist agent only needs the
write tool loaded — read is the aggregator's job. Atomic temp-file-rename
so concurrent specialists don't corrupt the scratchpad.
"""
from __future__ import annotations

import argparse
import json
import os
import fcntl
import re
import tempfile
import threading
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


# Intra-process lock registry keyed by scratchpad path. flock(2) locks the
# *open file description* on Linux, so multiple open() calls in the same
# process each get their own lock and do not serialize. A per-path
# threading.Lock is the correct primitive for same-process concurrency;
# flock below still serializes cross-process writers via the inode.
_INTRAPROC_LOCKS: dict[str, threading.Lock] = {}
_INTRAPROC_LOCKS_GUARD = threading.Lock()


def _get_intraproc_lock(path: Path) -> threading.Lock:
    key = str(path)
    with _INTRAPROC_LOCKS_GUARD:
        lock = _INTRAPROC_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _INTRAPROC_LOCKS[key] = lock
        return lock


def write_entry(
    swarm_name: str,
    agent: str,
    payload: dict,
    base_dir: Path | None = None,
) -> None:
    """Atomic append of an agent's entry to the scratchpad.

    Concurrency model:
      * Intra-process (threads, asyncio tasks): serialized by a per-path
        threading.Lock so distinct-key writes don't clobber each other in
        the read-modify-write window.
      * Inter-process: short-held fcntl.flock on the inode (best-effort;
        the atomic temp+rename write is the cross-process corruption
        guard).
    """
    _validate_swarm_name(swarm_name)
    base = base_dir or Path(get_hermes_home()) / "swarms"
    path = base / f"{swarm_name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Scratchpad {path} not initialized. Run swarm_init first."
        )
    intraproc = _get_intraproc_lock(path)
    with intraproc:
        with open(path, "r+") as fp:
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
            try:
                data = json.loads(fp.read())
                data["entries"][agent] = {
                    "ts": time.time(),
                    "payload": payload,
                }
                fd, tmp = tempfile.mkstemp(
                    dir=str(base), prefix=".swarm.", suffix=".tmp"
                )
                try:
                    with os.fdopen(fd, "w") as f:
                        json.dump(data, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(tmp, path)
                except Exception:
                    try:
                        os.unlink(tmp)
                    except OSError:
                        pass
                    raise
            finally:
                fcntl.flock(fp.fileno(), fcntl.LOCK_UN)


def main():
    p = argparse.ArgumentParser(description="Write an entry to a swarm scratchpad.")
    p.add_argument("swarm_name")
    p.add_argument("agent")
    p.add_argument("--payload-json", required=True,
                   help="JSON string to store as the entry payload.")
    p.add_argument("--base-dir", type=Path, default=None)
    args = p.parse_args()
    payload = json.loads(args.payload_json)
    write_entry(args.swarm_name, args.agent, payload, args.base_dir)
    print(f"Wrote entry for {args.agent} to {args.swarm_name}")


if __name__ == "__main__":
    main()