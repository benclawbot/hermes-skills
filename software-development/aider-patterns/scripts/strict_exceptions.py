#!/usr/bin/env python3
"""
strict_exceptions.py — fail loudly when upstream adds new *Error classes.

Aider reference: aider/exceptions.py:60-113
Source: https://github.com/Aider-AI/aider (cloned to /tmp/aider-analysis/aider/)

The pattern: maintain a hand-curated table of every exception class you
care about (with retry policy + user-facing message). On startup,
enumerate the upstream module's `*Error` classes and crash if any are
missing from your table.

Why this matters:
- Upstream libraries grow new exception types silently
- Without an explicit table, your retry loop eats new errors as generic
  exceptions and retries forever (or never)
- A startup crash forces an explicit decision: "do I retry, do I give
  up, what do I tell the user?"

Drop-in usage:

    from aider_patterns.scripts.strict_exceptions import (
        ExceptionInfo, build_strict_loader,
    )

    # 1. Declare your table
    EXCEPTIONS = [
        ExceptionInfo("APIConnectionError", retry=True,  msg=None),
        ExceptionInfo("AuthenticationError", retry=False,
                      msg="The API provider is not able to authenticate you. Check your API key."),
        ExceptionInfo("RateLimitError",      retry=True,
                      msg="The API provider has rate limited you. Try again later."),
        ExceptionInfo("ContextWindowExceededError", retry=False, msg=None),
        ExceptionInfo("Timeout",             retry=True,
                      msg="The API provider timed out without returning a response."),
    ]

    # 2. Build a strict loader for any upstream module
    loader = build_strict_loader("litellm", EXCEPTIONS)

    # 3. Use it in your retry loop
    def call_api():
        try:
            return litellm.completion(...)
        except tuple(loader.exceptions) as exc:
            info = loader.get_ex_info(exc)
            if info.retry:
                raise  # outer retry loop handles it
            raise UserFacingError(info.msg or str(exc))

If litellm ever ships `litellm.NewfangledError`, your tool crashes at
startup with: "NewfangledError is in litellm but not in your EXCEPTIONS table".
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ExceptionInfo:
    """One row in your exception table."""
    name: str
    retry: bool
    msg: Optional[str] = None  # user-facing message; None = use str(exc)


class StrictExceptionLoader:
    """Validates your EXCEPTIONS table covers everything upstream exposes."""

    def __init__(self, module_name: str, exceptions: List[ExceptionInfo]):
        self._module_name = module_name
        self._info_by_name: Dict[str, ExceptionInfo] = {e.name: e for e in exceptions}
        self.exceptions: Dict[type, ExceptionInfo] = {}
        self._load()

    def _load(self) -> None:
        module = importlib.import_module(self._module_name)
        # Walk module attributes; pick classes that end in 'Error' and
        # actually inherit from BaseException (some libs use ErrorEventError
        # or similar non-exception classes whose name happens to end in Error).
        for var in dir(module):
            if not var.endswith("Error"):
                continue
            obj = getattr(module, var)
            if not isinstance(obj, type) or not issubclass(obj, BaseException):
                continue
            if var not in self._info_by_name:
                raise ValueError(
                    f"{var!r} is in {self._module_name} but missing from your "
                    f"EXCEPTIONS table. Add an ExceptionInfo for it (decide retry "
                    f"policy + user-facing message)."
                )
            self.exceptions[obj] = self._info_by_name[var]

    def exceptions_tuple(self) -> Tuple[type, ...]:
        """Tuple form for use in `except (...)`."""
        return tuple(self.exceptions)

    def get_ex_info(self, exc: BaseException) -> ExceptionInfo:
        return self.exceptions[exc.__class__]


def build_strict_loader(module_name: str,
                        exceptions: List[ExceptionInfo]) -> StrictExceptionLoader:
    """Convenience factory."""
    return StrictExceptionLoader(module_name, exceptions)


# ---------------------------------------------------------------------------
# Self-test (uses stdlib only; doesn't need litellm)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # stdlib has plenty of *Error classes; use a controlled example.
    EXCEPTIONS = [
        ExceptionInfo("KeyError", retry=False, msg="missing key"),
        ExceptionInfo("ValueError", retry=False, msg="bad value"),
        ExceptionInfo("FileNotFoundError", retry=False, msg="no such file"),
    ]

    # Pass case: stdlib has exactly these *Error classes (plus others
    # we'll detect as missing) — this WILL raise. Demonstrate it:
    print("Test 1: strict loader on stdlib (expected to fail)...")
    try:
        loader = build_strict_loader("builtins", EXCEPTIONS)
        print(f"  unexpectedly succeeded: {len(loader.exceptions)} exceptions")
    except ValueError as e:
        print(f"  OK — strict loader raised: {e!s:.80}...")

    # Pass case: a module with NO *Error classes
    print("\nTest 2: strict loader on a clean module (string has none)...")
    import string as _str_mod
    assert not any(
        n.endswith("Error") and isinstance(getattr(_str_mod, n), type)
        and issubclass(getattr(_str_mod, n), BaseException)
        for n in dir(_str_mod)
    ), "precondition: string module has no Error classes"
    EXCEPTIONS_EMPTY: List[ExceptionInfo] = []
    loader = build_strict_loader("string", EXCEPTIONS_EMPTY)
    print(f"  OK — no exceptions registered: {len(loader.exceptions)} entries")

    # Pass case: declare all of a small known set
    print("\nTest 3: declare every *Error in stdlib's warnings module...")
    import warnings as _w
    warn_errors = [
        ExceptionInfo(n, retry=False, msg=None)
        for n in dir(_w)
        if n.endswith("Error") and isinstance(getattr(_w, n), type)
        and issubclass(getattr(_w, n), BaseException)
    ]
    print(f"  Found {len(warn_errors)} warnings.* classes")
    loader = build_strict_loader("warnings", warn_errors)
    print(f"  OK — loader built with {len(loader.exceptions)} exceptions")

    # Use the loader
    print("\nTest 4: get_ex_info lookup...")
    # Pick any of the registered classes to raise
    sample_exc_cls = next(iter(loader.exceptions))
    try:
        raise sample_exc_cls("test")
    except BaseException as exc:
        info = loader.get_ex_info(exc)
        print(f"  caught {exc.__class__.__name__}: retry={info.retry}, msg={info.msg}")

    print("\nAll self-tests passed.")
