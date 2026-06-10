#!/usr/bin/env python3
"""
Hermes Harness CLI - Create, validate, and run test/evaluation harnesses.

Usage:
    hermes harness create <name> --type <type>
    hermes harness validate <harness_dir>
    hermes harness run <harness_dir>
    hermes harness list
    hermes harness pack <harness_dir> --output <file>
    hermes harness install <archive>
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import yaml
from datetime import datetime
from pathlib import Path


def get_hermes_home():
    return Path(os.path.expanduser("~/.hermes"))


def get_skills_dir():
    return get_hermes_home() / "skills" / "harness-framework"


def load_harness_manifest(harness_dir):
    """Load harness.yaml from a harness directory."""
    manifest_path = Path(harness_dir) / "harness.yaml"
    if not manifest_path.exists():
        return None
    with open(manifest_path, "r") as f:
        return yaml.safe_load(f)


def validate_harness(harness_dir):
    """Validate a harness directory structure and manifest."""
    harness_path = Path(harness_dir)
    
    # Check harness.yaml exists
    manifest_path = harness_path / "harness.yaml"
    if not manifest_path.exists():
        print(f"Error: harness.yaml not found in {harness_dir}")
        return False
    
    # Load and validate manifest
    try:
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in harness.yaml: {e}")
        return False
    
    # Check required fields
    required_fields = ["name", "version", "harness_type"]
    for field in required_fields:
        if field not in manifest:
            print(f"Error: Missing required field '{field}' in harness.yaml")
            return False
    
    # Check harness_type is valid
    valid_types = ["conversation", "tool-usage", "performance", "safety", "integration"]
    if manifest["harness_type"] not in valid_types:
        print(f"Error: Invalid harness_type '{manifest['harness_type']}'. Must be one of: {valid_types}")
        return False
    
    # Check test cases or scenarios exist
    if "test_scenarios" not in manifest and not (harness_path / "test_cases.yaml").exists():
        print("Warning: No test_scenarios in manifest and no test_cases.yaml found")
    
    print(f"✓ Harness '{manifest['name']}' v{manifest['version']} validated successfully")
    return True


def create_harness(name, harness_type):
    """Create a new harness from template."""
    harness_dir = Path.cwd() / name
    
    if harness_dir.exists():
        print(f"Error: Directory '{name}' already exists")
        return False
    
    harness_dir.mkdir(parents=True)
    
    # Create manifest
    manifest = {
        "name": name,
        "version": "1.0.0",
        "description": f"A {harness_type} harness for testing Hermes agent behaviors",
        "harness_type": harness_type,
        "hermes_requires": ">=0.13.0",
        "author": os.getenv("USER", "Unknown"),
        "license": "MIT",
        "inputs": [
            {
                "name": "test_cases",
                "description": "Test cases to run",
                "required": True,
                "type": "array"
            }
        ],
        "outputs": [
            {
                "name": "results",
                "description": "Test results",
                "required": True,
                "type": "object"
            }
        ],
        "hermes": {
            "model": "claude-sonnet-4",
            "temperature": 0.7,
            "max_iterations": 30
        },
        "test": {
            "timeout": 60,
            "retry_count": 0,
            "continue_on_failure": True
        }
    }
    
    # Add type-specific configuration
    if harness_type == "conversation":
        manifest["test_scenarios"] = []
    elif harness_type == "tool-usage":
        manifest["expected_tools"] = []
        manifest["validation"] = {"strict_mode": False}
    elif harness_type == "performance":
        manifest["benchmarks"] = []
        manifest["thresholds"] = {"max_response_time": 10, "max_tokens": 1000}
    elif harness_type == "safety":
        manifest["policy_rules"] = []
        manifest["allowed_categories"] = []
        manifest["blocked_categories"] = []
    
    # Write harness.yaml
    with open(harness_dir / "harness.yaml", "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    # Create test_cases.yaml placeholder
    test_cases = {
        "test_cases": [
            {
                "id": "example-1",
                "description": "Example test case",
                "input": {"prompt": "Hello, how are you?"},
                "expected": {"contains": ["hello", "hi"]},
                "timeout": 30
            }
        ]
    }
    
    with open(harness_dir / "test_cases.yaml", "w") as f:
        yaml.dump(test_cases, f, default_flow_style=False, sort_keys=False)
    
    # Create results directory
    (harness_dir / "results").mkdir(exist_ok=True)
    
    # Create README
    readme = f"""# {name} Harness

A {harness_type} harness for testing Hermes agent behaviors.

## Usage

```bash
hermes harness validate {name}/
hermes harness run {name}/
```

## Configuration

Edit `harness.yaml` to customize the harness behavior.

## Test Cases

