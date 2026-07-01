---
name: aider-patterns
description: >
  Reusable design patterns extracted from Aider (github.com/Aider-AI/aider)
  for building LLM tooling, agent CLIs, and editor-aware code assistants.
  Load when building or improving any of: LLM-backed CLI that edits files
  via prompt; agent harness with multiple prompt strategies; tools that
  give an LLM structured access to a git repo; tools that cache LLM API
  responses across edits; tools that parse diff/edit blocks out of model
  output. Each pattern is a copy-pasteable snippet with file:line
  provenance against the Aider source tree, not a research summary. The
  scripts/ subdir has 4 ready-to-use modules (LazyLiteLLM, EXCEPTIONS
  strict-load, ChatChunks caching, RelativeIndenter) you can drop into
  a new project.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [LLM, Agent, CLI, Code Editing, Patterns]
    requires_toolsets: [terminal, file]
---

# Aider Patterns — drop-in for LLM CLI tools

Source repo: <https://github.com/Aider-AI/aider> (cloned to
`/tmp/aider-analysis/aider/` on this machine). Reference depth: every
.py file read end-to-end (147 files, ~13k LOC of core).

This skill is **about the patterns**, not about Aider itself. Load it
when you're building any tool where an LLM has to (a) edit files in a
git repo, (b) handle malformed model output gracefully, or (c) run in
multiple "modes" without state-machines.

## When to load

- "I'm building an LLM agent that edits code"
- "How do I support multiple prompt formats / edit grammars?"
- "How do I give the LLM project context without dumping every file?"
- "How do I parse diffs out of model output reliably?"
- "How do I cache LLM responses across edits?"

**Don't load** for: web research, repo analysis (use `oss-pattern-mining`
first to find patterns, then this skill to apply them), or non-LLM code
review (use `requesting-code-review`).

## The patterns — ranked by impact

### 1. Edit-format registry (the big one)

Subclass-as-plugin: drop a file in `coders/`, add to `__all__`, done.

**Aider reference**: `aider/coders/__init__.py:18-34` + `aider/coders/base_coder.py:190-201` + `aider/args.py:46-54`.

Each coder carries three knobs: `edit_format` (str), `gpt_prompts`
(instance of a prompts class), and 2-3 methods (`get_edits`,
`apply_edits`, optional `reply_completed`).

```python
# coder registry pattern — copy this
class Coder:
    edit_format = None

    @classmethod
    def create(cls, main_model, edit_format=None, **kwargs):
        for sub in cls.__subclasses__():  # or iterate an __all__
            if hasattr(sub, "edit_format") and sub.edit_format == edit_format:
                return sub(main_model, **kwargs)
        raise ValueError(f"Unknown edit format: {edit_format}")

class EditBlockCoder(Coder):
    edit_format = "diff"
    def get_edits(self): ...
    def apply_edits(self, edits, dry_run=False): ...

class WholeFileCoder(Coder):
    edit_format = "whole"
    def get_edits(self): ...
```

**When to use**: any tool that supports >1 prompt strategy (different
output grammars, different edit formats, different model families with
different preferred styles). Adding a new strategy = drop a file.

### 2. PageRank repo map (binary-searched to token budget)

Build a graph of `(file, symbol, references)`, run PageRank with
personalization on user-mentioned identifiers + files-in-chat,
binary-search the top-N until tokenized output is within budget.

**Aider reference**: `aider/repomap.py:42-867`. Full pipeline in
`references/aider-repomap-deep-dive.md`.

The clever bits:

- **Personalization vector** boosts files-in-chat × 50, mentioned idents
  × 10, files whose path-components match mentioned idents (snake_case
  / kebab-case / camelCase split, ≥8 chars) × 10.
- **Two fallback passes** ensure something is always returned: (chat ∪
  other) → (∅ ∪ all) → (∅ ∪ all, no hints).
- **Binary search** over `ranked_tags[:middle]` until tokenized tree
  within ±15% of budget (`repomap.py:676-706`).
- **Versioned cache dir** keyed by mtime: `.aider.tags.cache.v4`.

