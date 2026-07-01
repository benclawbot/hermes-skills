# Aider Case Study — verified pattern set

Source: `/tmp/aider-analysis/aider/` (cloned `--depth 1` from
`https://github.com/Aider-AI/aider`). 147 .py files, ~13k LOC of core,
mature (v0.x with extensive HISTORY.md). LLM-tooling CLI: wraps litellm
to edit files in a git repo. Class: terminal AI pair-programming tool.

This file is the **verification set** — every pattern below was spot-
checked against the source during this session. Future sessions using
`oss-pattern-mining` can read this as a worked example.

---

## Top 3 (highest-impact, steal these first)

### 1. Edit-format coder as a registry

The killer pattern. `aider/coders/__init__.py` (34 lines) declares a
flat `__all__` of coder classes. Each subclass carries exactly three
knobs: `edit_format` (str), `gpt_prompts` (instance), and
`get_edits()` / `apply_edits()` methods. Selection is data-driven
(`base_coder.py:190-201`): iterate the registry, match by
`class.edit_format`. The CLI's `--edit-format` choices are derived
from the same registry (`args.py:46-54`) — adding a coder is 2 files,
no other plumbing.

```python
# aider/coders/__init__.py:18-34
__all__ = [
    HelpCoder, AskCoder, Coder,
    EditBlockCoder, EditBlockFencedCoder, WholeFileCoder,
    PatchCoder, UnifiedDiffCoder, UnifiedDiffSimpleCoder,
    ArchitectCoder, EditorEditBlockCoder, EditorWholeFileCoder,
    EditorDiffFencedCoder, ContextCoder,
]

# aider/coders/base_coder.py:190-201
for coder in coders.__all__:
    if hasattr(coder, "edit_format") and coder.edit_format == edit_format:
        return coder(main_model, io, **kwargs)
```

**Apply when**: any LLM tool with multiple prompt/output conventions
(edit grammars, output schemas, model-specific formats).

### 2. PageRank repo map

`aider/repomap.py:372-525` — three-phase:

1. Tree-sitter extracts `(file, symbol, definition, references)` triples
2. Build `MultiDiGraph`, run `nx.pagerank()` with personalization
   (chat files + path-component-matched mentioned identifiers get
   boosted — `repomap.py:381-446`)
3. Binary-search prefix length of ranked tags until tokenized output is
   within ±15% of budget (`repomap.py:676-706`)

Caching by mtime, version-tagged cache dir `CACHE_VERSION = 3/4`.
Reproducible, scales to big repos, *actually relevant* to the prompt.

**Apply when**: any "give the LLM project context" feature. The
implementation is ~200 LOC. `networkx` is a heavy dep — consider
vendoring a 50-LOC bespoke ranker if you need to drop it.

### 3. YAML-backed capability registry for models

`aider/models.py:127-158` defines `ModelSettings` dataclass + loads from
`aider/resources/model-settings.yml`:

```yaml
- name: claude-sonnet-4-6
  edit_format: diff
  weak_model_name: claude-haiku-4-5
  use_repo_map: true
  cache_control: true
  accepts_settings: [thinking_tokens, reasoning_effort]
```

Three-tier lookup (`models.py:385-435`): exact YAML match → substring
heuristics in `apply_generic_model_settings()` → litellm defaults for
token limits. User can override per-model via `aider/extra_params`
entry that deep-merges last.

**Apply when**: any project that hits "support a new LLM" repeatedly.
YAML > string-matching ifs.

---

## Mid-tier (5 patterns worth adopting)

### 4. "Did you mean" diff fallback on failed edits

`aider/coders/editblock_coder.py:82-124`: when a SEARCH block fails to
match exactly, the error includes the closest fuzzy match using
`difflib.SequenceMatcher` (`find_similar_lines`, threshold 0.6).
Filename matching has 4-tier fallback — exact → basename → fuzzy 0.8 →
first-with-extension → first (`editblock_coder.py:560-599`).

Saves "typo in filename = silent failure" / "model hallucinated a path"
from being dead ends.

### 5. Reflection loop with bounded retry

`aider/coders/base_coder.py:924-944`:

```python
def run_one(self, user_message, preproc):
    self.init_before_message()
    message = preproc and self.preproc_user_input(user_message) or user_message
    while message:
        self.reflected_message = None
        list(self.send_message(message))
        if not self.reflected_message:
            break
        if self.num_reflections >= self.max_reflections:  # 3
            return
        self.num_reflections += 1
        message = self.reflected_message
```

`send_message` wraps `litellm.completion` with exponential backoff +
reflection-after-error: failed edits feed back as a new user turn.
`max_reflections = 3` hard caps the loop.

