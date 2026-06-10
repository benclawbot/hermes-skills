# Pyright — Static Type Checking for Python

Installed: `~/.hermes/hermes-agent/.venv/bin/pyright` (v1.1.410)
Installed via: `uv pip install --python ~/.hermes/hermes-agent/.venv/bin/python3 pyright`

## When to Use

- Before committing complex Python code (catches type errors before execution)
- After implementing a feature with complex function signatures
- When working on hermes-agent internals (large Python codebase)
- When the user says "check this code" or "run type checking"

## How to Run

```bash
# Full project check
/home/thomas/Desktop/hermes-agent/.venv/bin/pyright

# Single file
/home/thomas/Desktop/hermes-agent/.venv/bin/pyright src/some_file.py

# Package-level
/home/thomas/Desktop/hermes-agent/.venv/bin/pyright src/module/

# With config (pyproject.toml / pyrightconfig.json)
/home/thomas/Desktop/hermes-agent/.venv/bin/pyright --project .
```

## Expected Workflow

After implementing complex Python code and before running requesting-code-review:

```bash
# Run pyright against the changed files
PYRIGHT="/home/thomas/Desktop/hermes-agent/.venv/bin/pyright"
$PYRIGHT src/feature.py
# If errors → fix before committing
```

## Integration with requesting-code-review

Pyright should run as part of Step 3 (linting and type checking) in requesting-code-review. Add after ruff:

```bash
# Python type checking (run only if installed)
which pyright && pyright . --ignore-missing-imports 2>&1 | tail -10
```

## Key Error Types

- `reportUnknownVariableType` — variable has no type annotation
- `reportUnknownMemberType` — method/property type unclear
- `reportImportCycles` — circular imports
- `reportMissingTypeStubs` — missing type stubs for external packages

## Limitations

- Requires type annotations to be effective (unannotated code passes silently)
- Works best with full project context (run from project root with pyproject.toml)
- Not a substitute for runtime tests — catches type errors, not logic errors