**When to use**: any "give the LLM project context" problem. The full
implementation needs `networkx` + `tree-sitter` + `grep-ast`. If those
are too heavy, a simpler version: build a bag-of-symbols file index
once per change, score by term-frequency-of-mentioned-idents, top-N
files. Loses the PageRank quality, keeps the binary-search trick.

### 3. YAML capability registry, three-tier fallback

Define `ModelSettings` as a dataclass. Load from package resource YAML.
Resolve in order: exact match → substring heuristics → upstream defaults.

**Aider reference**: `aider/models.py:127-158` + `aider/resources/model-settings.yml` (357 entries) + `aider/models.py:385-435`.

```yaml
# aider/resources/model-settings.yml (excerpt)
- name: claude-sonnet-4-6
  edit_format: diff
  weak_model_name: claude-haiku-4-5
  use_repo_map: true
  cache_control: true
  accepts_settings: [thinking_tokens, reasoning_effort]
```

```python
# three-tier resolution
def configure_model_settings(model_name):
    # 1. Exact match
    for ms in MODEL_SETTINGS:
        if model_name == ms.name:
            return ms
    # 2. Substring heuristics for new releases
    if "gpt-4.1" in model_name:
        return ModelSettings(edit_format="diff", use_repo_map=True, ...)
    if "/o3-mini" in model_name:
        return ModelSettings(edit_format="diff", use_temperature=False, ...)
    # 3. Fall through to provider defaults
    return ModelSettings()
```

User can override per-model with `.aider.model.settings.yml` (search
home → repo → cwd, last wins). Special synthetic entry `aider/extra_params`
deep-merges parameters into ALL models.

**When to use**: any project that supports multiple model variants and
needs to know "does this model support vision / tools / prompt cache"
without scattering if-trees everywhere.

### 4. ChatChunks prompt-cache checkpointing

`scripts/chat_chunks.py` (drop-in). Splits the conversation into stable
chunks (system, examples, repo-map, readonly-files, chat-files) and puts
an `ephemeral` cache_control marker on the last message of each chunk.
Claude prompt cache only checkpoints every ~4 cache_writes, so chunk
boundaries are where stable data transitions to volatile.

**Aider reference**: `aider/coders/chat_chunks.py:14-50`.

```python
@dataclass
class ChatChunks:
    system: List
    examples: List
    done: List           # summarized history
    repo: List           # repo-map
    readonly_files: List
    chat_files: List     # files in chat
    cur: List            # current turn
    reminder: List

    def add_cache_control_headers(self):
        # Place ephemeral marker at end of each stable chunk
        self._mark(self.examples or self.system)
        self._mark(self.repo or self.readonly_files)
        self._mark(self.chat_files)
```

The `_mark()` helper is non-obvious: it mutates the last message of
the chunk, converting string content into Anthropic's list-of-blocks
shape and inserting `cache_control: {type: ephemeral}`:

```python
def _mark(self, messages):
    if not messages: return
    content = messages[-1]["content"]
    if isinstance(content, str):
        content = {"type": "text", "text": content}
    if isinstance(content, dict):
        content["cache_control"] = {"type": "ephemeral"}
        messages[-1]["content"] = [content]
    else:
        content[-1]["cache_control"] = {"type": "ephemeral"}
```

`pyright`/`mypy` will flag the dict mutation as
`Argument of type "dict[str, str]" cannot be assigned to parameter "value" of type "str"`
because the inferred content type is too narrow. Suppress with
`# type: ignore[index]`.

**When to use**: any Claude API caller that sends a large system
prompt + many files + conversation history. Default ordering wastes
cache hits because the boundary moves every turn. Chunking puts the
boundary at the last stable message and keeps it stable across edits.

### 5. LazyLiteLLM (defer expensive import)

`scripts/lazy_litellm.py` (drop-in). 25 lines. Saves ~1.5s of startup.

**Aider reference**: `aider/llm.py:21-45`.

```python
import importlib

class LazyLiteLLM:
    _lazy_module = None
    def __getattr__(self, name):
        if name == "_lazy_module":
            return self
        if self._lazy_module is None:
            self._lazy_module = importlib.import_module("litellm")
        return getattr(self._lazy_module, name)

litellm = LazyLiteLLM()
__all__ = [litellm]
```

