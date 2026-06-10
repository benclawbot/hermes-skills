#!/usr/bin/env python3
"""
Save the latest Hermes session transcript to Obsidian as a daily summary.
Reads ~/.hermes/sessions/saved/hermes_conversation_YYYYMMDD_HHMMSS.json,
writes summary to ~/Dropbox/memory/Obsidian/Conversations/YYYY/YYYY-MM/YYYY-MM-DD.md
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

VAULT_BASE = Path(os.environ.get("OBSIDIAN_VAULT_PATH", Path.home() / "Dropbox/memory/Obsidian"))
SESSIONS_DIR = Path.home() / ".hermes/sessions/saved"
CONV_DIR = VAULT_BASE / "Conversations"
README_PATH = CONV_DIR / "README.md"


def find_latest_session():
    """Find the most recent hermes_conversation_YYYYMMDD_HHMMSS.json"""
    files = sorted(SESSIONS_DIR.glob("hermes_conversation_*.json"), reverse=True)
    if not files:
        return None
    return files[0]


def parse_session(filepath):
    """Parse a session JSON and return list of (role, content) tuples."""
    with open(filepath) as f:
        data = json.load(f)

    messages = []
    for msg in data.get("messages", []):
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append((role, content))
    return messages


def truncate(content, max_chars=800):
    """Truncate content to max_chars, breaking at word boundaries."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars].rsplit(" ", 1)[0] + "…"


def format_messages(messages):
    """Format message list as readable exchange text."""
    lines = []
    for i, (role, content) in enumerate(messages):
        prefix = "You" if role == "user" else "Assistant"
        truncated = truncate(content, 600)
        lines.append(f"[{prefix}]: {truncated}")
        if i >= 12:  # Cap at 6 exchanges to keep summary lean
            lines.append("…")
            break
    return "\n\n".join(lines)


def generate_summary(messages):
    """Generate a structured summary from messages."""
    if not messages:
        return None

    # Topic: first user message
    topic = truncate(messages[0][1], 120) if messages else "Session"

    # Key exchanges: sample across the conversation
    lines = ["## Topic\n" + topic, "\n## Key exchanges\n"]

    # Sample: first user, some middle exchanges, last exchange
    if len(messages) >= 2:
        lines.append(f"- You: {truncate(messages[0][1], 200)}")
        lines.append(f"- Assistant: {truncate(messages[1][1], 200)}")

    if len(messages) > 4:
        mid = messages[len(messages) // 2]
        lines.append(f"- … Assistant: {truncate(mid[1], 200)}")

    if len(messages) > 2:
        last_user = None
        for role, content in reversed(messages):
            if role == "user":
                last_user = (role, content)
                break
        if last_user:
            lines.append(f"- You (end): {truncate(last_user[1], 200)}")

    return "\n".join(lines)


def get_date_from_session(filepath):
    """Extract date from session filename: hermes_conversation_YYYYMMDD_HHMMSS.json"""
    name = filepath.stem  # e.g. hermes_conversation_20260505_222311
    date_str = name.replace("hermes_conversation_", "").split("_")[0]
    return datetime.strptime(date_str, "%Y%m%d")


def write_to_obsidian(date, summary_text):
    """Write summary to Obsidian, create month dir if needed."""
    year = date.strftime("%Y")
    month = date.strftime("%Y-%m")
    day = date.strftime("%Y-%m-%d")

    month_dir = CONV_DIR / year / month
    month_dir.mkdir(parents=True, exist_ok=True)

    filepath = month_dir / f"{day}.md"

    content = f"# Conversation — {day}\n\n{summary_text}\n"
    with open(filepath, "w") as f:
        f.write(content)

    print(f"Wrote: {filepath}")
    return filepath


def update_readme(date):
    """Add date entry to Conversations/README.md if missing."""
    day = date.strftime("%Y-%m-%d")
    year = date.strftime("%Y")
    month = date.strftime("%Y-%m")

    if not README_PATH.exists():
        print("README.md not found, skipping update")
        return

    with open(README_PATH) as f:
        readme = f.read()

    link = f"- [[Conversations/{year}/{month}/{day}|{day}]]"

    # Check if already linked
    if day in readme:
        print("Date already in README, skipping update")
        return

    # Find the right section and add it
    section_header = f"### {year}-{month.replace(year+'-', '')}"  # e.g. ### 2026-04
    # Simple approach: find the month section and add after the last entry
    lines = readme.split("\n")
    new_lines = []
    inserted = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        if f"### {year}" in line:
            # Find next section or end
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("### 20") and not inserted:
                    # Insert before next year section
                    new_lines.insert(j, f"- [[Conversations/{year}/{month}/{day}|{day}]]")
                    inserted = True
                    break
            if not inserted and i == len(lines) - 1:
                new_lines.append(f"- [[Conversations/{year}/{month}/{day}|{day}]]")
                inserted = True

    if not inserted:
        new_lines.append(link)

    with open(README_PATH, "w") as f:
        f.write("\n".join(new_lines))

    print(f"Updated: {README_PATH}")


def main():
    session_file = find_latest_session()
    if not session_file:
        print("No session file found in ~/.hermes/sessions/saved/")
        sys.exit(1)

    print(f"Reading: {session_file}")
    messages = parse_session(session_file)
    if not messages:
        print("No messages found in session")
        sys.exit(1)

    date = get_date_from_session(session_file)
    summary_text = generate_summary(messages)

    filepath = write_to_obsidian(date, summary_text)
    update_readme(date)

    print(f"\nDone. Summary saved to:\n  {filepath}")


if __name__ == "__main__":
    main()
