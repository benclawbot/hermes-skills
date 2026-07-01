#!/usr/bin/env python3
"""
lazy_litellm.py — defer the litellm import (saves ~1.5s startup).

Aider reference: aider/llm.py:21-45
Source: https://github.com/Aider-AI/aider (cloned to /tmp/aider-analysis/aider/)

Drop-in usage:

    # your_tool/llm.py
    from aider_patterns.scripts.lazy_litellm import LazyProxy, configure

    litellm = LazyProxy("litellm",
                        on_load=lambda m: setattr(m, "drop_params", True))

    # any other module:
    from .llm import litellm
    response = litellm.completion(model="gpt-4o", messages=[...])

First attribute access triggers the real import + on_load callback.
Subsequent accesses hit the cached module.

Why this matters:
- `/help`, `--version`, onboarding flows never touch litellm
- Cold start time of a CLI tool drops by 1-2 seconds
- Same pattern works for any heavy ML client (transformers, torch,
  tensorflow, openai, anthropic)
"""
from __future__ import annotations

import importlib
from typing import Any, Callable, Optional


class LazyProxy:
    """Proxy that defers module import until first attribute access."""

    def __init__(self, module_name: str, on_load: Optional[Callable[[Any], None]] = None):
        self._module_name = module_name
        self._on_load = on_load
        self._module: Optional[Any] = None

    def _load(self) -> Any:
        if self._module is None:
            self._module = importlib.import_module(self._module_name)
            if self._on_load is not None:
                self._on_load(self._module)
        return self._module

    def __getattr__(self, name: str) -> Any:
        # _module_name / _module / _on_load are looked up via __dict__ first
        # (Python data model), so this only fires for "external" attrs.
        return getattr(self._load(), name)

    def __repr__(self) -> str:
        loaded = self._module is not None
        return f"<LazyProxy {self._module_name} {'loaded' if loaded else 'unloaded'}>"

    def reset(self) -> None:
        """Force the proxy to re-import. Useful for tests."""
        self._module = None


def configure(module_name: str, **defaults: Any) -> LazyProxy:
    """Build a proxy that applies default attribute values on first load.

    Convenience wrapper. Example:

        litellm = configure(
            "litellm",
            drop_params=True,
            suppress_debug_info=True,
            set_verbose=False,
        )
    """
    def on_load(m: Any) -> None:
        for k, v in defaults.items():
            setattr(m, k, v)
    return LazyProxy(module_name, on_load=on_load)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time
    import sys

    print(f"Python startup overhead: {sys.version_info[:2]}")

    # Time a non-lazy import
    t0 = time.perf_counter()
    import importlib
    mod = importlib.import_module("json")  # cheap but illustrative
    t1 = time.perf_counter()
    print(f"Direct import:           {(t1 - t0) * 1000:.2f}ms  ({mod.__name__})")

    # Time a lazy proxy that never loads
    proxy = LazyProxy("json")
    t0 = time.perf_counter()
    _ = proxy  # no attribute access = no import
    t1 = time.perf_counter()
    print(f"Proxy, no access:        {(t1 - t0) * 1000:.2f}ms  ({proxy!r})")

    # Time the first attribute access
    t0 = time.perf_counter()
    dumps = proxy.dumps
    t1 = time.perf_counter()
    print(f"First attribute access:  {(t1 - t0) * 1000:.2f}ms  ({dumps.__module__}.dumps)")

    # Subsequent accesses hit the cache
    t0 = time.perf_counter()
    for _ in range(1000):
        proxy.dumps({"x": 1})
    t1 = time.perf_counter()
    print(f"1000 cached accesses:   {(t1 - t0) * 1000:.2f}ms total")

    # reset() re-imports
    proxy.reset()
    assert proxy._module is None
    print("reset() works:", proxy)
