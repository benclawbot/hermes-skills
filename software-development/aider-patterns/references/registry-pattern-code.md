# Registry / Plugin Pattern — Drop-in Code

Aider reference: `aider/coders/__init__.py` (34 lines) + `aider/coders/base_coder.py:88-201`.

## The pattern in 50 lines

```python
# plugins/__init__.py
from typing import Any, List, Type

class Plugin:
    """Base class — every plugin carries 3 things."""
    name: str = None          # public identifier (matches CLI choices)
    config: Any = None        # strategy-specific config (prompts, etc.)
    def execute(self, **kw): ...
    def cleanup(self): ...

# Import every concrete plugin so __subclasses__() sees them
from .plugin_a import PluginA
from .plugin_b import PluginB

__all__: List[Type[Plugin]] = [PluginA, PluginB]
```

```python
# plugins/base.py
from typing import Type, List, Optional
from . import Plugin, __all__ as _registry

class PluginRegistry:
    _registry: List[Type[Plugin]] = _registry

    @classmethod
    def create(cls, name: str, **kwargs) -> Plugin:
        for sub in cls._registry:
            if getattr(sub, "name", None) == name:
                return sub(**kwargs)
        valid = [getattr(s, "name", "?") for s in cls._registry
                 if getattr(s, "name", None)]
        raise ValueError(f"Unknown plugin: {name}. Valid: {valid}")

    @classmethod
    def available(cls) -> List[str]:
        return [s.name for s in cls._registry if getattr(s, "name", None)]
```

```python
# your_cli.py
import argparse
from plugins.base import PluginRegistry

parser = argparse.ArgumentParser()
parser.add_argument(
    "--plugin",
    choices=PluginRegistry.available(),  # dynamic, never stale
    required=True,
)
args = parser.parse_args()

p = PluginRegistry.create(args.plugin, model=...)
p.execute(model=...)
p.cleanup()
```

## How Aider uses this

```python
# aider/coders/__init__.py:18-34
from .architect_coder import ArchitectCoder
from .ask_coder import AskCoder
from .base_coder import Coder
from .editblock_coder import EditBlockCoder
# ... 12 more

__all__ = [
    HelpCoder, AskCoder, Coder,
    EditBlockCoder, EditBlockFencedCoder, WholeFileCoder,
    PatchCoder, UnifiedDiffCoder, UnifiedDiffSimpleCoder,
    ArchitectCoder,
    EditorEditBlockCoder, EditorWholeFileCoder, EditorDiffFencedCoder,
    ContextCoder,
]
```

```python
# aider/coders/base_coder.py:190-201 — the factory
@classmethod
def create(cls, main_model, edit_format=None, ...):
    import aider.coders as coders
    if not edit_format:
        edit_format = main_model.edit_format

    for coder in coders.__all__:
        if hasattr(coder, "edit_format") and coder.edit_format == edit_format:
            return coder(main_model, io, **kwargs)
    valid = [c.edit_format for c in coders.__all__ if hasattr(c, "edit_format")]
    raise UnknownEditFormat(edit_format, valid)
```

```python
# aider/args.py:46-54 — CLI choices derived from registry
from aider import coders as _aider_coders
edit_format_choices = sorted({
    c.edit_format for c in _aider_coders.__all__
    if hasattr(c, "edit_format") and c.edit_format is not None
})
```

## Why this works

1. **Adding a plugin is 2 files** — one class, add to `__all__`. Nothing else.
2. **CLI choices never go stale** — derived from the registry at parser creation time.
3. **Adding state to the factory is trivial** — `create()` can take any kwargs and pass them through.
4. **Subclasses can extend** — `ArchitectCoder(AskCoder)` is just inheritance. The factory still finds it via the same loop.

## When to extend with hooks

For complex lifecycles, add hooks to the base class:

```python
class Plugin:
    name: str = None
    config: Any = None

    def pre_execute(self, ctx): ...      # before main work
    def execute(self, ctx): ...           # main work
    def post_execute(self, ctx): ...      # after, even on failure
    def on_error(self, ctx, exc): ...     # exception hook
    def cleanup(self): ...                # always called
```

The registry doesn't change — subclasses just override the hooks they need.

## Gotcha: circular imports

If your registry needs to know about ALL plugins at import time, and
plugins need to import from the registry's module, you have a cycle.

Fix: put the registry in a separate module (`plugins/registry.py`) that
imports NOTHING from plugins. Have `plugins/__init__.py` import the
registry + each plugin. Plugins import from `plugins.base` only.

## Gotcha: subclasses discovered at import time

`__subclasses__()` is populated at class definition time. If a plugin
is defined conditionally (e.g., only if `import x` succeeds), the
registry won't see it on systems without `x`. Use `__all__` (explicit)
instead of `__subclasses__()` if you need conditional plugins.
