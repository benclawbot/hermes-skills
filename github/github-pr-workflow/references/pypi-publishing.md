# PyPI Publishing Reference

How to build and publish a Python package to PyPI, with traps specific to this environment.

## Prerequisites

- PyPI token (format: `pypi-AgEIcHlwaS5vcmcCJ...`) stored in `~/.pypirc`
- `build` and `twine` installed on the system Python (not a project venv)
- A clean repo with `pyproject.toml` at the root

## Full Workflow

### 1. Store token

```bash
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
EOF
chmod 600 ~/.pypirc
```

Also store in Hermes credentials for future sessions:
```bash
# Add to ~/.hermes/.env (if write-access allowed)
PYPI_TOKEN=pypi-YOUR-TOKEN-HERE
```

### 2. Clean + build

```bash
cd /path/to/repo
rm -rf dist/ build/ *.egg-info

# Use SYSTEM Python, not project venv (venv may lack `build` module)
# Invoke via absolute path to avoid venv shadowing
/usr/bin/python3 -m build
```

Expected output: `Successfully built agent_commit-0.1.0.tar.gz and agent_commit-0.1.0-py3-none-any.whl` in `dist/`.

### 3. Verify the artifact

```bash
# Quick smoke — extract metadata without installing
unzip -p dist/*.whl '*.dist-info/METADATA' | head -10
python3 -c "
import zipfile, sys
with zipfile.ZipFile('dist/' + [f for f in __import__('os').listdir('dist') if f.endswith('.whl')][0]) as z:
    print(z.read('agent_commit-0.1.0.dist-info/METADATA').decode()[:500])
"
```

### 4. Publish

```bash
/usr/bin/python3 -m twine upload dist/* --repository pypi
```

Expected: `View at: https://pypi.org/project/<package>/<version>/`

### 5. Immediately verify on PyPI

```bash
curl -s https://pypi.org/simple/<package>/ | head -5
curl -s "https://pypi.org/pypi/<package>/<version>/json/" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('OK:', d['info']['version'], d['info']['summary'])
"
```

---

## Traps

### uv lockfile `exclude-newer` hides newly published packages

Hermes uses `uv lock` with `exclude-newer = "7 days"` (relative). This silently filters out any package uploaded less than 7 days ago from uv's resolution view.

**Symptom**: `uv pip install <package>` fails with "No versions of <package> found" even though `curl https://pypi.org/simple/<package>/` shows the package exists.

**Fix**: Bump the `exclude-newer` date in `uv.lock`:
```
exclude-newer = "2026-05-10T00:00:00.000000000Z"
```
Then run `uv lock` to regenerate. Alternatively use `uv pip install --refresh` to force a fresh index fetch.

**Rule**: After publishing a new package, always update `uv.lock`'s `exclude-newer` date before trying to `uv pip install` it into a locked environment.

### Building with the wrong Python

`python -m build` from a project venv often fails — the venv may not have `build` installed, or may shadow the system Python.

**Fix**: Always invoke build via `/usr/bin/python3 -m build` (absolute path to system Python) from inside the project directory.

### Project venv has no pip

The Hermes `.venv` has no `pip` module. Direct `python -m pip install` fails with "No module named pip".

**Fix**:
```bash
# Install pip into the venv first
python3 -m ensurepip --upgrade

# Then install normally
python3 -m pip install <wheel.whl> --target /path/to/venv/lib/python3.11/site-packages/

# Or use uv to target the venv Python
uv pip install --python /path/to/venv/bin/python <package>
```

### `uv pip install` from PyPI fails with "exclude-newer" even with `--index-url`

The `uv.lock` file in a project pins the `exclude-newer` cutoff at resolution time. Even passing `--index-url https://pypi.org/simple/` to `uv pip install` doesn't override the lockfile's cutoff.

**Fix**: Edit `uv.lock`'s `exclude-newer` line to a date after the package's upload, then run `uv lock` to re-resolve.

### Publishing a package with the same version twice

PyPI does not allow re-uploading the same version. You must bump the version.

**Fix**: Update `version` in `pyproject.toml` before building.

---

## PyPI vs TestPyPI

- **PyPI** (pypi.org) — live, permanent, requires a verified account
- **TestPyPI** (test.pypi.org) — isolated, good for validation, tokens are separate

To publish to TestPyPI first:
```bash
# Register at test.pypi.org and get a token
# Store in ~/.pypirc under [testpypi] section
/usr/bin/python3 -m twine upload dist/* --repository testpypi
```

To install from TestPyPI:
```bash
uv pip install --python .venv/bin/python <package> --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/
```
