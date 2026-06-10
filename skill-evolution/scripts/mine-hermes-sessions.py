#!/usr/bin/env python3
"""
mine-hermes-sessions.py — Extract lessons from Hermes session transcripts
and write them to ~/.hermes/.pi/skill-memory.json

Ref: ~/Pi-Agent-Optimus/skills/skill-evolution/scripts/mine-sessions.py
"""

import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Configuration
SESSIONS_DIR = Path.home() / ".hermes" / "sessions"
MEMORY_FILE = Path.home() / ".hermes" / ".pi" / "skill-memory.json"

# Patterns to mine
CORRECTION_PATTERNS = [
    r"\b(actually|no,|wrong|incorrect|not right|stop doing|don't do|"
    r"I said|I meant|that's not|correction|remember that|don't forget)\b",
]
preference_patterns = [
    r"\b(I prefer|I like|I don't like|I want|from now on|always use|"
    r"never use|going forward|keep in mind|make sure to|default to)\b",
]
decision_patterns = [
    r"\b(let's go with|I decided|we're using|the plan is|switch to|"
    r"move to|chosen|picked|decision|we agreed|use this instead)\b",
]
tool_patterns = [
    r"\b(again|every time|keep forgetting|as usual|same as before|"
    r"like last time|we always|the usual|repeated the same)\b",
]
lesson_patterns = [
    r"\b(learned|lesson|figured out|discovered|found that|worked around|"
    r"fixed by|resolved by|took a while to find|turns out)\b",
]
gap_patterns = [
    r"\b(error|failed|crash|crash|exception|traceback|not working|"
    r"doesn't work|stuck|can't find|won't|unable to|broke|broken)\b",
]
approach_patterns = [
    r"\b(delegate then verify|test first|verify before commit|check.*before|"
    r"read.*then do|look before you leap|confirm.*then proceed|"
    r"backup.*before|try.*except|timing issue|race condition|bottleneck)\b",
]
tool_sequence_patterns = [
    r"\b(terminal.*terminal|read_file.*patch|write_file.*terminal|"
    r"patch.*test|cronjob.*cronjob|delegate.*delegate)\b",
]

PATTERNS = {
    "correction": re.compile("|".join(CORRECTION_PATTERNS), re.IGNORECASE),
    "preference": re.compile("|".join(preference_patterns), re.IGNORECASE),
    "decision": re.compile("|".join(decision_patterns), re.IGNORECASE),
    "pattern": re.compile("|".join(tool_patterns), re.IGNORECASE),
    "lesson": re.compile("|".join(lesson_patterns), re.IGNORECASE),
    "gap": re.compile("|".join(gap_patterns), re.IGNORECASE),
    "approach": re.compile("|".join(approach_patterns), re.IGNORECASE),
}


def load_memory() -> dict:
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {"lessons": [], "gaps": [], "patterns": [], "evaluations": [], "sessions": [], "evolutions": []}


