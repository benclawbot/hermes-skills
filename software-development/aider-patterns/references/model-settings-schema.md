# Model Settings YAML Schema

Aider reference: `aider/resources/model-settings.yml` (357 entries, 86KB)
+ `aider/models.py:127-158` (`ModelSettings` dataclass).

## Top-level fields per entry

| Field | Type | Meaning |
|---|---|---|
| `name` | str (required) | Model identifier. Exact match against `--model` arg. |
| `edit_format` | str | Which Coder subclass to use. One of: `whole`, `diff`, `udiff`, `diff-fenced`, `patch`, `editor-diff`, `editor-whole`, `architect`. |
| `weak_model_name` | str | Model to use for cheap tasks (commit messages, summarization). |
| `editor_model_name` | str | Model used in architect mode to translate plain-text instructions to edits. |
| `editor_edit_format` | str | Edit format for the editor model. |
| `use_repo_map` | bool | Inject the repo map into the system prompt. |
| `lazy` | bool | Defer sending the system prompt until needed. |
| `overeager` | bool | Add hint about eager completion (Claude 3.7+, GPT-5 codex). |
| `reminder` | str | Where to inject the post-turn reminder: `user` (last user turn) or `sys` (system prompt). |
| `examples_as_sys_msg` | bool | Send few-shot examples as system message instead of user/assistant turns. |
| `cache_control` | bool | Enable Claude prompt caching (insert `cache_control: ephemeral` markers). |
| `caches_by_default` | bool | (DeepSeek) Always cache. |
| `use_temperature` | bool/float | Whether to send temperature. `false` for o1/o3/GPT-5. |
| `streaming` | bool | Whether the model supports streaming. |
| `system_prompt_prefix` | str | Prefix prepended to the system prompt (e.g., `"Formatting re-enabled. "` for o1). |
| `reasoning_tag` | str | XML tag wrapping reasoning content to strip (e.g., `"think"` for DeepSeek R1). |
| `accepts_settings` | list | Settings the model accepts in API call: `["thinking_tokens"]`, `["reasoning_effort"]`. |
| `extra_params` | dict | Passed through to litellm. Keys: `max_tokens`, `extra_headers`, `temperature`, `include_reasoning`. |

## Resolution order

When `Model(model_name)` is called (`aider/models.py:385-435`):

1. **Exact match** in `MODEL_SETTINGS` list. Copy all fields to `self`.
2. **Substring heuristics** in `apply_generic_model_settings()` for new releases:
   ```python
   if "gpt-4.1" in model:
       self.edit_format = "diff"
       self.use_repo_map = True
       self.reminder = "sys"
       # ...
       return
   ```
3. **Defaults**: edit_format=`whole`, use_repo_map=False, streaming=True, etc.
4. **`aider/extra_params`** (synthetic entry) deep-merges into `extra_params` dict.

User can override per-model via `.aider.model.settings.yml` in home → repo → cwd (last wins).

## Example entries

```yaml
# Claude 3.7 Sonnet — uses prompt caching + thinking tokens
- name: anthropic/claude-3-7-sonnet-20250219
  overeager: true
  edit_format: diff
  weak_model_name: anthropic/claude-3-5-haiku-20241022
  use_repo_map: true
  examples_as_sys_msg: true
  extra_params:
    extra_headers:
      anthropic-beta: prompt-caching-2024-07-31,pdfs-2024-09-25,output-128k-2025-02-19
    max_tokens: 64000
  cache_control: true
  editor_model_name: anthropic/claude-3-7-sonnet-20250219
  editor_edit_format: editor-diff
  accepts_settings: ["thinking_tokens"]

# o1-pro — no temperature, no streaming, prefix prompt
- name: o1-pro
  edit_format: diff
  weak_model_name: gpt-4o-mini
  use_repo_map: true
  use_temperature: false
  streaming: false
  editor_model_name: gpt-4o
  editor_edit_format: editor-diff
  system_prompt_prefix: "Formatting re-enabled. "
  accepts_settings: ["reasoning_effort"]
  examples_as_sys_msg: true

# Plain GPT-3.5 — minimal config
- name: gpt-3.5-turbo
  weak_model_name: gpt-4o-mini
  reminder: sys
```

## Schema in your own project

Drop-in minimal schema for your own model registry:

```yaml
# your_tool/models.yml
- name: gpt-4o
  edit_format: diff
  use_repo_map: true
  cache_control: false
  accepts_settings: []

- name: claude-sonnet-4-5
  edit_format: diff
  weak_model: claude-haiku-4-5
  use_repo_map: true
  cache_control: true
  accepts_settings: [thinking_tokens]
```

```python
# your_tool/models.py
from dataclasses import dataclass, field
from typing import List, Optional
import yaml, importlib.resources

@dataclass
class ModelSettings:
    name: str
    edit_format: str = "whole"
    weak_model: Optional[str] = None
    use_repo_map: bool = False
    cache_control: bool = False
    accepts_settings: List[str] = field(default_factory=list)
    extra_params: dict = field(default_factory=dict)

MODEL_SETTINGS: List[ModelSettings] = []
with importlib.resources.open_text("your_tool.resources", "models.yml") as f:
    for entry in yaml.safe_load(f):
        MODEL_SETTINGS.append(ModelSettings(**entry))


def get_settings(model_name: str) -> ModelSettings:
    for ms in MODEL_SETTINGS:
        if ms.name == model_name:
            return ms
    # Fall through to substring heuristics or defaults
    return ModelSettings(name=model_name)
```
