# GitHub Script Optimization

Two patterns for making `gh` CLI / `gh api` scripts dramatically faster when they iterate over many repos or run frequently. Use both together for repo monitoring cron jobs (project-health-digest, github-pr-digest, single-repo-digest).

## 1. GitHub API Caching (`gh_cached`)

Cache `gh` calls to disk with a 5-minute TTL. Eliminates repeated `gh` CLI latency (~500ms → ~50ms on cache hit). **Use this for any script that calls `gh api` more than a handful of times per minute.**

### Core Pattern

```python
import hashlib, json, time, os
from pathlib import Path

CACHE_DIR = Path.home() / ".hermes/cache/gh"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
TTL = 300  # 5 minutes

def gh_cached(cmd: list[str]) -> dict:
    """Run gh command, return cached result if fresh."""
    cache_key = hashlib.sha256(" ".join(cmd).encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"

    # Check memory + disk cache
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < TTL:
            return json.loads(cache_file.read_text())

    # Run gh (use /home/thomas/bin/gh, not /usr/bin/gh)
    import subprocess
    result = subprocess.run(
        ["/home/thomas/bin/gh"] + cmd,
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)

    # Cache to disk
    cache_file.write_text(json.dumps(data))
    return data
```

### Usage

```python
from gh_cached import gh_cached

repos = gh_cached(["repo", "list", "--limit", "30"])
for repo in repos:
    runs = gh_cached(["api", f"/repos/benclawbot/{repo['name']}/actions/runs"])
    # ... process
```

### Constraints

- **Use `/home/thomas/bin/gh`** — authenticated as benclawbot via keyring
- **TTL=300s (5 min)** — safe for cron jobs that run every hour or less
- **Not safe for real-time user-facing queries** — cache is shared across all scripts
- For script-local cache (faster repeated calls within one run), add an in-memory dict wrapper

### Verification

```bash
cd /home/thomas/.hermes/scripts && /home/thomas/Desktop/hermes-agent/.venv/bin/python3 -c "
from gh_cached import gh_cached
import time
t0 = time.time(); r1 = gh_cached(['repo', 'list', '--limit', '1'])
t1 = time.time(); r2 = gh_cached(['repo', 'list', '--limit', '1'])
print(f'fresh: {(t1-t0)*1000:.0f}ms, cached: {(time.time()-t1)*1000:.0f}ms')
"
```

Expected: fresh ~500ms, cached ~50ms.

## 2. Parallel `gh` Scripts (`ThreadPoolExecutor`)

Parallelize multi-repo `gh api` calls. **29 repos in 5.3s vs 30s sequential** (~6x speedup). Use when iterating over a known list of repos.

### Core Structure

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess, json

GH = "/home/thomas/bin/gh"
WORKERS = 8

def fetch_repo_data(repo_name: str) -> dict:
    """Fetch all data for one repo. Runs in thread pool."""
    data = {"name": repo_name, "error": None}
    try:
        result = subprocess.run(
            [GH, "api", f"/repos/benclawbot/{repo_name}/actions/runs"],
            capture_output=True, text=True, timeout=15
        )
        runs = json.loads(result.stdout).get("workflow_runs", [])
        data["runs"] = runs[:3]  # last 3 runs
    except Exception as e:
        data["error"] = str(e)
    return data

def main():
    # Get repo list
    result = subprocess.run(
        [GH, "repo", "list", "benclawbot", "--limit", "30", "--json", "name"],
        capture_output=True, text=True
    )
    repos = [r["name"] for r in json.loads(result.stdout)]

    # Parallel fetch
    results = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_repo_data, repo): repo for repo in repos}
        for future in as_completed(futures):
            repo = futures[future]
            results[repo] = future.result()

    # Collate results
    for repo, data in results.items():
        if data["error"]:
            print(f"❌ {repo}: {data['error']}")
        else:
            print(f"✅ {repo}: {len(data['runs'])} runs")
```

### Key Parameters

| Param | Value | Rationale |
|-------|-------|-----------|
| `WORKERS` | 8 | Balances parallelism vs GitHub API rate limits |
| `timeout` | 15s per call | Prevents hung threads blocking the pool |
| `runs[:3]` | last 3 runs | Enough for health check, reduces data |

### Combine with `gh_cached`

```python
# In fetch_repo_data, replace subprocess.run with gh_cached():
from gh_cached import gh_cached

def fetch_repo_data(repo_name: str) -> dict:
    data = {"name": repo_name, "error": None}
    try:
        runs = gh_cached(["api", f"/repos/benclawbot/{repo_name}/actions/runs"])
        data["runs"] = runs.get("workflow_runs", [])[:3]
    except Exception as e:
        data["error"] = str(e)
    return data
```

### Verification

```bash
cd /home/thomas/.hermes/scripts && time /home/thomas/Desktop/hermes-agent/.venv/bin/python3 project-health-digest.py
```

Expected: ~5-6s for 29 repos. Sequential would be ~30s.

## Common Pitfalls

- **Don't use `ThreadPoolExecutor` with `map`** — use `as_completed` to process results as they finish
- **Set a timeout on subprocess calls** — `gh` API hangs can block threads forever
- **GitHub rate limit**: ~5000 req/hr authenticated. 8 workers × 29 repos × 2 calls = ~58 calls per run. Well within limit.
- **Cron PATH stripped**: `gh` lives at `/home/thomas/bin/gh`, not `/usr/bin/gh`. Cron PATH often doesn't include `~/bin`, so the full path is mandatory. Same goes for the credential helper — see the Push Troubleshooting section in this skill.
