# Testing Provider Classes (External Library Integration)

When testing a class that imports an external package (e.g., `from agent_commit import CommitStore`), the goal is **integration testing** — verify the provider correctly uses the real library, not mock it away.

## Core Technique: sys.path.insert for Runtime Library Paths

The library under test (e.g., `agent-commit`) lives at `/tmp/agent-commit-repo/src`. The test file adds it to `sys.path` before any imports:

```python
import sys
sys.path.insert(0, "/tmp/agent-commit-repo/src")
from agent_commit import CommitStore
from agent.agent_commit_provider import AgentCommitMemoryProvider
```

This is better than mocking because it catches:
- Import-time errors (wrong module structure)
- Runtime API mismatches (method signatures that changed)
- Behavioral bugs in the store interaction

## Key Patterns

### 1. Per-test store isolation with `_commit_stores.clear()`

The provider uses a module-level `_commit_stores` dict as a cache. Between tests, clear it to ensure each test gets a fresh store:

```python
def test_sync_turn_commits_turn(self, tmp_path):
    from agent import agent_commit_provider
    agent_commit_provider._commit_stores.clear()  # critical!

    db_path = str(tmp_path / "agent_commit.db")
    provider = AgentCommitMemoryProvider(enabled=True, store_path=db_path)
    ...
```

Without this, a store created in one test is reused by another, causing test pollution.

### 2. Use pytest's `tmp_path` fixture for temporary DBs

Never use `tempfile.mktemp()` or `tempfile.mkstemp()` directly in tests — they create files outside pytest's cleanup system. Use `tmp_path`:

```python
def test_example(self, tmp_path):
    db_path = str(tmp_path / "agent_commit.db")  # Good: pytest cleans this up
    provider = AgentCommitMemoryProvider(enabled=True, store_path=db_path)
```

anti-pattern (don't do this):
```python
tempfile.mktemp() / "ac.db"   # TypeError: str / str
tempfile.mkstemp()             # Returns (fd, path) tuple — not a path
```

### 3. Catching ImportError at call time

The provider's `_get_commit_store()` is called inside `sync_turn()`. If the external library isn't installed, it raises `ImportError`. Wrap the call:

```python
def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
    if not self._enabled:
        return
    try:
        store = _get_commit_store(self._store_path)
    except ImportError:
        store = None
    if store is None:
        return
    ...
```

### 4. Mocking `_get_commit_store` for the "not installed" test

To test graceful degradation when the library is absent, mock the function directly:

```python
def test_lazy_import_not_installed(self):
    from agent import agent_commit_provider
    agent_commit_provider._commit_stores.clear()

    original = agent_commit_provider._get_commit_store

    def fake_get(path=None):
        raise ImportError("No module named 'agent_commit'")

    agent_commit_provider._get_commit_store = fake_get
    try:
        provider = AgentCommitMemoryProvider(enabled=True)
        provider.sync_turn("msg", "resp", session_id="test")  # must not raise
    finally:
        agent_commit_provider._get_commit_store = original
```

Don't try to actually uninstall the package — just mock the function.

### 5. Concurrent threading test: unique content per call

SQLite's `INSERT OR IGNORE` deduplicates rows by content hash. If all 50 concurrent calls have identical messages, only 1 row gets inserted. Use unique content per call:

```python
call_count = [0]
lock = threading.Lock()

def sync(n):
    with lock:
        idx = call_count[0]
        call_count[0] += 1
    provider.sync_turn(f"user-{idx}", f"assistant-{idx}", session_id="concurrent")

threads = [threading.Thread(target=sync, args=(i,)) for i in range(5)]
```

This ensures 5 separate commits, not 1.

### 6. Thread-safe store creation with a lock

If multiple threads race to create `CommitStore` for the same path simultaneously, SQLite can fail. Serialize store creation:

```python
_store_create_lock = threading.Lock()

def _get_commit_store(store_path: Optional[str] = None):
    global _commit_stores
    if store_path not in _commit_stores:
        with _store_create_lock:
            if store_path not in _commit_stores:  # double-check after acquiring lock
                _commit_stores[store_path] = CommitStore(db_path=path)
```

## Running the Tests

```bash
cd /path/to/hermes-agent
PYTHONPATH=/tmp/agent-commit-repo/src python -m pytest tests/tools/test_agent_commit_provider.py -v
```

`PYTHONPATH` is required because the tests import from `agent_commit` (the external lib) and `agent` (the hermes package), and the test needs the external lib's `src/` on the path to find it.