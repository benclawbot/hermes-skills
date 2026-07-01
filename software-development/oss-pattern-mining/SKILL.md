---
name: oss-pattern-mining
description: >
  Read a public open-source repository end-to-end and extract design patterns
  that can be applied to a similar codebase. The deliverable is a structured
  pattern report (concrete patterns with file:line references, ranked by
  impact), not a summary. Use when the user shares a GitHub URL and says
  "take inspiration", "learn from this", "study how X does it", "extract
  patterns from Y", "what can we steal from this repo", or "improve our
  tool by looking at how Z does it". Distinct from codebase-porting
  (which implements INTO a real codebase) and last30days (web research,
  not code reading). The output is a patterns report, not an implementation
  plan — if the user later wants to implement the patterns, route to
  codebase-porting or writing-plans.

triggers:
  - take inspiration from
  - learn from this repo
  - study how X does it
  - extract patterns from
  - what can we steal from
  - improve our code by looking at
  - analyze this github repo
  - read this repo and find patterns
  - look at how aider does it
  - look at how langchain does it
  - look at how X implements Y

---

# OSS Pattern Mining

The user wants design patterns extracted from a public OSS repo so they
can apply them to their own similar project. The deliverable is a
**pattern report with file:line references and concrete code snippets**,
ranked by impact. Not a code review, not an architecture summary, not an
implementation plan.

## When to Use

- User shares a GitHub URL and wants to learn from it
- User says "take inspiration", "improve our code by looking at how X does Y"
- User says "study this codebase", "extract patterns", "what can we steal"
- The repo is a public reference implementation in a domain adjacent to
  the user's work (LLM tooling, CLI tools, agent frameworks, etc.)

**Do NOT use when:**
- The user wants to implement INTO a codebase → `codebase-porting`
- The user wants a single-file architecture overview → lighter, ad-hoc
- The user wants to read a specific file in isolation → just read it
- The user wants to know "how does X work" as background, not as
  inspiration for their own work → read it, don't write a report

## Core Principle: Verify Before Reporting

**The single most important rule**: every file:line reference and every
code snippet in the final report must be verified against the actual
source. The number one failure mode of "analyze this repo" tasks is
plausible-looking line numbers and snippets that don't match the file.

A subagent can return a report that *sounds* right and contains references
to functions and lines that don't exist. Before delivering any pattern
report:

1. Spot-check 3-5 of the most surprising claims. Open the file at the
   claimed line. Read the surrounding 20 lines. Confirm the snippet is
   real and the line number is within ±5 lines.
2. Verify the registry / plugin pattern by reading the actual `__init__.py`
   the report claims the registry lives in.
3. If a report says "look at lines 800-850 of file X", read those lines
   and check it actually has what the report claims.

The cost of one verification round is 30-60 seconds. The cost of a report
full of fabricated file:line refs is the user catching you later and
losing trust in your work.

## Workflow

### Phase 0: Scope check

**Before cloning anything**, ask one question if the user hasn't been
specific:

- What kind of patterns are you looking for? (Architecture / UX / error
  handling / extensibility / specific feature X)
- What's the target project you want to apply them to?

If the user said "be thorough" or "read every file" — they want the full
deep-read, not a narrow slice. Skip the scope question.

### Phase 1: Clone + Map

```bash
# Always shallow clone to /tmp/<topic>-analysis/. Don't pollute the
# working dir, don't deep-clone unless git history is actually needed.
rm -rf /tmp/<topic>-analysis && mkdir /tmp/<topic>-analysis
cd /tmp/<topic>-analysis
git clone --depth 1 <url> .

# Map: file count, top-level layout, biggest files
find . -type f -name "*.py" | wc -l
ls <package>/
wc -l <package>/*.py | sort -rn | head -20
```

The file count + size distribution tells you the architecture before you
read a single line:

- <30 .py files: monolith. Read it all.
- 30-150 .py files: layered, one central class probably dominates. Find
  the biggest file, that's the god class.
- 150+ .py files: clear subdir structure. Map the subdirs, identify
  the central abstraction in each, read those.

### Phase 2: Identify the central files

Three signals to look for, in order:

1. **Size**: `wc -l | sort -rn | head` — the biggest file is almost
   always the central class
2. **Imports**: `grep -l "from \." <dir>/*.py` — the file that everyone
   else imports from is the base class / shared abstraction
3. **Re-exports**: the `__init__.py` with the longest import list is the
   registry / plugin surface

For an LLM tool, the central class is almost always `<package>/<role>.py`
containing the `Coder` / `Agent` / `Runner` / `<Verb>er` base class with
a registry pattern in `__init__.py`. Read both in full first.

### Phase 3: Read deeply — but in parallel

For a 100+ file repo, you cannot read every file in one turn. Two
strategies work:

**Strategy A: delegate parallel research.**

```python
delegate_task(tasks=[
  {"goal": "Read these files thoroughly and extract concrete patterns...",
   "context": "Working dir: /tmp/<topic>-analysis/. Files: <list>",
   "toolsets": ["file"]},
  {"goal": "Read these other files...", "context": "..."},
  {"goal": "Read these more files...", "context": "..."}
])
```

Each subagent reads 8-15 files. Each returns concrete patterns with
file:line refs. The subagent's final summary enters your context, not
the raw files.

**Strategy B: read in main context with truncation.**

Use `read_file` with `limit` + `offset` to read 500-line windows. Skip
boilerplate, focus on the central class. When you hit a pattern, grab
the snippet + line number and move on.

For 13k+ LOC repos, Strategy A wins. For <5k LOC, Strategy B works.