**Apply when**: any "LLM produces output validated against reality"
loop.

### 6. SwitchCoder exception for mid-session swaps

`aider/commands.py:30-33`:

```python
class SwitchCoder(Exception):
    def __init__(self, placeholder=None, **kwargs):
        self.kwargs = kwargs
        self.placeholder = placeholder
```

When `/model` or `/editor` runs, it raises `SwitchCoder`. Outer loop
catches, builds a new Coder with `from_coder=self` to carry state,
continues. No state machine, no half-built objects. 48 LOC
(`architect_coder.py:36-44`) to swap from planner → editor model
mid-session.

**Apply when**: any tool where the user can change the active "agent"
mid-flow without losing context.

### 7. Per-action argparse formatter for `--help` in 3 formats

`aider/args_formatter.py`: three `argparse.HelpFormatter` subclasses
(`DotEnvFormatter`, `YamlHelpFormatter`, `MarkdownHelpFormatter`) share
a metadata channel — `action.env_var = "OPENAI_API_KEY"` set as a
custom attribute on the Action. Result: `aider --help` renders as
terminal, YAML, Markdown, or `.env` template.

**Apply when**: any CLI tool with argparse help that's barely usable.

### 8. Lazy litellm import

`aider/llm.py` is ~47 LOC; its main job is the lazy import. Coder base
class only imports litellm when actually creating a model. `/help`,
`--version`, onboarding skip it entirely. Saves ~1.5s startup.

**Apply when**: any tool with a heavy ML client. Move imports inside
functions.

---

## Smaller defensive tricks

- `choose_fence()` (`base_coder.py:609-635`) — pick fence chars not
  present in file content. Prevents model ` ``` ` blocks from colliding
  with code in the user's repo.
- `RelativeIndenter` rewrites a file as indent-relative blocks so
  SEARCH/REPLACE is invariant to leading-whitespace drift.
- `oslex.join` for OS-correct shell quoting (Windows quirks).
- Triple-format `.env`/`.yaml`/`markdown` config-file parsers via
  `configargparse`.
- `report_uncaught_exceptions()` installs `sys.excepthook` that posts
  tracebacks to a file — survives even when the CLI crashes.
- `guessed_wrong_repo` (`main.py:69-85`) — recursive `main()` if
  initial git-root guess was wrong. Analytics event `"Recursing with
  correct repo"` so you see it in telemetry.
- Hex-prefix sampling (`aider/analytics.py`): `uuid.uuid4().hex[:4] <
  "8000"` → 50% cohort, stable across sessions because UUID is
  persisted in `~/.aider/analytics.json`. Deterministic opt-in cohort
  assignment with no manual flag.
- Double-`^C`-to-quit with `thresh=2s` (`base_coder.py:986-1000`).
- Lazy-install extra requirements via `check_pip_install_extra("playwright")`.
- Write-with-retry-on-PermissionError (`io.py:478-507`): exponential
  backoff, 5 tries. Handles editor windows, AV scanners, Dropbox locks.
- `aider_commit_hashes` set gates `/undo` to aider's own commits, never
  user commits. `check_for_dirty_commit` queues edits before applying
  if the working tree has unrelated user changes.
- `ConfirmGroup` (`io.py:81-85`) — batch Y/N/A/S/D for fan-out actions
  (12 URLs, 8 file ops) so the user answers once.
- Background-thread `ChatSummary` with optimistic concurrency
  (apply result only if no new messages arrived in meantime).

---

## Packaging notes

`pyproject.toml`:

- Optional-deps groups: `dev`, `help`, `browser`, `playwright` — each
  lazy-loaded. The `help` and `browser` groups use `importlib.resources`
  for resources.
- `setuptools_scm` writes version to `aider/_version.py`.
- `auto_env_var_prefix = "AIDER_"` in configargparse — every flag is
  also an env var with zero boilerplate.

## What NOT to copy

- **Litellm dependency** — god-module with breaking changes every
  release. Target 1-2 providers directly if you can.
- **prompt_toolkit** — powerful but ~3MB dep for an interactive prompt.
  Plain input is fine for Y/N + free-text.
- **The 2485-line `base_coder.py`** — God class. Registry works but
  everything else piled on. Split into `CoderCore`, `EditApply`,
  `GitIntegration`, `FileWatcher` if starting fresh.
- **Recursive `main()` for repo detection** (`main.py:716-720`) — works
  but hides control flow. A single normalizer pass is clearer.

---

## Concrete takeaways ranked

If you only adopt 3: **(1) coder registry, (2) PageRank repo map,
(3) YAML model registry.** Each collapses a hard multi-file feature
into 50-200 LOC. Everything else is polish.
