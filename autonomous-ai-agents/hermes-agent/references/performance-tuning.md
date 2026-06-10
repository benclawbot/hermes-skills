# Hermes Gateway Performance Tuning

The three highest-leverage config tweaks for `hermes-agent` gateway — faster tool calls, lower token burn, less context noise. Apply after fresh install, on token-budget pressure, or when terminal calls feel slow.

## Recommended Config Values

Place in `~/.hermes/config.yaml` under `agent:`:

```yaml
agent:
  auto_source_bashrc: false    # saves ~500ms–1s per terminal call
  file_read_max_chars: 30000   # forces surgical reads, not full files

tools:
  tool_output:
    max_bytes: 30000           # forces early summarization, less token waste
```

## What Each Setting Does

| Setting | Default | Tuned | Effect |
|---------|---------|-------|--------|
| `auto_source_bashrc` | `true` | `false` | Removes bashrc sourcing overhead on every terminal call (~500ms–1s saved) |
| `file_read_max_chars` | `100000` | `30000` | Forces targeted reads; avoids loading huge files into context |
| `tool_output max_bytes` | `50000` | `30000` | Truncates large tool output earlier; reduces token burn |

## Applying Changes

```bash
# Edit config
nano ~/.hermes/config.yaml

# Restart gateway to apply
systemctl --user restart hermes-gateway

# Verify gateway is up
systemctl --user status hermes-gateway
```

## When to Revert

- If you need to read large files in full (`file_read_max_chars: 30000` may truncate)
- If bashrc has critical env vars needed by tools (git-completion, custom prompt, etc.)
- If you want verbose tool output for debugging

## Verification

```bash
# Time a simple terminal call
time echo "test"

# Time a gh command (should be fast with gh-api-caching skill too)
time ~/.hermes/scripts/gh-cached.py || time /home/thomas/bin/gh repo list --limit 1
```

## Related

- `references/hermes-optimization.md` — broader daily-use config bundle (compression, max_turns, display toggles)
- `references/test-harness-improvements.md` — pytest/xdist/testmon patterns for the hermes-agent monorepo
- `references/s6-container-supervision.md` — perf-relevant container architecture (profile gateway supervision)