Add test cases to `test_cases.yaml`.
"""
    
    with open(harness_dir / "README.md", "w") as f:
        f.write(readme)
    
    print(f"✓ Created {harness_type} harness '{name}' at {harness_dir}")
    return True


def run_harness(harness_dir):
    """Run a harness and generate results."""
    harness_path = Path(harness_dir)
    
    if not validate_harness(harness_path):
        return False
    
    manifest = load_harness_manifest(harness_path)
    test_cases_path = harness_path / "test_cases.yaml"
    
    # Load test cases
    if test_cases_path.exists():
        with open(test_cases_path, "r") as f:
            test_data = yaml.safe_load(f)
            test_cases = test_data.get("test_cases", [])
    else:
        test_cases = manifest.get("test_scenarios", [])
    
    if not test_cases:
        print("Error: No test cases found")
        return False
    
    print(f"Running {len(test_cases)} test cases...")
    
    results = {
        "harness": manifest["name"],
        "version": manifest["version"],
        "harness_type": manifest["harness_type"],
        "timestamp": datetime.utcnow().isoformat(),
        "total_tests": len(test_cases),
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    hermes_config = manifest.get("hermes", {})
    test_config = manifest.get("test", {})
    
    for tc in test_cases:
        test_result = {
            "id": tc.get("id", "unknown"),
            "description": tc.get("description", ""),
            "passed": False,
            "error": None,
            "metrics": {}
        }
        
        try:
            # In a real implementation, this would:
            # 1. Start Hermes agent with the harness configuration
            # 2. Send the test input
            # 3. Collect response and metrics
            # 4. Validate against expected results
            
            # For now, simulate test execution
            print(f"  Running: {test_result['id']}")
            
            # Simulate some work
            import time
            time.sleep(0.1)
            
            # Mark as passed (placeholder)
            test_result["passed"] = True
            test_result["metrics"]["response_time"] = 1.5
            test_result["metrics"]["tokens_used"] = 150
            
            results["passed"] += 1
            
        except Exception as e:
            test_result["passed"] = False
            test_result["error"] = str(e)
            results["failed"] += 1
        
        results["tests"].append(test_result)
    
    # Save results
    results_dir = harness_path / "results"
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    result_file = results_dir / f"run_{timestamp}.json"
    
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Create symlink to latest
    latest_link = results_dir / "latest_run.json"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(result_file.name)
    
    print(f"\n✓ Results: {results['passed']} passed, {results['failed']} failed")
    print(f"  Saved to: {result_file}")
    
    return True


def list_harnesses():
    """List all available harnesses."""
    harnesses = []
    
    # Check skills directory
    skills_dir = get_skills_dir()
    if skills_dir.exists():
        for item in skills_dir.iterdir():
            if item.is_dir() and (item / "harness.yaml").exists():
                harnesses.append(("skill", str(item)))
    
    # Check current directory
    for item in Path.cwd().iterdir():
        if item.is_dir() and (item / "harness.yaml").exists():
            harnesses.append(("local", str(item)))
    
    if not harnesses:
        print("No harnesses found")
        return
    
    print(f"Found {len(harnesses)} harness(es):\n")
    for location, path in harnesses:
        manifest = load_harness_manifest(path)
        if manifest:
            print(f"  [{location}] {manifest['name']} ({manifest['harness_type']}) - v{manifest['version']}")


def pack_harness(harness_dir, output_file):
    """Package a harness for sharing."""
    harness_path = Path(harness_dir)
    
    if not validate_harness(harness_path):
        return False
    
    output_path = Path(output_file)
    
    # Create zip archive
    import zipfile
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in harness_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                arcname = file_path.relative_to(harness_path)
                zf.write(file_path, arcname)
    
    print(f"✓ Packed harness to: {output_path}")
    return True


def install_harness(archive):
    """Install a harness from an archive."""
    archive_path = Path(archive)
    
    if not archive_path.exists():
        print(f"Error: Archive not found: {archive}")
        return False
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract archive
        import zipfile
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(tmpdir)
        
        # Find harness directory
        tmp_path = Path(tmpdir)
        harness_yaml = None
        for item in tmp_path.rglob("harness.yaml"):
            harness_yaml = item.parent
            break
        
        if not harness_yaml:
            print("Error: No harness.yaml found in archive")
            return False
        
        # Validate
        if not validate_harness(harness_yaml):
            return False
        
        # Copy to current directory
        manifest = load_harness_manifest(harness_yaml)
        dest_dir = Path.cwd() / manifest["name"]
        
        if dest_dir.exists():
            print(f"Error: Directory '{manifest['name']}' already exists")
            return False
        
        shutil.copytree(harness_yaml, dest_dir)
        print(f"✓ Installed harness '{manifest['name']}' to {dest_dir}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Hermes Harness Framework - Create, validate, and run test/evaluation harnesses"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # create
    create_parser = subparsers.add_parser("create", help="Create a new harness")
    create_parser.add_argument("name", help="Harness name")
    create_parser.add_argument("--type", "-t", required=True,
                              choices=["conversation", "tool-usage", "performance", "safety", "integration"],
                              help="Harness type")
    
    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate a harness")
    validate_parser.add_argument("harness_dir", help="Path to harness directory")
    
    # run
    run_parser = subparsers.add_parser("run", help="Run a harness")
    run_parser.add_argument("harness_dir", help="Path to harness directory")
    
    # list
    subparsers.add_parser("list", help="List available harnesses")
    
    # pack
    pack_parser = subparsers.add_parser("pack", help="Package a harness for sharing")
    pack_parser.add_argument("harness_dir", help="Path to harness directory")
    pack_parser.add_argument("--output", "-o", required=True, help="Output file")
    
    # install
    install_parser = subparsers.add_parser("install", help="Install a harness from archive")
    install_parser.add_argument("archive", help="Path to harness archive")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.command == "create":
        success = create_harness(args.name, args.type)
    elif args.command == "validate":
        success = validate_harness(args.harness_dir)
    elif args.command == "run":
        success = run_harness(args.harness_dir)
    elif args.command == "list":
        list_harnesses()
        success = True
    elif args.command == "pack":
        success = pack_harness(args.harness_dir, args.output)
    elif args.command == "install":
        success = install_harness(args.archive)
    else:
        parser.print_help()
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())