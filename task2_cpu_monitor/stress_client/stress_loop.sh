#!/bin/bash
# stress_loop.sh
# Alternates between CPU stress and idle in a continuous loop.
# Uses stress-ng to generate real kernel-level CPU load.
#
# Environment variables:
#   STRESS_DURATION  – seconds to run stress (default: 30)
#   IDLE_DURATION    – seconds to idle between stress runs (default: 20)
#   CPU_WORKERS      – number of CPU stressor workers (default: 2)

set -euo pipefail

STRESS_DURATION=${STRESS_DURATION:-30}
IDLE_DURATION=${IDLE_DURATION:-20}
CPU_WORKERS=${CPU_WORKERS:-2}

echo "[stress-client] Starting stress loop"
echo "[stress-client] stress=${STRESS_DURATION}s | idle=${IDLE_DURATION}s | workers=${CPU_WORKERS}"

cycle=0
while true; do
    cycle=$((cycle + 1))
    echo "[stress-client] Cycle ${cycle}: Stressing CPU with ${CPU_WORKERS} workers for ${STRESS_DURATION}s …"
    stress-ng --cpu "${CPU_WORKERS}" --timeout "${STRESS_DURATION}s" --metrics-brief 2>&1 || true

    echo "[stress-client] Cycle ${cycle}: Idle for ${IDLE_DURATION}s …"
    sleep "${IDLE_DURATION}"
done