### Phase 4: Verify surprising claims

For each "this is clever" claim in the subagent's report (or your own
notes), open the file at the claimed line and read it. This is the rule
from "Core Principle" above. Spend 5 minutes here. It's the difference
between a useful report and a useful-looking report.

Specific things to verify:

- The registry pattern: does the `__init__.py` actually export a flat
  `__all__`? Does the base class's `create()` method actually iterate
  it? Are the choices for the CLI derived from it?
- The "did you mean" fallback: does the actual code use fuzzy matching,
  or did the subagent hallucinate that?
- Any claim about a specific function ("the cache is keyed by mtime
  and versioned directory name") — open the function, confirm.

### Phase 5: Write the report

**Structure** (this is what works):

1. **Top-of-report section**: what the repo is, file count, central
   class, total LOC. One paragraph, no philosophy.
2. **Ranked patterns, biggest impact first**. Each pattern gets:
   - 1-line title
   - "Why it's gold" or "Why it matters" — one sentence
   - Code snippet (5-20 lines) with file:line reference
   - "Steal this" — concrete instruction on how to apply it
3. **Smaller defensive tricks** — short list, no code, just names
4. **Packaging notes** — pyproject.toml, optional deps, install flow
5. **What NOT to copy** — the load-bearing negative section
6. **Concrete takeaways ranked** — if you only adopt 3: 1, 2, 3.

**Anti-patterns in the report:**

- Long prose explaining the project. The user can read the README.
  They came to you for patterns.
- Philosophy ("separation of concerns matters"). The user knows.
- "This repo is well-architected" — empty praise.
- Recommendations without file:line refs.
- Patterns labeled as "good" without explaining why for THIS user.

**Output location**: write to `/tmp/<topic>-analysis/patterns.md` for
the full report. If the user wants it elsewhere (Obsidian, repo, chat),
copy it there after.

### Phase 6: Deliver

For Telegram, the report is too long for one message. Options:

- `html-to-telegram`: convert to a `.txt` and deliver
- Summarize the top 5 patterns in chat, link to the file path with
  `MEDIA:/tmp/<topic>-analysis/patterns.md` for the full version
- If the user said "be thorough", deliver the full markdown as an
  attachment

The user said "be thorough" in this exact session — the deliverable was
two 25-47KB markdown files at predictable paths
(`/tmp/aider-analysis/patterns.md` and `~/aider-patterns-analysis.md`).
When the user explicitly asks for thorough, full report > summary.

## Common Pitfalls

### Skipping Phase 4 verification

The subagent said "look at line 525 of `repomap.py` for the PageRank
personalization logic." You didn't read it. The user later tries to
copy that pattern and the line numbers are off by 50. Trust is gone.

**Fix**: every report goes through 5-10 minutes of verification before
delivery. If you can't verify a claim in time, drop the claim.

### Reading 100 files in main context

You start reading files, each one is 500+ lines, you burn 200k tokens
and only cover 20% of the repo. The report is shallow.

**Fix**: delegate_task with 2-3 parallel subagents, each gets a
specific file list. The subagent's summary is condensed; the raw
files never enter your context.

### Reporting patterns without ranking

You list 12 patterns alphabetically. The user has to figure out which
to adopt first. The report reads like documentation, not a plan.

**Fix**: rank by impact. Top 3 should be the patterns that, if
adopted alone, would meaningfully change the user's codebase. Bottom
5 should be polish.

### Missing the "What NOT to copy" section

The user adopts a pattern, it doesn't fit their stack, and they
come back saying "you said this was a great pattern." The negative
section prevents that.

**Fix**: always include "What NOT to copy" with 3-5 specific reasons
(dep weight, breaking-change risk, the God-class anti-pattern that
shipped because no one had time to refactor).

### Conflating pattern-mining with implementation planning

You read the repo, find patterns, and then start writing an
implementation plan for the user's codebase. The user didn't ask for
that. They asked for inspiration.

**Fix**: deliver patterns only. If they say "now build this" or
"implement that", route to `codebase-porting` (for "implement this
spec") or `writing-plans` (for "plan the work").

### The "analysis is a research skill" trap

You treat the task like research: search the web, gather external
reviews, summarize what other people say. That's `last30days` /
`notebooklm-research` territory.

**Fix**: pattern mining is **reading source code** with intent. External
docs are background; the patterns come from the code itself.

## Output Template

```markdown
# <Repo Name> — patterns worth stealing for <user's domain>

Repo at `/tmp/<topic>-analysis/<repo>`. ~Nk LOC of core, N .py files,
<one-line maturity assessment>.

## 1. <Pattern name> (<class-level descriptor>)

<file>:<line_range>:

<5-15 line code snippet>

**Steal this** for <specific application>: <one sentence on how to
adapt it to the user's codebase>.
```

## Related Skills

- `codebase-porting` — inverse direction: implement INTO a real codebase
- `last30days` — research what people say, not what code does
- `writing-plans` — turn a chosen pattern into a bite-sized task list
- `notebooklm-research` — research a topic using external sources
- `research-briefing-pdf` — produce a polished PDF report (different
  output format than this skill's markdown report)
- `aider-patterns` — pre-packaged drop-in patterns extracted from
  Aider (registry, PageRank repo map, model registry, ChatChunks
  cache checkpointing, LazyLiteLLM, strict exceptions, indent-
  invariant SEARCH/REPLACE, reflection loop, SwitchCoder, ConfirmGroup,
  fuzzy fallback, write-retry). Load it directly if the user wants
  LLM-CLI patterns specifically — skip the mine-and-report loop.
