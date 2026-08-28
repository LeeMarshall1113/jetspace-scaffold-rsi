#!/usr/bin/env bash
# Broker lease wrapper for Git Bash on Windows.
#
# Why this exists rather than using ~/.compute-broker/lease-run.sh:
# that wrapper passes `--pid $$`. Under Git Bash, $$ is an MSYS pid, while the
# broker's pid_alive() checks Windows pids via tasklist when host_id() ends in
# /nt. The namespaces differ, the pid is never found, and the lease is reaped
# "process gone" in the same second it is granted. Its WSL callers are fine --
# there $$ and os.kill(pid, 0) share a namespace.
#
# So: no --pid. Heartbeats are the documented liveness signal and they work
# from any shell. Everything else matches the original, including the EXIT trap
# that returns capacity if this dies, and the preempt file the runner checks at
# batch boundaries.
set -uo pipefail

BROKER="C:/Users/hackathon/.compute-broker/broker.py"
PY="${PY:-/c/Python314/python.exe}"

ARGS=()
while [ $# -gt 0 ]; do
    if [ "$1" = "--" ]; then shift; break; fi
    ARGS+=("$1"); shift
done
[ $# -eq 0 ] && { echo "usage: $0 <request args> -- <command>" >&2; exit 64; }

ID=$("$PY" "$BROKER" request "${ARGS[@]}" | head -1)
[ -z "$ID" ] && { echo "lease: request failed" >&2; exit 65; }
echo "lease: request $ID"

export BROKER_PREEMPT_FILE="${TMPDIR:-/tmp}/broker-preempt-$ID"
rm -f "$BROKER_PREEMPT_FILE"

cleanup() {
    [ -n "${HB_PID:-}" ] && kill "$HB_PID" 2>/dev/null
    "$PY" "$BROKER" release "$ID" >/dev/null 2>&1
    echo "lease: released $ID"
}
trap cleanup EXIT INT TERM

if ! "$PY" "$BROKER" wait "$ID" --timeout "${LEASE_WAIT:-7200}"; then
    echo "lease: not granted, not starting" >&2
    exit 66
fi
echo "lease: granted $ID"

# Heartbeat well inside the 900s grace window, and start immediately rather
# than after the first sleep so a slow model load cannot look like a dead agent.
(
    while true; do
        "$PY" "$BROKER" heartbeat "$ID" >/dev/null 2>&1
        rc=$?
        if [ "$rc" = "10" ]; then
            echo "lease: PREEMPT requested -- flagging"
            touch "$BROKER_PREEMPT_FILE"
        elif [ "$rc" = "2" ]; then
            echo "lease: lease lost -- flagging"
            touch "$BROKER_PREEMPT_FILE"
        fi
        sleep 240
    done
) &
HB_PID=$!

"$@"
exit $?
