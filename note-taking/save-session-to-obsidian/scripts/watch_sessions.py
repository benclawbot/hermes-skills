#!/usr/bin/env python3
"""
Watchdog: monitors ~/.hermes/sessions/saved/ for new Hermes session files.
On new files, generates and writes a summary to Obsidian.
Maintains state in ~/.hermes/sessions/.session_watchdog_state to avoid re-processing.
Designed to run as a no_agent=true cron job — stdout is the delivery mechanism.
"""

import json
import os
import sys
import fcntl
import time
from datetime import datetime
from pathlib import Path

VAULT_BASE = Path(os.environ.get("OBSIDIAN_VAULT_PATH", Path.home() / "Dropbox/memory/Obsidian"))
SESSIONS_DIR = Path.home() / ".hermes/sessions"
STATE_FILE = Path.home() / ".hermes/sessions/.session_watchdog_state"
CONV_DIR = VAULT_BASE / "Conversations"
README_PATH = CONV_DIR / "README.md"


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return set(data)
    return set()


def save_state(processed):
    with open(STATE_FILE, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(sorted(processed), f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def find_new_sessions(processed):
    """Return list of unprocessed session files, newest first.

    Covers both container formats:
    - JSON arrays: hermes_conversation_*.json (Telegram),
                   session_*.json, session_bg_*.json, session_cron_*.json (CLI)
    - JSON Lines:  YYYYMMDD_HHMMSS_<hex>.jsonl (CLI default writer)

    The .jsonl pattern has no prefix; it's matched by the date_stamp_hash shape
    alone. Discovered 2026-06-07 when sessions were silently falling through
    the pipeline (the SKILL.md documented "4 formats" but never listed .jsonl).

    Defensive: also emits a warning when OTHER session-shaped files exist
    in the dir that don't match any known pattern, so format changes don't
    silently drop sessions again.
    """
    saved_dir = SESSIONS_DIR / "saved"
    matched = sorted(
        list(saved_dir.glob("hermes_conversation_*.json")) +
        list(SESSIONS_DIR.glob("session_*.json")) +
        list(SESSIONS_DIR.glob("session_bg_*.json")) +
        list(SESSIONS_DIR.glob("[0-9]*_[0-9]*_*.jsonl")),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    matched_names = {f.name for f in matched}

    # Defensive scan: anything in sessions/ that looks like a session
    # file but doesn't match a known pattern → warn so format changes
    # don't silently drop conversations again.
    try:
        known_patterns = (
            "hermes_conversation_", "session_", "session_bg_",
            ".jsonl",  # all .jsonl files we want, even if name-shape is novel
        )
        noise = ("sessions.json", "request_dump_", ".jsonl.gz", ".tmp")
        for f in SESSIONS_DIR.iterdir():
            if not f.is_file():
                continue
            n = f.name
            if n in matched_names or any(n.startswith(p) for p in noise):
                continue
            if any(p in n for p in known_patterns) or n.endswith(".json"):
                # ends in .json but no known prefix — possible new format
                if n.endswith(".json") and not n.startswith(("hermes_", "session_", "request_")):
                    print(f"UNMATCHED_SESSION_FORMAT: {n} (consider adding to watchdog patterns)", file=sys.stderr)
    except OSError:
        pass

    # Coverage check: if the newest on-disk session file is NEWER than
    # the newest state entry, sessions are piling up unprocessed.
    # This catches the "pipeline silently broke because glob didn't
    # match" failure mode (e.g. May 2026: writer switched to .jsonl
    # but watchdog globs only listed .json). State-based dedup looks
    # healthy from the outside, but real sessions are being dropped.
    try:
        newest_session_mtime = max(
            (f.stat().st_mtime for f in SESSIONS_DIR.iterdir()
             if f.is_file() and f.suffix in (".json", ".jsonl") and not f.name.startswith("sessions.")),
            default=0.0,
        )
        # Convert state entries (filenames) to mtimes
        state_files = json.loads(STATE_FILE.read_text() or "[]")
        newest_state_mtime = 0.0
        for name in state_files:
            if name.startswith("db:"):
                continue
            p = SESSIONS_DIR / name
            if p.exists():
                newest_state_mtime = max(newest_state_mtime, p.stat().st_mtime)
        if newest_session_mtime and newest_state_mtime:
            gap = newest_session_mtime - newest_state_mtime
            if gap > 86400:  # 24h of unprocessed sessions
                print(
                    f"STALE_STATE_WARNING: newest session is {int(gap/3600)}h newer than newest "
                    f"processed state entry. Check glob patterns — pipeline may be silently "
                    f"dropping sessions.",
                    file=sys.stderr,
                )
    except (OSError, ValueError, json.JSONDecodeError):
        pass

    return [f for f in matched if f.name not in processed]


def parse_session(filepath):
    """Dispatch on extension: .jsonl = line-delimited, .json = single object."""
    if filepath.suffix == ".jsonl":
        return _parse_jsonl_session(filepath)
    return _parse_json_session(filepath)


def _parse_json_session(filepath):
    with open(filepath) as f:
        data = json.load(f)
    messages = []
    for msg in data.get("messages", []):
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append((role, content))
    return messages


def _parse_jsonl_session(filepath):
    """JSONL: one JSON object per line, accumulate role/content pairs.

    Skips malformed lines silently (partial writes from Ctrl+C etc.).
    The first line of a Hermes JSONL is `role: "session_meta"` and is filtered
    out by the role check.
    """
    messages = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = obj.get("role", "")
            content = obj.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append((role, content))
    return messages


def truncate(content, max_chars=700):
    if len(content) <= max_chars:
        return content
    return content[:max_chars].rsplit(" ", 1)[0] + "…"


def get_source_from_session(filepath):
    """Detect session source from filename."""
    name = filepath.name
    if name.startswith("hermes_conversation_"):
        return "telegram"
    return "cli"

def generate_summary(messages, source="telegram"):
    if not messages:
        return None
    icon = "📱" if source == "telegram" else "💻"
    topic = truncate(messages[0][1], 100)
    lines = [f"## Topic [{icon} {source.upper()}]\n{topic}"]

    sampled = []
    if len(messages) >= 2:
        sampled.append(f"- You: {truncate(messages[0][1], 200)}")
        sampled.append(f"- Assistant: {truncate(messages[1][1], 200)}")
    if len(messages) > 4:
        sampled.append(f"- … Assistant: {truncate(messages[len(messages)//2][1], 200)}")
    if len(messages) > 2:
        for role, content in reversed(messages):
            if role == "user":
                sampled.append(f"- You (end): {truncate(content, 200)}")
                break

    lines.append("\n## Key exchanges")
    lines.extend(sampled[:6])

    # Detect decision-shaped statements so the daily file's
    # "Decisions today" section is not empty even when the writer
    # never edits it manually. Per vault analysis (theme 07),
    # the only section that MUST be non-empty is decisions —
    # blocks without decisions are the empty-container pattern.
    decisions = detect_decisions(messages)
    if decisions:
        lines.append("\n## Decisions today")
        for d in decisions[:5]:
            lines.append(f"- {d}")

    return "\n".join(lines)


DECISION_PATTERNS = [
    r"\b(i'?ll|let'?s|going to|will|gonna)\b.{0,80}\b(use|switch|adopt|change|fix|build|start|stop|focus|try|move to|drop|enable|disable|set to|set the|make it)\b",
    r"\b(decided|decision|choosing|chose|switched to|moved to|adopted|killed|deprecated|pinned|archived|removed|deleted)\b.{0,80}\b(hermes|skill|repo|project|tool|file|note|tag|path|script|version|format|approach|strategy)\b",
    r"\b(from now on|going forward|new plan|new rule|new approach)\b",
    r"^(?:use|switch to|move to|adopt|enable|disable|delete|remove|archive|fix|build|create|start|stop|set)\b",
]


def detect_decisions(messages):
    """Return a deduplicated list of decision-shaped lines from the session.

    Heuristic: looks for first-person commitments, switch/decide verbs,
    and imperative-style bullets. Caps at 5 to keep the section scannable.
    """
    import re
    found = []
    seen = set()
    patterns = [re.compile(p, re.IGNORECASE) for p in DECISION_PATTERNS]
    for role, content in messages:
        if role != "user":
            continue
        # Split on line boundaries so bulleted decisions count individually
        for line in content.splitlines():
            # Strip leading bullet markers so we don't double-bullet in the output
            cleaned = re.sub(r"^[\s>*\-•·]+", "", line).strip()
            if len(cleaned) < 10 or len(cleaned) > 240:
                continue
            for pat in patterns:
                if pat.search(cleaned):
                    key = cleaned.lower()
                    if key in seen:
                        break
                    seen.add(key)
                    found.append(truncate(cleaned, 180))
                    break
    return found


def get_date_from_session(filepath):
    """Extract date from session filename. Handles all known formats:
    - session_YYYYMMDD_HHMMSS_id.json (CLI JSON)
    - session_bg_HHMMSS_id.json (background JSON)
    - session_cron_JOBID_YYYYMMDD_HHMMSS.json (cron JSON)
    - hermes_conversation_YYYYMMDD_HHMMSS.json (Telegram JSON)
    - YYYYMMDD_HHMMSS_<hex>.jsonl (CLI JSONL — date at start, not after prefix)
    """
    import re
    name = filepath.stem
    # JSONL: date is at the START of the stem, not after a prefix.
    if filepath.suffix == ".jsonl":
        m = re.match(r"^(\d{8})", name)
    else:
        # JSON formats: date is anywhere, but typically after the prefix.
        m = re.search(r"(\d{8})", name)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d")
        except ValueError:
            pass
    # Fallback: mtime
    return datetime.fromtimestamp(filepath.stat().st_mtime)


def write_to_obsidian(date, summary_text, session_file=None):
    year = date.strftime("%Y")
    month = date.strftime("%Y-%m")
    day = date.strftime("%Y-%m-%d")
    month_dir = CONV_DIR / year / month
    month_dir.mkdir(parents=True, exist_ok=True)
    filepath = month_dir / f"{day}.md"

    session_marker = ""
    if session_file:
        source = get_source_from_session(session_file)
        icon = "📱" if source == "telegram" else "💻"
        import re
        name = session_file.stem
        # JSON formats: time at end after date prefix.
        #   session_YYYYMMDD_HHMMSS_id / hermes_conversation_YYYYMMDD_HHMMSS
        # JSONL: time is in the middle (YYYYMMDD_HHMMSS_hash), so we need the
        # SECOND 6-digit group, not the first.
        if session_file.suffix == ".jsonl":
            times = re.findall(r"(\d{6})", name)
            t = times[1] if len(times) >= 2 else (times[0] if times else None)
        else:
            t = re.search(r"_(\d{2})(\d{2})(\d{2})(?:_\w+)?$", name)
            if t:
                t = t.group(0).lstrip("_")[:6]
        if t and len(t) == 6:
            hh, mm = t[:2], t[2:4]
            session_marker = f"\n\n---\n### Session {hh}:{mm} [{icon} {source.upper()}]\n"

    content = f"{session_marker}{summary_text}\n"

    if filepath.exists():
        with open(filepath, "a") as f:
            f.write(content)
    else:
        with open(filepath, "w") as f:
            f.write(f"# Conversation — {day}\n{content}\n\n---\n## Decisions today\n_(Auto-detected from this day's sessions. Edit to keep only what was actually decided.)_\n")

    return filepath


def update_readme(date):
    day = date.strftime("%Y-%m-%d")
    year = date.strftime("%Y")
    month = date.strftime("%Y-%m")
    link = f"- [[Conversations/{year}/{month}/{day}|{day}]]"

    if not README_PATH.exists():
        return

    with open(README_PATH) as f:
        readme = f.read()

    if day in readme:
        return

    lines = readme.split("\n")
    new_lines = []
    inserted = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        if f"### {year}" in line and not inserted:
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("### 20"):
                    new_lines.insert(j, link)
                    inserted = True
                    break
            if not inserted:
                new_lines.append(link)
                inserted = True

    if not inserted:
        new_lines.append(link)

    with open(README_PATH, "w") as f:
        f.write("\n".join(new_lines))


def is_json_valid(filepath):
    """Check if a file contains valid, complete data. Format-aware."""
    try:
        if filepath.suffix == ".jsonl":
            # JSONL: at least one non-empty line that parses as a JSON object
            # with role+content. Just verify first non-empty line parses.
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    json.loads(line)
                    return True
            return False  # empty file
        with open(filepath) as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False

def process_session(filepath, processed_state=None):
    # Skip incomplete/corrupt files (e.g. Ctrl+C mid-write)
    if not is_json_valid(filepath):
        print(f"SKIP (incomplete/corrupt): {filepath.name}", file=sys.stderr)
        # Record in state so we don't re-check every tick
        if processed_state is not None:
            processed_state.add(filepath.name)
        return None
    messages = parse_session(filepath)
    if not messages:
        return None
    source = get_source_from_session(filepath)
    date = get_date_from_session(filepath)
    summary_text = generate_summary(messages, source)
    filepath_written = write_to_obsidian(date, summary_text, filepath)
    update_readme(date)
    return str(filepath_written)


def main():
    state = load_state()
    new_sessions = find_new_sessions(state)

    if not new_sessions:
        print("NO_NEW_SESSIONS")
        return

    written = []
    for session_file in new_sessions:
        try:
            result = process_session(session_file, state)
            if result:
                state.add(session_file.name)
                written.append(result)
        except Exception as e:
            print(f"ERROR processing {session_file.name}: {e}", file=sys.stderr)

    save_state(state)

    if written:
        print(f"PROCESSED:{len(written)}")
        for w in written:
            print(w)
    else:
        print("NO_NEW_SESSIONS")


if __name__ == "__main__":
    main()
