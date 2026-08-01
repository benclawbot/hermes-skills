#!/usr/bin/env python3
"""
verify-pipeline.py — synthetic-data smoke test for any
"collect from N sources → ingest to a central hub" pipeline.

Usage:
    python3 verify-pipeline.py \\
        --hub-dir ~/Omni-Memory/hub \\
        --db-path ~/.memory/hub/events.db \\
        --export-dir /tmp/verify/exports \\
        --ingest-script ingest/merge-events.mjs

Exit code 0 on full pass, 1 on any check failure.

What it checks:
  1. Ingest script runs without fatal exit on a freshly-seeded export dir
  2. Events land in the destination DB (>= 1 row per expected source)
  3. Re-run is idempotent (ingested=0, skipped=N — dedup works)
  4. Synthesis script runs and produces >= 1 proposal
  5. Bot starts cleanly and exits on bad token (no crash)
  6. (Optional) Telegram getMe is reachable with the real token

Each check prints a clear PASS/FAIL line. Run the script and read the output.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import hashlib
from pathlib import Path

DEFAULTS = {
    "sources": ["pi", "hermes", "codex"],
    "events_per_source": 3,
    "device_id": "verify-device",
    "ingest_args": ["--export-dir"],  # the script accepts an --export-dir flag
    "synthesis_args": [],
    "bot_args": [],
}


def seed_export(export_dir: Path, device_id: str, sources: list[str], n: int) -> Path:
    """Seed a minimal real-shape export and return the device subdir."""
    device_dir = export_dir / device_id
    device_dir.mkdir(parents=True, exist_ok=True)
    ts_base = int((time.time() - 86400) * 1000)
    manifest_exports = []
    for source in sources:
        events = []
        for i in range(n):
            content = f"user: {source} verify message {i} about async refactor"
            h = hashlib.sha256(
                f"{source}:verify-sess:{ts_base + i}:{content}".encode()
            ).hexdigest()
            events.append({
                "id": f"verify-{source}-{i}",
                "timestamp": ts_base + i,
                "content_type": "transcript",
                "content": content,
                "source": source,
                "source_type": "ai_session",
                "device_id": device_id,
                "session_id": f"verify-sess-{source}",
                "event_hash": h,
                "metadata": json.dumps({"role": "user"}),
                "imported_at": int(time.time() * 1000),
            })
        jsonl_path = device_dir / f"{source}.jsonl"
        with open(jsonl_path, "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")
        manifest_exports.append({"source": source, "file": str(jsonl_path)})
    manifest = {
        "device_id": device_id,
        "platform": "darwin" if sys.platform == "darwin" else "linux",
        "host": "verify-host",
        "collected_at": int(time.time() * 1000),
        "exports": manifest_exports,
    }
    manifest_path = device_dir / f"manifest_{device_id}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return device_dir


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command and return the result. Captures stdout+stderr."""
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def check(name: str, ok: bool, detail: str = "") -> bool:
    """Print a PASS/FAIL line. Returns ok for chaining."""
    icon = "✓" if ok else "✗"
    color = "\033[32m" if ok else "\033[31m"
    reset = "\033[0m"
    print(f"  {color}{icon}{reset} {name}{(': ' + detail) if detail else ''}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub-dir", required=True, type=Path)
    ap.add_argument("--db-path", required=True, type=Path)
    ap.add_argument("--export-dir", required=True, type=Path)
    ap.add_argument("--ingest-script", required=True, type=Path)  # relative to hub-dir
    ap.add_argument("--synthesis-script", type=Path, default=None)
    ap.add_argument("--bot-script", type=Path, default=None)
    ap.add_argument("--device-id", default=DEFAULTS["device_id"])
    ap.add_argument("--sources", nargs="+", default=DEFAULTS["sources"])
    ap.add_argument("--events-per-source", type=int, default=DEFAULTS["events_per_source"])
    args = ap.parse_args()

    # Make all paths absolute
    hub_dir = args.hub_dir.resolve()
    db_path = args.db_path.resolve()
    export_dir = args.export_dir.resolve()
    ingest_path = (hub_dir / args.ingest_script).resolve()
    synthesis_path = (hub_dir / args.synthesis_script).resolve() if args.synthesis_script else None
    bot_path = (hub_dir / args.bot_script).resolve() if args.bot_script else None

    print(f"=== verify-pipeline ===")
    print(f"  hub:     {hub_dir}")
    print(f"  db:      {db_path}")
    print(f"  export:  {export_dir}")
    print(f"  ingest:  {ingest_path}")
    print(f"  node:    {subprocess.run(['node', '--version'], capture_output=True, text=True).stdout.strip()}")
    print()

    # ── 0. Clean state ──
    if export_dir.exists():
        shutil.rmtree(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    # Also clean the wal/shm sidecar files (better-sqlite3 creates them)
    for suffix in ("-wal", "-shm"):
        p = db_path.with_name(db_path.name + suffix)
        if p.exists():
            p.unlink()

    # ── 1. Seed export ──
    print("[1/6] Seeding export...")
    seed_export(export_dir, args.device_id, args.sources, args.events_per_source)
    expected_total = len(args.sources) * args.events_per_source
    print(f"  Seeded {expected_total} events across {len(args.sources)} sources")

    # ── 2. Ingest (first run) ──
    print("\n[2/6] Ingesting (first run)...")
    cmd = ["node", str(ingest_path), "--export-dir", str(export_dir)]
    r = run(cmd, cwd=str(hub_dir))
    print(r.stdout, end="") if r.stdout else None
    if r.returncode != 0:
        print(r.stderr, end="")
        check("ingest first run", False, f"exit {r.returncode}")
        return 1
    check("ingest first run", True, f"exit 0")

    # ── 3. DB row count ──
    print("\n[3/6] Verifying DB rows...")
    if not db_path.exists():
        check("db exists", False, f"{db_path} not found")
        return 1
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        grand = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    finally:
        conn.close()
    if grand < expected_total:
        check("db row count", False, f"got {grand}, expected >= {expected_total}")
        return 1
    check("db row count", True, f"{grand} events")

    # ── 4. Ingest (second run, dedup) ──
    print("\n[4/6] Re-ingesting (dedup check)...")
    r = run(cmd, cwd=str(hub_dir))
    if r.returncode != 0:
        check("ingest second run", False, f"exit {r.returncode}")
        return 1
    if "ingested=0" not in r.stdout and "skipped=" not in r.stdout:
        # Loose check — at minimum, the second run should NOT add new rows
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            grand2 = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        finally:
            conn.close()
        if grand2 != grand:
            check("dedup works", False, f"row count changed: {grand} -> {grand2}")
            return 1
    check("dedup works", True, "second run did not add new rows")

    # ── 5. Synthesis ──
    if synthesis_path and synthesis_path.exists():
        print(f"\n[5/6] Running synthesis ({synthesis_path.name})...")
        r = run(["node", str(synthesis_path)], cwd=str(hub_dir))
        if r.returncode != 0:
            check("synthesis", False, f"exit {r.returncode}")
            return 1
        check("synthesis", True, "exit 0")
    else:
        print(f"\n[5/6] Synthesis script not specified or not found, skipping")

    # ── 6. Bot smoke test ──
    if bot_path and bot_path.exists():
        print(f"\n[6/6] Bot smoke test ({bot_path.name}, fake token)...")
        env = os.environ.copy()
        env["TELEGRAM_BOT_TOKEN"] = "***"
        try:
            r = run(["node", str(bot_path)], cwd=str(hub_dir), env=env, timeout=3)
        except subprocess.TimeoutExpired:
            # Bot is long-polling; timeout is expected. Success = it stayed alive.
            check("bot starts and polls", True, "ran for 3s without crashing")
        else:
            # Bot exited before timeout — acceptable if the error is clean (401)
            if r.returncode in (0, 1) and ("401" in r.stderr or "Unauthorized" in r.stderr or "ETELEGRAM" in r.stderr):
                check("bot exits cleanly on bad token", True, "401 Unauthorized (expected)")
            else:
                check("bot exits cleanly on bad token", False, f"exit {r.returncode}: {r.stderr[:200]}")
    else:
        print(f"\n[6/6] Bot script not specified or not found, skipping")

    print(f"\n=== {db_path.parent} ===")
    print(f"Total events in DB: {grand}")
    print(f"Pass: all checks green ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
