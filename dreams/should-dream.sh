#!/usr/bin/env bash
#
# should-dream.sh — Check if dream consolidation should run
#
# Exit 0 if dream should run, exit 1 if not.
# Condition: 24+ hours since last dream.
# First run ever: always exit 0 (condition met).

set -euo pipefail

LAST_DREAM_FILE="$HOME/.hermes/.last-dream"

# If no timestamp exists, this is first run — condition met
if [[ ! -f "$LAST_DREAM_FILE" ]]; then
    echo "Dream conditions met: first-run (no .last-dream found)"
    exit 0
fi

LAST_DREAM=$(cat "$LAST_DREAM_FILE")
NOW=$(date +%s)
ELAPSED=$(( NOW - LAST_DREAM ))
HOURS_ELAPSED=$(( ELAPSED / 3600 ))

if (( HOURS_ELAPSED < 24 )); then
    echo "Skipping dream: ${HOURS_ELAPSED}h since last dream (need 24h)"
    exit 1
fi

echo "Dream conditions met: ${HOURS_ELAPSED}h since last dream"
exit 0