def save_memory(memory: dict) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def load_recent_sessions(limit: int = 50) -> list[dict]:
    """Load most recent JSONL session files, newest first."""
    if not SESSIONS_DIR.exists():
        return []

    session_files = sorted(SESSIONS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]

    sessions = []
    for session_file in session_files:
        try:
            entries = []
            with open(session_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            if entries:
                # Get timestamp from first entry or file mtime
                first = entries[0]
                ts = first.get("timestamp", "")
                if not ts:
                    ts = datetime.fromtimestamp(session_file.stat().st_mtime).isoformat()

                sessions.append({
                    "file": session_file.name,
                    "path": str(session_file),
                    "entries": entries,
                    "timestamp": ts,
                    "session_id": session_file.stem,
                })
        except Exception as e:
            print(f"Error loading {session_file}: {e}", file=sys.stderr)
            continue

    return sessions


def extract_messages(entries: list[dict]) -> list[dict]:
    """Extract user/assistant messages from session entries."""
    messages = []
    for entry in entries:
        role = entry.get("role", "")

        if role not in ("user", "assistant"):
            continue

        content = entry.get("content", "")

        # Handle content as list (multi-block)
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            content = " ".join(text_parts)
        elif not isinstance(content, str):
            content = str(content) if content else ""

        # Skip very long context-compaction entries (not useful for mining)
        if len(content) > 10000:
            content = content[:500]

        if content.strip():
            messages.append({"role": role, "content": content.strip()})

    return messages


def find_mining_hits(messages: list[dict], pattern_name: str, session_id: str = "unknown") -> list[dict]:
    """Find all pattern hits with surrounding context."""
    pattern = PATTERNS.get(pattern_name)
    if not pattern:
        return []

    hits = []
    for i, msg in enumerate(messages):
        content = msg["content"]
        if pattern.search(content):
            # Grab the surrounding messages for context
            context_before = messages[max(0, i - 2):i]
            context_after = messages[i + 1:min(len(messages), i + 3)]

            hits.append({
                "type": pattern_name,
                "content": content[:500],
                "context_before": [m["content"][:200] for m in context_before],
                "context_after": [m["content"][:200] for m in context_after],
                "role": msg["role"],
                "session_id": session_id,
            })

    return hits


def summarize_lesson(hit: dict) -> str:
    """Generate a one-line lesson summary from a hit."""
    content = hit["content"]
    role = hit["role"]
    ptype = hit["type"]

    # Truncate and clean up
    summary = content[:250].replace("\n", " ").strip()

    if ptype == "correction" and role == "user":
        return f"[correction] {summary}"
    elif ptype == "preference" and role == "user":
        return f"[preference] {summary}"
    elif ptype == "decision":
        return f"[decision] {summary}"
    elif ptype == "pattern":
        return f"[recurring] {summary}"
    elif ptype == "lesson":
        return f"[lesson] {summary}"
    else:
        return f"[{ptype}] {summary}"


def mine_sessions(limit: int = 50) -> dict:
    """Main mining function."""
    memory = load_memory()

    sessions = load_recent_sessions(limit)
    total_files = len(sessions)

    all_hits = []
    session_summaries = []

    for session in sessions:
        messages = extract_messages(session["entries"])
        session_hits = []

        for pattern_name in PATTERNS:
            hits = find_mining_hits(messages, pattern_name, session_id=session["session_id"])
            session_hits.extend(hits)
            all_hits.extend(hits)

        if session_hits:
            # Deduplicate by content (first 100 chars)
            seen = set()
            unique_hits = []
            for hit in session_hits:
                key = hit["content"][:100]
                if key not in seen:
                    seen.add(key)
                    unique_hits.append(hit)

            session_summaries.append({
                "session_id": session["session_id"],
                "file": session["file"],
                "timestamp": session["timestamp"],
                "hit_count": len(unique_hits),
                "types": list(set(h["type"] for h in unique_hits)),
                "lessons": [summarize_lesson(h) for h in unique_hits[:5]],
            })

    # Separate new_lessons (correction, preference, decision, pattern, lesson)
    # from gaps and approach patterns (stored separately)
    existing_lessons = {(l.get("lesson", "")[:80]) for l in memory.get("lessons", [])}
    existing_gaps = {(g.get("gap", "")[:80]) for g in memory.get("gaps", [])}
    existing_patterns = {(p.get("pattern", "")[:80]) for p in memory.get("patterns", [])}

    new_lessons = []
    new_gaps = []
    new_patterns = []

    for hit in all_hits:
        summary = summarize_lesson(hit)
        key = summary[:80]
        ptype = hit["type"]

        if ptype in ("gap",):
            if key not in existing_gaps:
                new_gaps.append({
                    "id": str(uuid.uuid4())[:8],
                    "gap": summary,
                    "type": ptype,
                    "source_session": hit.get("session_id", "unknown"),
                    "timestamp": datetime.now().isoformat()[:10],
                    "confidence": "high" if hit["role"] == "user" else "medium",
                })
                existing_gaps.add(key)
        elif ptype in ("approach",):
            if key not in existing_patterns:
                new_patterns.append({
                    "id": str(uuid.uuid4())[:8],
                    "pattern": summary,
                    "type": "approach",
                    "source_session": hit.get("session_id", "unknown"),
                    "timestamp": datetime.now().isoformat()[:10],
                    "confidence": "medium",
                })
                existing_patterns.add(key)
        else:
            if key not in existing_lessons:
                new_lessons.append({
                    "id": str(uuid.uuid4())[:8],
                    "lesson": summary,
                    "type": ptype,
                    "source_session": hit.get("session_id", "unknown"),
                    "timestamp": datetime.now().isoformat()[:10],
                    "confidence": "high" if hit["role"] == "user" else "medium",
                })
                existing_lessons.add(key)

    # Update memory
    memory["lessons"] = (memory.get("lessons", []) + new_lessons)[-100:]
    memory["gaps"] = (memory.get("gaps", []) + new_gaps)[-50:]
    memory["patterns"] = (memory.get("patterns", []) + new_patterns)[-50:]
    memory["sessions"] = (memory.get("sessions", []) + session_summaries)[-50:]

    save_memory(memory)

    return {
        "sessions_scanned": total_files,
        "total_hits": len(all_hits),
        "new_lessons": len(new_lessons),
        "new_gaps": len(new_gaps),
        "new_patterns": len(new_patterns),
        "sessions_with_findings": len(session_summaries),
        "memory_entries": {
            "lessons": len(memory.get("lessons", [])),
            "gaps": len(memory.get("gaps", [])),
            "patterns": len(memory.get("patterns", [])),
        },
    }


if __name__ == "__main__":
    limit = 50
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        try:
            limit = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    result = mine_sessions(limit=limit)
    print(json.dumps(result, indent=2))