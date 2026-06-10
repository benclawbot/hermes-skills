#!/usr/bin/env python3
"""
watch-hermes-health.py — Hermes gateway health watchdog

Checks:
1. Gateway process is alive
2. Cron scheduler is running
3. Memory files are readable and valid
4. skill-memory.json is valid JSON
5. Sessions directory is accessible
6. No recent crashes in gateway.log

Delivers only on anomaly — silent when healthy.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

HERMES_DIR = Path.home() / ".hermes"
SESSIONS_DIR = HERMES_DIR / "sessions"
MEMORIES_DIR = HERMES_DIR / "memories"
MEMORY_FILE = HERMES_DIR / ".pi" / "skill-memory.json"
LOG_FILE = HERMES_DIR / "logs" / "gateway.log"

ANOMALIES = []

def check_process(name: str, pattern: str) -> bool:
    """Check if a process matching pattern is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", pattern],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def check_gateway() -> None:
    """Check gateway process is alive."""
    if not check_process("hermes", "hermes_cli.main|hermes-gateway"):
        ANOMALIES.append("Gateway process not running (hermes_cli not found in pgrep)")

def check_cron() -> None:
    """Check cron scheduler is active."""
    if not check_process("cron", "hermes.*cron|cron.*hermes"):
        # Check via systemctl
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "hermes-gateway"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                ANOMALIES.append("Gateway service not active according to systemctl")
        except Exception:
            pass

def check_memories() -> None:
    """Check memory files are readable and valid."""
    for fname in ["MEMORY.md", "USER.md"]:
        fpath = MEMORIES_DIR / fname
        if not fpath.exists():
            ANOMALIES.append(f"Memory file missing: {fname}")
            continue
        try:
            content = fpath.read_text()
            if len(content) > 5000:
                ANOMALIES.append(f"{fname} is unusually large ({len(content)} chars) — may need pruning")
        except Exception as e:
            ANOMALIES.append(f"Cannot read {fname}: {e}")

def check_skill_memory() -> None:
    """Check skill-memory.json is valid JSON."""
    if not MEMORY_FILE.exists():
        ANOMALIES.append("skill-memory.json does not exist")
        return
    try:
        with open(MEMORY_FILE) as f:
            data = json.load(f)
        required_keys = ["lessons", "gaps", "patterns", "evaluations", "sessions", "evolutions"]
        for key in required_keys:
            if key not in data:
                ANOMALIES.append(f"skill-memory.json missing key: {key}")
    except json.JSONDecodeError as e:
        ANOMALIES.append(f"skill-memory.json is invalid JSON: {e}")
    except Exception as e:
        ANOMALIES.append(f"Cannot read skill-memory.json: {e}")

def check_sessions() -> None:
    """Check sessions directory is accessible and active."""
    if not SESSIONS_DIR.exists():
        ANOMALIES.append("Sessions directory does not exist")
        return
    try:
        # Check both .jsonl (transcripts) and .json (current sessions)
        jsonl_files = list(SESSIONS_DIR.glob("*.jsonl"))
        json_files = list(SESSIONS_DIR.glob("session_*.json"))
        all_session_files = jsonl_files + json_files

        if len(all_session_files) == 0:
            ANOMALIES.append("No session files found — session mining may not work")
            return

        # Check for very recent .json files (current sessions being written)
        recent_json = [f for f in json_files if time.time() - f.stat().st_mtime < 3600]
        if len(recent_json) == 0 and len(json_files) > 0:
            ANOMALIES.append("No session .json files in last hour — gateway may not be creating new sessions")
    except Exception as e:
        ANOMALIES.append(f"Cannot access sessions directory: {e}")

def check_gateway_log() -> None:
    """Check gateway log for recent errors."""
    if not LOG_FILE.exists():
        return  # Log may not exist on all systems

    try:
        # Read last 50 lines
        lines = LOG_FILE.read_text().strip().split("\n")
        recent_lines = []
        cutoff = time.time() - 3600  # last hour

        for line in reversed(lines[-50:]):
            # Try to parse timestamp from log line
            try:
                # Format: 2026-05-15 13:33:25,123 INFO ...
                ts_str = line.split(",")[0]
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                if ts.timestamp() > cutoff:
                    recent_lines.append(line)
            except Exception:
                continue

        # Check for ERROR or CRITICAL in recent lines
        errors = [l for l in recent_lines if "ERROR" in l or "CRITICAL" in l or "Exception" in l]
        if errors:
            ANOMALIES.append(f"Gateway log has {len(errors)} error(s) in last hour — first: {errors[0][:150]}")

        # Check for "Cron ticker stopped" without restart
        stopped = [l for l in recent_lines if "Cron ticker stopped" in l]
        if stopped:
            ANOMALIES.append("Cron ticker stopped — cron jobs may not be running")

    except Exception as e:
        ANOMALIES.append(f"Cannot read gateway log: {e}")

def check_disk_space() -> None:
    """Check disk space is not critically low."""
    try:
        result = subprocess.run(
            ["df", "-h", str(HERMES_DIR)],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            # Parse the usage line
            parts = lines[1].split()
            if len(parts) >= 5:
                usage_str = parts[4]  # e.g. "45%"
                if usage_str.endswith("%"):
                    pct = int(usage_str[:-1])
                    if pct > 90:
                        ANOMALIES.append(f"Disk usage at {pct}% — critical")
                    elif pct > 80:
                        ANOMALIES.append(f"Disk usage at {pct}% — getting high")
    except Exception:
        pass

def main():
    check_gateway()
    check_cron()
    check_memories()
    check_skill_memory()
    check_sessions()
    check_gateway_log()
    check_disk_space()

    if ANOMALIES:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        output = [f"[Hermes Health Alert] {timestamp}"]
        output.append(f"Gateway: {'OK' if check_process('hermes', 'hermes-gateway') else 'DOWN'}")
        for a in ANOMALIES:
            output.append(f"  ⚠ {a}")
        print("\n".join(output))
        return 1  # Non-zero = anomaly detected

    # Silent on healthy
    return 0

if __name__ == "__main__":
    sys.exit(main())