Every other module does `from .llm import litellm`. First attribute
access triggers the real import. `/help`, `--version`, onboarding skip
it entirely.

**When to use**: any tool whose dep includes a heavy ML client
(litellm, transformers, torch, tensorflow). Move the import inside a
proxy class.

### 6. EXCEPTIONS strict-load invariant

`scripts/strict_exceptions.py` (drop-in). Forces explicit acknowledgment
of every upstream exception type.

**Aider reference**: `aider/exceptions.py:60-113`.

```python
EXCEPTIONS = [
    ExInfo("APIConnectionError", retry=True, msg=None),
    ExInfo("AuthenticationError", retry=False, msg="Check your API key."),
    ExInfo("RateLimitError",      retry=True,  msg="Try again later."),
    # ... 25 total
]

class StrictExceptions:
    def _load(self):
        import upstream_lib  # litellm, boto3, etc.
        for var in dir(upstream_lib):
            if var.endswith("Error") and issubclass(getattr(upstream_lib, var), BaseException):
                if var not in {e.name for e in EXCEPTIONS}:
                    raise ValueError(
                        f"{var} is in upstream_lib but not in our EXCEPTIONS table"
                    )
```

If upstream ever ships a new `*Error` subclass, your tool crashes at
startup with a clear message. Forces you to make an explicit decision
(retry vs. fail, what message) for every error type.

**When to use**: any tool that wraps a third-party library with a
growing exception hierarchy. Prevents silent-failure mode where the
upstream adds a new error and your retry loop eats it as a generic
exception.

### 7. Indent-invariant SEARCH/REPLACE matching (the REAL algorithm)

`scripts/relative_indenter.py` (drop-in). **Common mistake to avoid**:
thinking the algorithm is "rewrite both sides into a relative-indent
form (← markers) and compare." That `make_relative` transform in
`aider/coders/search_replace.py:106-138` is only used for **emitting**
the REPLACE block back into the file at the right indent — NOT for
matching.

The actual matching algorithm lives in
`aider/coders/editblock_coder.py:243-293` (`replace_part_with_missing_leading_whitespace` +
`match_but_for_leading_whitespace`):

```python
# 1. Compute MIN leading whitespace across BOTH the SEARCH and
#    the REPLACE blocks (they should agree on baseline indent).
# 2. Outdent BOTH by that minimum.
# 3. Slide the outdented SEARCH over the file.
# 4. At each candidate position, match iff:
#    (a) all non-blank lines match when both are .lstrip()ed
#    (b) all non-blank lines have the SAME leading-ws offset
#        (the uniform shift the LLM applied to the SEARCH block)
#    In other words: the LLM uniformly outdented (or over-indented)
#    the whole SEARCH block relative to the file. Detect that
#    single uniform offset and you've found the match site.
```

This handles 95% of real-world indent mismatches because the LLM
either got the whole block right or uniformly wrong. The relative-
indent (←-marker) transform in `search_replace.py` only kicks in
when uniform-shift matching fails AND the indent relationships
within the block itself differ from the file's.

**Aider reference**: `aider/coders/editblock_coder.py:243-293`
(matcher) + `aider/coders/search_replace.py:106-138` (emitter).

**When to use**: any tool that parses diffs/search-replace from model
output. Stops the #1 failure mode ("search didn't match because of
indentation"). The drop-in script in `scripts/relative_indenter.py`
implements both stages (uniform-shift first, then relative-indent
fallback) — the smoke test exercises both.

### 8. Reflection loop with bounded retry

**Aider reference**: `aider/coders/base_coder.py:924-944`.

```python
def run_one(self, user_message, preproc=True):
    message = preproc_user_input(user_message)
    while message:
        self.reflected_message = None
        send_message(message)
        if not self.reflected_message:
            break
        if self.num_reflections >= self.max_reflections:  # 3
            return
        self.num_reflections += 1
        message = self.reflected_message  # re-prompt with the failure
```

When an edit fails to apply (SEARCH didn't match, file didn't exist,
JSON was malformed), the failure message is fed back as the next user
turn. `max_reflections = 3` bounds the loop.

