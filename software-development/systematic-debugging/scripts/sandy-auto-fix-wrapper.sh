#!/bin/bash
# Sandy watchdog wrapper with embedded 5-whys auto-fix.
# Place alongside your .sh cron script. Adjust PYTHON and SCENARIO paths.
#
# Usage: from your cron job's script field, call this wrapper directly, e.g.:
#   /home/thomas/.hermes/skills/systematic-debugging/5-whys-analysis/scripts/sandy-auto-fix-wrapper.sh \
#     /home/thomas/.hermes/sandy/scenarios/system-anomaly-watchdog.json \
#     /tmp/watch_anomalies_sandy.fail

SCENARIO="${1:-/home/thomas/.hermes/sandy/scenarios/system-anomaly-watchdog.json}"
FAIL_FILE="${2:-/tmp/sandy.fail}"
PYTHON="/home/thomas/Desktop/hermes-agent/.venv/bin/python3"
PLAY="/home/thomas/.hermes/skill-assets/sandy/scripts/play.py"

output=$($PYTHON "$PLAY" "$SCENARIO" 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    rm -f "$FAIL_FILE"
    [ -n "$output" ] && echo "$output"
    exit 0
fi

# 5-whys auto-fix: deterministic failure patterns
if echo "$output" | grep -q "ModuleNotFoundError"; then
    MODULE=$(echo "$output" | grep -oP "No module named '\K[^']+")
    if [ -n "$MODULE" ]; then
        uv pip install --python "$PYTHON" "$MODULE" 2>/dev/null
        output=$($PYTHON "$PLAY" "$SCENARIO" 2>&1)
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            rm -f "$FAIL_FILE"
            [ -n "$output" ] && echo "$output"
            exit 0
        fi
    fi
fi

echo "$output" > "$FAIL_FILE"
exit $exit_code
