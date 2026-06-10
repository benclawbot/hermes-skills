# RTK Setup — Verification Log (2025-05-08)

## Verified working commands

### Test sequence (live results)
```bash
# Standard vs RTK comparison
bash -c 'source ~/.bash_aliases 2>/dev/null; shopt -s expand_aliases; rtk git diff --cached'
# Standard: diff --git a/test_rtk.txt... (21 lines compressed to compact)
# rtk gain output:
#   rtk git diff --cached  21 saved (41.2%)
#   rtk ls -la              314 saved (72.7%)

rtk gain
# Total commands: 8
# Input tokens: 485, Output tokens: 153
# Tokens saved: 337 (69.5%)
```

### RTK gain output format
```
Total commands:    N
Input tokens:      N
Output tokens:     N
Tokens saved:      N (X.X%)
[warn] No hook installed — run `rtk init -g` for automatic token savings

By Command
───────────────────────────────────────────────────────────────────────
  #  Command                   Count  Saved    Avg%    Time  Impact
───────────────────────────────────────────────────────────────────────
```

The `[warn] No hook installed` is expected when using bash aliases — it's the Claude Code native hook, not relevant for Hermes. The savings still apply.

## Gateway restart needed
After patching `tools/environments/local.py`, the Hermes gateway must be restarted to pick up the changes:
```bash
systemctl --user restart hermes-gateway
```
This has historically timed out — use `systemctl --user restart` directly, not the graceful shutdown path.