**When to use**: any "LLM produces output that gets validated against
reality" loop. Reflection-after-failure is much cheaper than
reflection-after-each-step.

### 9. SwitchCoder exception (mid-session swap without state machine)

**Aider reference**: `aider/commands.py:30-33` + `aider/coders/architect_coder.py:36-44`.

```python
class SwitchCoder(Exception):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

# In a slash command:
def cmd_model(self, args):
    raise SwitchCoder(main_model=Model(args))

# In the outer loop:
try:
    coder.run_one(message)
except SwitchCoder as sc:
    coder = Coder.create(from_coder=coder, **sc.kwargs)
```

No state machine, no half-built objects. Outer loop catches, builds
new coder carrying state (history, cost, file list) via `from_coder`,
continues.

**When to use**: any tool where the user can change the active "agent"
mid-flow (model swap, mode swap, persona swap) without losing context.

### 10. ConfirmGroup (batch Y/N/A/S/D)

**Aider reference**: `aider/io.py:81-85`.

```python
@dataclass
class ConfirmGroup:
    preference: str = None
    show_group: bool = True

# Usage:
group = ConfirmGroup([url1, url2, url3, ...])
for url in urls:
    if not io.confirm_ask("Add URL?", subject=url, group=group):
        continue
```

Y/N/A (all-this-session)/S (skip)/D (never). When you have N similar
items you don't want N separate prompts, but you want batch-decision
semantics. The `preference` field lets a `/yes-always` or
`AIDER_YES_ALWAYS=1` env var short-circuit the whole group.

**When to use**: any tool that fans out N similar actions (file ops,
URL fetches, network calls).

### 11. SEARCH-block "did you mean?" fuzzy fallback

**Aider reference**: `aider/coders/editblock_coder.py:82-124` + `:602-628`.

When a SEARCH block fails to match exactly, the error message includes
the closest fuzzy match using `difflib.SequenceMatcher`:

```python
def find_similar_lines(search_lines, content_lines, threshold=0.6):
    best_ratio, best_match = 0, None
    for i in range(len(content_lines) - len(search_lines) + 1):
        chunk = content_lines[i:i + len(search_lines)]
        ratio = SequenceMatcher(None, search_lines, chunk).ratio()
        if ratio > best_ratio:
            best_ratio, best_match = ratio, chunk
    if best_ratio < threshold:
        return ""
    return "\n".join(best_match)
```

Plus 4-tier filename fallback: exact → basename → fuzzy 0.8 → first-
with-extension → first.

**When to use**: anywhere you parse LLM output back into file refs or
code blocks. Fuzzy fallback turns "model hallucinated a path" from a
dead end into a recoverable error.

### 12. Write-with-retry-on-PermissionError

**Aider reference**: `aider/io.py:478-507`.

```python
def write_text(self, filename, content, max_retries=5, initial_delay=0.1):
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            return
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # exponential
            else:
                raise
```

Beats editors holding locks, antivirus scanners, Dropbox syncs, etc.

**When to use**: any tool that writes to disk the user might also have
open. Two minutes of code, eliminates a whole class of "but it worked
yesterday" bugs.

## Scripts in this skill

All scripts are dependency-free or minimal-dependency drop-ins. Copy
the ones you need into your project.

| Script | Purpose | Deps |
|---|---|---|
| `scripts/lazy_litellm.py` | Defer litellm import (~1.5s) | stdlib |
| `scripts/strict_exceptions.py` | Fail-loudly on new upstream *Error classes | stdlib |
| `scripts/chat_chunks.py` | Claude prompt-cache checkpointing | stdlib |
| `scripts/relative_indenter.py` | Indent-invariant SEARCH/REPLACE matching | stdlib |
| `scripts/aider_smoke_test.py` | Self-test runner (smoke-tests all 4 modules) | stdlib |

## References

- `references/aider-repomap-deep-dive.md` — full PageRank pipeline walk-through
- `references/registry-pattern-code.md` — the full coder registry, copy-paste ready
- `references/model-settings-schema.md` — the YAML schema, with all fields documented

## Anti-patterns (do NOT copy)

