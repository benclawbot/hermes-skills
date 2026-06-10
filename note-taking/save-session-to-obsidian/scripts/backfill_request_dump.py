#!/usr/bin/env python3
"""
Backfill: process a Hermes request_dump_*.json file as a regular session.

These dumps are created when the API call exhausts retries mid-session
(typically Telegram gateway crash). They contain the full request body
(messages array) that was about to be sent, so the conversation is
fully recoverable — just not through the normal session-file pipeline.

Usage:
    python3 backfill_request_dump.py <path-to-request-dump.json>

Writes to the same Obsidian Conversation file structure as the watchdog.
Records the dump in the watchdog state so it isn't double-processed.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

VAULT = Path("/home/thomas/Desktop/Memory")
CONV = VAULT / "Conversations"
STATE_FILE = Path.home() / ".hermes/sessions/.session_watchdog_state"


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f)


def truncate(s, n=700):
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0] + "…"


def extract_content(content):
    """Convert Anthropic-style content blocks (list of dicts) to plain text."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        t = block.get("type")
        if t == "text":
            parts.append(block.get("text", ""))
        elif t == "tool_use":
            inp = block.get("input", {})
            inp_str = json.dumps(inp)[:150]
            parts.append(f"[tool_use: {block.get('name', '?')}({inp_str})]")
        elif t == "tool_result":
            res = str(block.get("content", ""))
            parts.append(f"[tool_result: {res[:200]}]")
    return "\n".join(parts)


def parse_dump(path):
    with open(path) as f:
        dump = json.load(f)
    msgs = []
    for m in dump["request"]["body"]["messages"]:
        role = m.get("role", "")
        content = extract_content(m.get("content", ""))
        if role in ("user", "assistant") and content:
            msgs.append((role, content))
    return msgs, dump


def detect_decisions(messages):
    patterns = [
        r"\b(i'?ll|let'?s|going to|will|gonna)\b.{0,80}\b(use|switch|adopt|change|fix|build|start|stop|focus|try|move to|drop|enable|disable|set to|set the|make it)\b",
        r"\b(decided|decision|choosing|chose|switched to|moved to|adopted|killed|deprecated|pinned|archived|removed|deleted)\b.{0,80}\b(hermes|skill|repo|project|tool|file|note|tag|path|script|version|format|approach|strategy)\b",
        r"\b(from now on|going forward|new plan|new rule|new approach)\b",
        r"^(?:use|switch to|move to|adopt|enable|disable|delete|remove|archive|fix|build|create|start|stop|set)\b",
    ]
    found, seen = [], set()
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    for role, content in messages:
        if role != "user":
            continue
        for line in content.splitlines():
            cleaned = re.sub(r"^[\s>*\-•·]+", "", line).strip()
            if len(cleaned) < 10 or len(cleaned) > 240:
                continue
            for pat in compiled:
                if pat.search(cleaned):
                    if cleaned.lower() in seen:
                        break
                    seen.add(cleaned.lower())
                    found.append(truncate(cleaned, 180))
                    break
    return found


def write_obsidian(date, summary, session_label):
    year, month, day = date.strftime("%Y"), date.strftime("%Y-%m"), date.strftime("%Y-%m-%d")
    target = CONV / year / month / f"{day}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    marker = f"\n\n---\n### Session 19:42 [📱 TELEGRAM] (recovered from request_dump {session_label})\n"
    body = f"{marker}{summary}\n"
    if target.exists():
        with open(target, "a") as f:
            f.write(body)
    else:
        with open(target, "w") as f:
            f.write(f"# Conversation — {day}\n{body}\n\n---\n## Decisions today\n_(Auto-detected from this day's sessions. Edit to keep only what was actually decided.)_\n")
    return target


def summarize(messages):
    if not messages:
        return None
    topic = truncate(messages[0][1], 100)
    lines = [f"## Topic [📱 TELEGRAM]\n{topic}"]
    lines.append("\n## Key exchanges")
    if len(messages) >= 2:
        lines.append(f"- You: {truncate(messages[0][1], 200)}")
        lines.append(f"- Assistant: {truncate(messages[1][1], 200)}")
    if len(messages) > 4:
        lines.append(f"- … Assistant: {truncate(messages[len(messages)//2][1], 200)}")
    for role, content in reversed(messages):
        if role == "user":
            lines.append(f"- You (end): {truncate(content, 200)}")
            break
    decisions = detect_decisions(messages)
    if decisions:
        lines.append("\n## Decisions today")
        for d in decisions[:5]:
            lines.append(f"- {d}")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: backfill_request_dump.py <path>", file=sys.stderr)
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Not found: {path}", file=sys.stderr)
        sys.exit(1)

    messages, dump = parse_dump(path)
    if not messages:
        print("No messages extracted.", file=sys.stderr)
        sys.exit(1)

    # Date priority: session_id embeds the actual session start time
    # (YYYYMMDD_HHMMSS). The dump's own timestamp is when the failure
    # happened (often seconds-to-minutes later, sometimes on a different
    # day if the crash spanned midnight). Always trust the session_id.
    date = None
    sid = dump.get("session_id", "")
    m = re.match(r"^(\d{8})_(\d{6})", sid)
    if m:
        date = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    if not date:
        ts = dump.get("timestamp", "")
        date = datetime.fromisoformat(ts) if ts else datetime.now()

    summary = summarize(messages)
    target = write_obsidian(date, summary, dump.get("session_id", path.stem))
    print(f"Wrote: {target} ({len(messages)} messages)")

    # Mark in state so watchdog doesn't reprocess
    state = load_state()
    state.add(path.name)
    save_state(state)
    print(f"State updated: {path.name}")


if __name__ == "__main__":
    main()
