---
name: gh-api-optimization
description: "GitHub API performance patterns for cron scripts: caching (gh-cached.py) and parallel execution. Reduces 30s+ repository health checks to ~5s."
version: 1.0.0
---

# GitHub API Optimization for Cron Scripts

Two patterns learned from benchmarking and fixing slow digest scripts (May 2026):

## 1. Cache with `gh-cached.py`

**Problem:** Unauthenticated gh CLI calls take ~500ms each. A script hitting 29 repos runs sequential = timeout.

**Solution:** `~/.hermes/scripts/gh-cached.py` — transparent gh API cache with 5-min TTL, in-memory + disk persistence.

```python
# In any script that calls gh:
import sys
sys.path.insert(0, '/home/thomas/.hermes/scripts')
from gh_cached import gh

# Use like subprocess but cached:
rc, out, err = gh('api repos/benclawbot/FastBot/actions/runs?per_page=1')
```

**Key properties:**
- Session-memory LRU caches repeated calls within same run (same command in same 5-min bucket)
- Disk cache (`/tmp/gh-cache/`) persists across script invocations within 5-min window
- Cache key = hash of (command, 5-min time bucket) — stale enough to avoid fragmentation, fresh enough for same-session reuse
- Automatic fallback to uncached `gh` if cache miss

**Why 5-min:** Balance between freshness and speed for weekly/daily cron runs. Same-session repeated calls hit memory cache (~50ms vs 500ms = 10x speedup).

## 2. Parallelize with `ThreadPoolExecutor`

**Problem:** Sequential API calls to N repos = N × ~500ms = timeout for large repo lists.

**Solution:** Parallel workers, bounded concurrency to avoid rate limiting.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.path.insert(0, '/home/thomas/.hermes/scripts')
from gh_cached import gh

REPOS = [...]  # list of repo names
WORKERS = 8   # avoid rate limiting, maximize parallelism

def check_repo(repo):
    rc, out, err = gh(f'api repos/benclawbot/{repo}/actions/runs?per_page=1')
    # ... parse output ...
    return repo, status

with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = {executor.submit(check_repo, repo): repo for repo in REPOS}
    for future in as_completed(futures):
        repo, status = future.result()
        # ... accumulate results ...
```

**Real result (project-health-digest.py):** 29 repos: 30s+ sequential → 5.3s parallel.

**Workers = 8:** Sweet spot — enough parallelism without hitting GitHub rate limits.

## Canonical reference scripts

| Script | What it does | Key pattern |
|--------|-------------|-------------|
| `~/.hermes/scripts/gh-cached.py` | Reusable caching wrapper around gh CLI | Import and use `gh(cmd)` instead of subprocess |
| `~/.hermes/scripts/project-health-digest.py` | Checks CI status for 29 repos | `ThreadPoolExecutor(8)` + `gh_cached` |
| `~/.hermes/scripts/github-pr-digest.py` | Reports open PRs across all repos | `gh_cached` for all gh calls |
| `~/.hermes/scripts/single-repo-digest.py` | Single benclawbot repo weekly summary | `gh_ccached` for all gh calls |

## Pitfalls

**1. Don't use `gh auth token` in cron context.** Cron jobs run in a stripped `$PATH`. gh is at `/home/thomas/bin/gh`, not in default PATH. Use `gh-cached.py` which hardcodes the path.

**2. Don't parallelize unbounded.** GitHub rate limits: 5000 requests/hour for authenticated. With 29 repos and ~3 calls each per run, a bounded ThreadPoolExecutor(8) stays well under the limit.

**3. Cache invalidation.** 5-min TTL is the right default for digest scripts running on hour-plus intervals. For real-time operations, use `gh api --refresh` or clear the cache key explicitly.

**4. gh path matters.** The gh CLI at `/home/thomas/bin/gh` (not `/usr/bin/gh`) is what the cron scripts use. `gh-cached.py` hardcodes this path.
