#!/usr/bin/env python3
"""Verify all .csl policy files in skills/csl-policy/policies/ and ~/.hermes/policies/"""
import subprocess
import sys
from pathlib import Path

SKILL_POLICIES = Path(__file__).parent.parent / "policies"
USER_POLICIES = Path.home() / ".hermes" / "policies"

def verify_file(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "chimera_core.cli", "verify", str(path)],
        capture_output=True, text=True
    )
    return result.returncode == 0

def main():
    all_ok = True
    for policy_dir in [SKILL_POLICIES, USER_POLICIES]:
        if not policy_dir.exists():
            continue
        for csl in sorted(policy_dir.glob("*.csl")):
            ok = verify_file(csl)
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {csl.name}")
            if not ok:
                all_ok = False

    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