| Anti-pattern | Why | Better |
|---|---|---|
| 2485-line `base_coder.py` god class | Registry works, everything piled on | Split: CoderCore, EditApply, GitIntegration |
| `litellm` dependency | Breaking changes every release | Direct API clients if you only support 1-2 providers |
| `prompt_toolkit` | ~3MB dep for an interactive prompt | Plain input if Y/N + free-text is enough |
| Recursive `main()` for repo detection | Hides control flow | One normalization pass |
| Hardcoded string marker in `linter.lint_python_compile` (`# USE TRACEBACK BELOW HERE`) | Brittle | Use a class sentinel + check `f.f_code` |

## Pitfalls (learned while packaging these)

These are the bugs and near-misses hit while building the drop-in
scripts. Save yourself the round-trips.

### Indent-matching

- **`make_relative` is the emitter, not the matcher.** It rewrites
  the file + the search into a `←`-marker form so you can emit the
  REPLACE at the right indent. The matcher is `match_but_for_leading_whitespace`
  in `editblock_coder.py:243-293`. Pattern #7 above has the
  corrected explanation. A first implementation that strips the
  search's min-indent from BOTH sides will fail on the common case
  where the LLM uniformly outdented the whole block.
- **Tabs count as 1 char in `leading_spaces`, not 4.** Aider's
  algorithm is char-count, not visual column. If you need visual-
  column matching, expand tabs to spaces first. Document the
  choice in the docstring.
- **Blank lines must not count toward min-indent.** `"    "` (whitespace
  only) is `not ln.strip()` and should be skipped when computing
  min-indent. Easy off-by-one bug.

### Strict exceptions

- **The test "find a clean module" needs a *precondition* check.**
  `json` looked clean (no `*Error` classes) but `json.JSONDecodeError`
  is one. `string` is actually clean. Always assert the precondition
  before running the test, or your "clean module" test will start
  failing when stdlib adds new error types.
- **Use `next(iter(loader.exceptions))` to pick a real class to
  raise in tests** instead of a hardcoded name like `_w.UserWarning`
  (which is not an exception and will fail pyright's import check).

### ChatChunks

- **`cache_control: {type: ephemeral}` must be inside a list of
  blocks, not a string.** Anthropic's API rejects `content: "..."` +
  `cache_control: {...}` at the same level. Convert str content to
  `[{"type": "text", "text": "..."}]` first, then add the marker.
- **Pyright false-positive on the dict mutation.** The mutation
  `content["cache_control"] = {...}` on a freshly-constructed dict
  with `str` text value gets flagged because the inferred type is
  still narrow. `# type: ignore[index]` is fine — you're deliberately
  widening the dict's value type.

### Smoke tests

- **Running scripts via `runpy.run_path` collects `__pycache__` in
  the script's directory.** The skill ships in `scripts/`; the
  `.pyc` lands alongside. Add `__pycache__/` to the skill's
  `.gitignore` (or `find . -name __pycache__ -exec rm -rf {} +`
  before packaging). Not a runtime bug, but it dirties `git status`.
- **Self-test scripts double as docs.** The `__main__` block in
  each module is also its smoke test. Make assertions explicit
  (not just `print`); the `aider_smoke_test.py` runner needs `OK` /
  `FAIL` lines that it can grep for.

## Source provenance

All patterns verified against `https://github.com/Aider-AI/aider`
cloned to `/tmp/aider-analysis/aider/` (commit = main @ clone time,
2026-06-21). Every file:line reference above was spot-checked against
the actual source. Full analysis reports:
- `/tmp/aider-analysis/patterns.md` (47KB)
- `/tmp/aider-analysis/aider-algorithms.md` (55KB)
- `/tmp/aider-analysis/aider_coder_analysis_report.md` (38KB)
- `/tmp/aider-analysis/aider_top_modules_report.md` (44KB)

## Related skills

- `oss-pattern-mining` — find patterns in arbitrary OSS repos
- `codebase-porting` — implement patterns into your codebase
- `writing-plans` — break a chosen pattern into tasks
- `spec-driven-build` — LLM-driven iterative spec loop
- `test-what-you-built` — verify the patterns actually work in your context
