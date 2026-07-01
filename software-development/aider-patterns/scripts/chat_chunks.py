#!/usr/bin/env python3
"""
chat_chunks.py — Claude prompt-cache checkpointing.

Aider reference: aider/coders/chat_chunks.py:14-50
Source: https://github.com/Aider-AI/aider (cloned to /tmp/aider-analysis/aider/)

Claude prompt cache writes every ~4 cache_control breakpoints. The
default ordering wastes cache hits because the boundary moves every
turn (anything that changes goes after the marker). Chunking puts the
cache_control marker at the END of each STABLE chunk, so the marker
stays in the same logical position across edits.

Stable chunks (in order):
    system        — system prompt (changes rarely)
    examples      — few-shot examples (never changes mid-session)
    done          — summarized past conversation (only on summary)
    repo          — repo-map (changes on file save, not on every turn)
    readonly_files — files added with /read (changes on /drop)
    chat_files    — files added with /add (changes on /drop)
    cur           — current turn (volatile)
    reminder      — post-turn reminder

Cache-control markers go on the LAST message of (system|examples),
(repo|readonly), and chat_files — the three natural stability boundaries.

Drop-in usage:

    from aider_patterns.scripts.chat_chunks import ChatChunks

    chunks = ChatChunks(
        system=[{"role": "system", "content": "..."}],
        examples=[{"role": "user", "content": "..."},
                  {"role": "assistant", "content": "..."}],
        done=[],
        repo=[{"role": "user", "content": repo_map_text}],
        readonly_files=[...],
        chat_files=[{"role": "user", "content": "file1.py..."}],
        cur=[{"role": "user", "content": user_msg}],
        reminder=[],
    )
    chunks.add_cache_control_headers()
    messages = chunks.all_messages()
    # Send to Claude API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ChatChunks:
    """Conversation split into stability chunks for prompt caching."""

    system: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    done: List[Dict[str, Any]] = field(default_factory=list)
    repo: List[Dict[str, Any]] = field(default_factory=list)
    readonly_files: List[Dict[str, Any]] = field(default_factory=list)
    chat_files: List[Dict[str, Any]] = field(default_factory=list)
    cur: List[Dict[str, Any]] = field(default_factory=list)
    reminder: List[Dict[str, Any]] = field(default_factory=list)

    def all_messages(self) -> List[Dict[str, Any]]:
        """Concatenate all chunks in canonical order."""
        return (
            self.system
            + self.examples
            + self.readonly_files
            + self.repo
            + self.done
            + self.chat_files
            + self.cur
            + self.reminder
        )

    def add_cache_control_headers(self) -> None:
        """Insert `cache_control: {type: ephemeral}` at end of each stable chunk."""
        # Chunk 1: examples or system (whichever is the boundary that changes last)
        if self.examples:
            self._mark(self.examples)
        else:
            self._mark(self.system)

        # Chunk 2: repo or readonly_files (whichever is present)
        if self.repo:
            self._mark(self.repo)
        else:
            self._mark(self.readonly_files)

        # Chunk 3: chat_files (volatile across /add /drop)
        self._mark(self.chat_files)

    def _mark(self, messages: List[Dict[str, Any]]) -> None:
        """Mark the last message of `messages` as cache-control-end."""
        if not messages:
            return
        content = messages[-1]["content"]
        # Convert str content to Anthropic's list-of-blocks format
        if isinstance(content, str):
            content = {"type": "text", "text": content}
        # Mutate in place — caller passed references
        if isinstance(content, dict):
            content["cache_control"] = {"type": "ephemeral"}  # type: ignore[index]
            messages[-1]["content"] = [content]
        else:
            # Already a list of blocks; mark the last block
            content[-1]["cache_control"] = {"type": "ephemeral"}  # type: ignore[index]  # noqa: E501

    def cacheable_messages(self) -> List[Dict[str, Any]]:
        """Return messages with cache_control markers, useful for inspection."""
        msgs = []
        for m in self.all_messages():
            content = m.get("content")
            if isinstance(content, list) and content and isinstance(content[0], dict) \
                    and content[0].get("cache_control"):
                msgs.append(m)
        return msgs

    def stats(self) -> Dict[str, int]:
        """Token-estimate-style stats: how many messages per chunk, how many cache hits."""
        return {
            "system": len(self.system),
            "examples": len(self.examples),
            "done": len(self.done),
            "repo": len(self.repo),
            "readonly_files": len(self.readonly_files),
            "chat_files": len(self.chat_files),
            "cur": len(self.cur),
            "reminder": len(self.reminder),
            "cacheable": len(self.cacheable_messages()),
        }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Test 1: empty chunks")
    c = ChatChunks()
    assert c.all_messages() == []
    c.add_cache_control_headers()  # should be no-op
    assert c.cacheable_messages() == []
    print(f"  OK — stats={c.stats()}")

    print("\nTest 2: minimal chunks (system + cur)")
    c = ChatChunks(
        system=[{"role": "system", "content": "You are a helpful assistant."}],
        cur=[{"role": "user", "content": "Hello!"}],
    )
    c.add_cache_control_headers()
    msgs = c.all_messages()
    assert len(msgs) == 2
    # System message should have cache_control
    sys_content = msgs[0]["content"]
    assert isinstance(sys_content, list)
    assert sys_content[0].get("cache_control") == {"type": "ephemeral"}
    # Cur message should NOT have cache_control
    cur_content = msgs[1]["content"]
    assert isinstance(cur_content, str), "cur content unchanged"
    print(f"  OK — system has cache_control, cur does not")
    print(f"  stats={c.stats()}")

    print("\nTest 3: full chunks (system + examples + repo + chat_files)")
    c = ChatChunks(
        system=[{"role": "system", "content": "sys"}],
        examples=[
            {"role": "user", "content": "ex_user"},
            {"role": "assistant", "content": "ex_asst"},
        ],
        repo=[{"role": "user", "content": "repo_map"}],
        readonly_files=[{"role": "user", "content": "read1"}],
        chat_files=[{"role": "user", "content": "chat1"}],
        cur=[{"role": "user", "content": "user_msg"}],
    )
    c.add_cache_control_headers()
    cacheable = c.cacheable_messages()
    # examples last message + repo last message + chat_files last message = 3
    assert len(cacheable) == 3, f"expected 3 cacheable, got {len(cacheable)}"
    print(f"  OK — {len(cacheable)} cache breakpoints")
    print(f"  stats={c.stats()}")

    print("\nTest 4: examples chunk takes priority over system when both present")
    c = ChatChunks(
        system=[{"role": "system", "content": "sys"}],
        examples=[{"role": "user", "content": "ex"}],
        cur=[{"role": "user", "content": "now"}],
    )
    c.add_cache_control_headers()
    cacheable = c.cacheable_messages()
    # examples is marked (not system)
    sys_content = c.system[0]["content"]
    ex_content = c.examples[0]["content"]
    assert isinstance(ex_content, list) and ex_content[0].get("cache_control")
    assert isinstance(sys_content, str), "system unchanged when examples present"
    print(f"  OK — examples boundary marked, system untouched")
    print(f"  stats={c.stats()}")

    print("\nAll self-tests passed.")
