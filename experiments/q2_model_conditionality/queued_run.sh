#!/usr/bin/env bash
# Wait for a NAMED GPU to be free, then run under a lease that actually holds it.
#
# Why this exists: broker.py's --gpu is a boolean and schedule() assigns from the
# pool by availability, so a caller cannot ask for a specific device. My ROCm venv
# can only use amd-9070xt; an nvidia assignment is not a substitute, it is a lease
# for a card I will not touch while I quietly use one the broker believes is free.
# That produced a real collision with solar-filament-26's converged segmenter run.
#
# So: wait until nothing holds the card, then request, then VERIFY the grant is
# the card we need and abort if it is not. Never run on a device the broker has
# assigned to someone else.
set -uo pipefail

BROKER="C:/Users/hackathon/.compute-broker/broker.py"
STATE="C:/Users/hackathon/.compute-broker/state.json"
PY="${PY:-/c/Python314/python.exe}"
WANT_GPU="${WANT_GPU:-amd-9070xt}"
POLL_S="${POLL_S:-60}"
MAX_WAIT_S="${MAX_WAIT_S:-25200}"   # 7h, then give up rather than linger forever

gpu_held() {   # 0 = held by someone
    "$PY" -c "
import json,sys
try: s=json.load(open(r'$STATE'))
except Exception: sys.exit(1)
sys.exit(0 if any(l.get('gpu')=='$WANT_GPU' for l in s.get('leases',[])) else 1)
"
}

echo "[queue] waiting for $WANT_GPU to clear (poll ${POLL_S}s, give up after $((MAX_WAIT_S/3600))h)"
waited=0
while gpu_held; do
    if [ "$waited" -ge "$MAX_WAIT_S" ]; then
        echo "[queue] gave up after ${waited}s -- $WANT_GPU still held. Nothing run."
        exit 75
    fi
    sleep "$POLL_S"
    waited=$((waited + POLL_S))
done
echo "[queue] $WANT_GPU free after ${waited}s"

ID=$("$PY" "$BROKER" request \
    --project jetspace-scaffold-rsi --min-gb 5 --want-gb 8 --minutes 40 --gpu \
    --match "run_loo|q2_model_conditionality" \
    --why "Q2 v3 coverage check at n=50 (3B), queued behind amd-9070xt" \
    --argument "Queued to start only once amd-9070xt was released, after an earlier attempt was granted nvidia-16g while actually running on the AMD card that solar-filament-26 held exclusively. Verifies the granted device before starting and aborts if it is not the AMD card. Measures how many of 12 entries can express a NEGATIVE effect in the redesigned instrument at n=50; the n=8-10 smokes disagreed (2/12 vs 1/12). This gates whether a four-backbone sign-flip run is worth several GPU-hours. 1400 greedy generations, batch 13, 5.8GB bf16 weights, ~7GB commit -- the broker reads WorkingSetSize, which understates ROCm jobs roughly 12x. Preemptible; checkpoints every batch." \
    --preemptible | head -1)
[ -z "$ID" ] && { echo "[queue] request failed"; exit 65; }
echo "[queue] request $ID"

export BROKER_PREEMPT_FILE="${TMPDIR:-/tmp}/broker-preempt-$ID"
rm -f "$BROKER_PREEMPT_FILE"
cleanup() {
    [ -n "${HB_PID:-}" ] && kill "$HB_PID" 2>/dev/null
    "$PY" "$BROKER" release "$ID" >/dev/null 2>&1
    echo "[queue] released $ID"
}
trap cleanup EXIT INT TERM

"$PY" "$BROKER" wait "$ID" --timeout 3600 || { echo "[queue] not granted"; exit 66; }

GOT=$("$PY" -c "
import json
s=json.load(open(r'$STATE'))
print(next((l.get('gpu') for l in s.get('leases',[]) if l['id']=='$ID'), ''))
")
if [ "$GOT" != "$WANT_GPU" ]; then
    echo "[queue] ABORT: granted '$GOT', need '$WANT_GPU'. Not running on a device"
    echo "[queue] the broker has assigned elsewhere. Releasing."
    exit 70
fi
echo "[queue] granted $ID on $GOT -- starting"

( while true; do
    "$PY" "$BROKER" heartbeat "$ID" >/dev/null 2>&1
    rc=$?
    [ "$rc" = "10" ] && { echo "[queue] preempt requested"; touch "$BROKER_PREEMPT_FILE"; }
    [ "$rc" = "2" ]  && { echo "[queue] lease lost";      touch "$BROKER_PREEMPT_FILE"; }
    sleep 240
  done ) &
HB_PID=$!

cd "$(dirname "$0")"
ROCBLAS_USE_HIPBLASLT=0 \
/c/Users/hackathon/Documents/GitHub/arc-agi-2/.venv-rocm/Scripts/python.exe run_loo.py \
    --model /c/Users/hackathon/Documents/GitHub/arc-agi-2/models/qwen2.5-coder-3b-instruct \
    --tag v3-qwen25c-3b --limit 50 --batch 13 --max-new 160 2>&1 \
  | grep -vE "Loading weights|UserWarning|_ = torch" | tail -4
