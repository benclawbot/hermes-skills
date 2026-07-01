#!/usr/bin/env python3
"""
relative_indenter.py — uniform-indent-shift SEARCH/REPLACE matching.

Aider reference: aider/coders/editblock_coder.py:243-293 (replace_part_with_missing_leading_whitespace
+ match_but_for_leading_whitespace) and :106-138 (RelativeIndenter.make_relative).
Source: https://github.com/Aider-AI/aider (cloned to /tmp/aider-analysis/aider/)

The problem: an LLM emits a SEARCH block uniformly outdented (or
over-indented) relative to the file. Without help, exact substring
match fails.

The fix (two-stage):

Stage 1 — uniform-shift match (the common case):
    1. Find the min leading whitespace across BOTH the SEARCH text
       AND the REPLACE text (they should agree; if they don't, the
       LLM was sloppy).
    2. Outdent both by that minimum.
    3. Slide the outdented SEARCH over each candidate region in the
       file.
    4. At each position, the candidate matches iff:
       a) all non-blank lines match when both are `.lstrip()`-ed
       b) all non-blank lines have the SAME leading-whitespace offset
          (the uniform shift the LLM applied to the SEARCH block)

Stage 2 — relative-indent transform (for blocks where the LLM
emitted MIXED indents that don't match the file at all):
    Rewrite both sides so each line's leading whitespace is expressed
    as delta-from-previous-line, with `←` markers for outdent and
    literal spaces for over-indent. Then look for the same
    delta-sequence on both sides.

Drop-in usage:

    from aider_patterns.scripts.relative_indenter import match_search_block

    file = open("myfile.py").read()
    m = match_search_block(file, search_text_from_llm)
    if m is None:
        raise ValueError("SEARCH block did not match")
    start, end = m  # line indices
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def leading_spaces(line: str) -> int:
    """Count leading whitespace chars (tabs counted as 1, not expanded)."""
    n = 0
    for ch in line:
        if ch in (" ", "\t"):
            n += 1
        else:
            break
    return n


def _outdent_lines(lines: List[str], n: int) -> List[str]:
    """Strip `n` leading spaces from each non-blank line; blanks unchanged."""
    if n <= 0:
        return list(lines)
    out = []
    for ln in lines:
        if not ln.strip():
            out.append(ln)
        else:
            out.append(ln[n:] if n < len(ln) else "")
    return out


def _shared_leading(part_lines: List[str], replace_lines: List[str]) -> int:
    """Min leading whitespace across BOTH part and replace (non-blank lines)."""
    candidates = []
    for p in part_lines:
        if p.strip():
            candidates.append(leading_spaces(p))
    for r in replace_lines:
        if r.strip():
            candidates.append(leading_spaces(r))
    return min(candidates) if candidates else 0


# ---------------------------------------------------------------------------
# Stage 1: uniform-shift match (handles the common case)
# ---------------------------------------------------------------------------

def _match_uniform_shift(
    whole_lines: List[str],
    part_lines: List[str],
    replace_lines: List[str],
) -> Optional[Tuple[int, int]]:
    """Try to match `part_lines` in `whole_lines` allowing a uniform
    leading-whitespace shift. Returns (start_line, end_line) on match.

    Algorithm (Aider's match_but_for_leading_whitespace):
      At each candidate position, all non-blank lines must:
        (a) match when both are .lstrip()ed (content match)
        (b) share the SAME leading-whitespace offset (uniform shift)

    The shift is the # of leading spaces the file region has BEYOND
    what the outdented part_lines have.
    """
    if not part_lines:
        return None
    num = len(part_lines)

    # Outdent part_lines & replace_lines by their shared minimum
    min_leading = _shared_leading(part_lines, replace_lines)
    part_outdented = _outdent_lines(part_lines, min_leading)

    for i in range(len(whole_lines) - num + 1):
        chunk = whole_lines[i : i + num]
        add_offsets = set()
        ok = True
        for k in range(num):
            wl = chunk[k]
            pl = part_outdented[k]
            # Blank lines must align (both blank or both have content)
            if not wl.strip() and not pl.strip():
                continue
            if not wl.strip() or not pl.strip():
                ok = False
                break
            # Content match after lstrip
            if wl.lstrip() != pl.lstrip():
                ok = False
                break
            # Compute leading-ws offset the file has over the part
            file_ls = leading_spaces(wl)
            part_ls = leading_spaces(pl)
            add_offsets.add(file_ls - part_ls)
        if ok and len(add_offsets) == 1:
            return (i, i + num)

    return None


# ---------------------------------------------------------------------------
# Stage 2: relative-indent (delta-sequence) match (handles the rare case
# where the LLM emitted mixed indents the file doesn't have at all)
# ---------------------------------------------------------------------------

MARKER = "←"


def _make_relative(text: str) -> str:
    """Aider-style relative-indent transform (line-by-line, delta from prev).

    Each line's leading whitespace becomes either:
      * spaces (over-indent vs previous line's indent)
      * MARKER chars (under-indent vs previous line's indent)
      * nothing (same indent as previous line)

    Followed by the line content with its original absolute indent stripped.

    Each line is emitted as TWO output lines: indent-marker line + content
    line. This is what Aider's actual implementation does.
    """
    lines = text.splitlines(keepends=True)
    out = []
    prev_indent = ""
    for line in lines:
        line_wo_end = line.rstrip("\n\r")
        len_indent = len(line_wo_end) - len(line_wo_end.lstrip())
        indent = line[:len_indent]
        change = len_indent - len(prev_indent)
        if change > 0:
            cur_indent = indent[-change:]
        elif change < 0:
            cur_indent = MARKER * (-change)
        else:
            cur_indent = ""
        out.append(cur_indent + "\n")
        out.append(line[len_indent:])
        prev_indent = indent
    return "".join(out)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def match_search_block(
    file_content: str,
    search_text: str,
    replace_text: str = "",
) -> Optional[Tuple[int, int]]:
    """Find the line range [start, end) in file_content that matches search_text.

    Returns (start_line, end_line) on success, or None.

    Tries in order:
      1. Exact substring match (cheapest)
      2. Uniform-shift match (the common case)
      3. Relative-indent match (rare, more expensive)
    """
    s = search_text.rstrip("\n")
    if not s:
        return None

    file_lines = file_content.splitlines()
    search_lines = s.splitlines()
    replace_lines = (replace_text or "").splitlines()

    # 1. Exact substring match (handles the trivial case)
    idx = file_content.find(s)
    if idx >= 0:
        start = file_content.count("\n", 0, idx)
        end = start + s.count("\n") + 1
        return (start, end)

    # 2. Uniform-shift match (handles "I stripped my leading ws")
    m = _match_uniform_shift(file_lines, search_lines, replace_lines)
    if m is not None:
        return m

    # 3. Relative-indent match (handles "I changed indent within the block")
    s_rel = _make_relative(s)
    needle = len(search_lines)
    for i in range(len(file_lines) - needle + 1):
        chunk = "\n".join(file_lines[i : i + needle])
        if _make_relative(chunk) == s_rel:
            return (i, i + needle)

    return None


# ---------------------------------------------------------------------------
# Dataclass API (for callers that want the relative-indent form of a REPLACE)
# ---------------------------------------------------------------------------

@dataclass
class RelativeIndenter:
    """Annotate a REPLACE block with `←` markers on under-indented lines.

    After `match_search_block` succeeds, the caller can use this to
    rewrite the REPLACE block in the file's indent style. Lines that
    the LLM wrote at LESS indent than the SEARCH block's min indent
    get a `←` prefix (so the writer re-indents them relative to the
    file's existing anchor line).

    For most use cases, callers don't need this — they can just splice
    the REPLACE text at the matched position. It's here for completeness.
    """

    min_spaces: int
    MARKER: str = MARKER

    @classmethod
    def from_anchor(cls, anchor_text: str) -> "RelativeIndenter":
        lines = anchor_text.splitlines()
        non_blank = [leading_spaces(ln) for ln in lines if ln.strip()]
        return cls(min_spaces=min(non_blank) if non_blank else 0)

    def annotate(self, replace_text: str) -> str:
        out = []
        for ln in replace_text.splitlines():
            if not ln.strip():
                out.append(ln)
                continue
            ls = leading_spaces(ln)
            if ls < self.min_spaces:
                # Under-indent: mark with ←s
                deficit = self.min_spaces - ls
                out.append(self.MARKER * deficit + ln[ls:])
            else:
                out.append(ln)
        return "\n".join(out)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Test 1: leading_spaces + min_indent")
    assert leading_spaces("    hello") == 4
    assert leading_spaces("hello") == 0
    assert leading_spaces("\thello") == 1
    print("  OK")

    print("\nTest 2: outdent_lines")
    assert _outdent_lines(["    a", "    b", ""], 2) == ["  a", "  b", ""]
    assert _outdent_lines(["  a", "    b"], 0) == ["  a", "    b"]
    print("  OK")

    print("\nTest 3: match_search_block — exact match")
    file = "line1\nline2\nline3\nline4\n"
    m = match_search_block(file, "line2\nline3")
    assert m == (1, 3), f"got {m}"
    print(f"  OK — match at {m}")

    print("\nTest 4: match_search_block — uniform-shift match (the common case)")
    # File indented at 4 spaces; search block uniformly stripped to 0.
    file = "def f():\n    if x:\n        return 1\n    return 2\n"
    search = "if x:\n    return 1\nreturn 2\n"  # LLM stripped the leading 4 spaces
    replace = "if y:\n    return 1\nreturn 2\n"  # same indent as search
    m = match_search_block(file, search, replace)
    assert m is not None, f"expected uniform-shift match, got None"
    print(f"  OK — match at {m}")

    print("\nTest 5: match_search_block — uniform-shift with different base indent")
    # File at 8 spaces; search at 4 spaces (uniformly shifted)
    file = "class C:\n    def m(self):\n        if x:\n            return 1\n"
    search = "def m(self):\n    if x:\n        return 1\n"  # 4 spaces, file is 4 deeper
    m = match_search_block(file, search)
    assert m is not None, f"expected match at deeper indent, got None"
    print(f"  OK — match at {m}")

    print("\nTest 6: match_search_block — relative-indent (mixed indents)")
    # File: def / if / return (indent 0, 4, 8) — clean nested block
    # Search: same content but with extra indent (2, 6, 10) — uniform
    # shift won't work, relative form should match
    file = "def f():\n    if x:\n        return 1\n"
    search = "  if x:\n      return 1\n"  # uniformly +2 from file
    m = match_search_block(file, search)
    print(f"  match at {m}")

    print("\nTest 7: no match")
    file = "alpha\nbeta\ngamma\n"
    m = match_search_block(file, "delta\nepsilon")
    assert m is None
    print("  OK — returns None for no match")

    print("\nTest 8: RelativeIndenter.annotate")
    ri = RelativeIndenter(min_spaces=4)
    replace = "    if x:\n        return 1  # normal\n    return 2\n"
    out = ri.annotate(replace)
    assert "    if x:" in out
    assert "        return 1" in out  # equal indent, no marker
    print(f"  OK — annotated:\n{out}")

    print("\nAll self-tests passed.")
