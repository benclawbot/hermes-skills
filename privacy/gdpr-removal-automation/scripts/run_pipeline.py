#!/usr/bin/env python3
"""
run_pipeline.py — Orchestrate the full GDPR removal pipeline.

Usage:
    python3 run_pipeline.py --name "Thomas Schmoele" --email t@email.com --output ./gdpr_results/

Steps:
    1. person_search.py   — Discover which brokers hold data
    2. optout_discovery.py — Find opt-out URLs
    3. removal_request.py  — File removal requests
"""

import argparse
import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime


def run(script_name: str, args: list, cwd: Path) -> int:
    script = Path(__file__).parent / script_name
    cmd = ["python3", str(script)] + args
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run full GDPR removal pipeline")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", default="")
    parser.add_argument("--phone", default="")
    parser.add_argument("--output", default="./gdpr_results")
    parser.add_argument("--skip-search", action="store_true", help="Skip person_search (use existing brokers_found.csv)")
    parser.add_argument("--skip-optout", action="store_true", help="Skip optout_discovery")
    parser.add_argument("--skip-removal", action="store_true", help="Skip removal_request")
    args = parser.parse_args()

    base_dir = Path(args.output)
    base_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = Path(__file__).parent

    summary = {
        "person": args.name,
        "email": args.email,
        "started": datetime.now().isoformat(),
        "steps": [],
    }

    # Step 1: Person search
    brokers_csv = base_dir / "brokers_found.csv"
    if args.skip_search and brokers_csv.exists():
        print("[SKIP] person_search — using existing brokers_found.csv")
    else:
        print("\n=== STEP 1: Discover which brokers hold data ===")
        rc = run("person_search.py", [
            "--name", args.name,
            "--email", args.email,
            "--phone", args.phone,
            "--output", str(brokers_csv),
            "--method", "both",
        ], cwd=scripts_dir)
        summary["steps"].append({"step": "person_search", "rc": rc, "output": str(brokers_csv)})
        if rc != 0:
            print(f"[WARN] person_search exited with code {rc}")

    # Step 2: Opt-out discovery
    optout_csv = base_dir / "optout_urls.csv"
    if args.skip_optout and optout_csv.exists():
        print("[SKIP] optout_discovery — using existing optout_urls.csv")
    elif not brokers_csv.exists():
        print("[SKIP] optout_discovery — no brokers_found.csv")
    else:
        print("\n=== STEP 2: Discover opt-out URLs ===")
        rc = run("optout_discovery.py", [
            "--input", str(brokers_csv),
            "--output", str(optout_csv),
        ], cwd=scripts_dir)
        summary["steps"].append({"step": "optout_discovery", "rc": rc, "output": str(optout_csv)})

    # Step 3: File removal requests
    removal_csv = base_dir / "removal_requests.csv"
    if args.skip_removal:
        print("[SKIP] removal_request")
    elif not optout_csv.exists():
        print("[SKIP] removal_request — no optout_urls.csv")
    else:
        print("\n=== STEP 3: File removal requests ===")
        rc = run("removal_request.py", [
            "--input", str(optout_csv),
            "--output", str(removal_csv),
            "--method", "gdpr",
            "--person-name", args.name,
            "--person-email", args.email,
        ], cwd=scripts_dir)
        summary["steps"].append({"step": "removal_request", "rc": rc, "output": str(removal_csv)})

    summary["completed"] = datetime.now().isoformat()
    summary_path = base_dir / "pipeline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== Pipeline complete ===")
    print(f"Results in: {base_dir}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())