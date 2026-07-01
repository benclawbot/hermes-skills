#!/usr/bin/env python3
"""
aider_smoke_test.py — run all self-tests in this skill.

Usage:
    python3 aider_smoke_test.py            # runs all modules
    python3 aider_smoke_test.py lazy_litellm   # one module

Each module's __main__ block is exec'd in isolation. Exit 0 = all
passed; non-zero = at least one failed.
"""
from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path


SKILLS_DIR = Path(__file__).parent
MODULES = {
    "lazy_litellm": SKILLS_DIR / "lazy_litellm.py",
    "strict_exceptions": SKILLS_DIR / "strict_exceptions.py",
    "chat_chunks": SKILLS_DIR / "chat_chunks.py",
    "relative_indenter": SKILLS_DIR / "relative_indenter.py",
}


def run_one(name: str) -> bool:
    path = MODULES[name]
    print(f"\n=== {name} ({path.name}) ===")
    try:
        # Run as a standalone script
        import runpy
        runpy.run_path(str(path), run_name="__main__")
        return True
    except SystemExit as e:
        return e.code in (None, 0)
    except Exception:
        traceback.print_exc()
        return False


def main(args: list[str]) -> int:
    targets = args[1:] if len(args) > 1 else list(MODULES)
    results = {}
    for name in targets:
        if name not in MODULES:
            print(f"unknown module: {name}")
            print(f"available: {', '.join(MODULES)}")
            return 2
        results[name] = run_one(name)

    print("\n=== summary ===")
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {name}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
