#!/usr/bin/env bash
# Run the Q2 coverage check under a lease for a NAMED GPU.
#
# History: broker.py's --gpu was a boolean and schedule() assigned from the pool
# by availability, so a caller could not ask for a specific device. My ROCm venv
# can only use amd-9070xt, so an nvidia grant was a lease for a card I would not
# touch while quietly using one the broker believed free -- which collided with
# solar-filament-26's converged segmenter run. That is fixed upstream (e98e16c):
# `--gpu <name>` now requires that device and QUEUES rather than substituting.
#
# So this no longer polls. It asks for the card by name and lets the broker hold
# its place. The post-grant verification stays anyway: it costs nothing, and it is
# the check that would have caught the original bug.
set -uo pipefail

BROKER="C:/Users/hackathon/.compute-broker/broker.py"
STATE="C:/Users/hackathon/.compute-broker/state.json"
PY="${PY:-/c/Python314/python.exe}"
WANT_GPU="${WANT_GPU:-amd-9070xt}"
WAIT_S="${WAIT_S:-25200}"   # 7h; solar-filament-26 has ~4h left

ID=$("$PY" "$BROKER" request \
    --project jetspace-scaffold-rsi --min-gb 5 --want-gb 8 --minutes 40 \
    --gpu "$WANT_GPU" --preemptible \
    --match "run_loo|q2_model_conditionality" \
    --why "Q2 v3 coverage check at n=50 (3B), queued on amd-9070xt" \
    --argument "Queued against amd-9070xt by name so it starts the moment solar-filament-26 releases -- not sharing the card, which nearly cost that converged run earlier. Measures how many of 12 entries can express a NEGATIVE effect in the redesigned instrument at n=50; the n=8-10 smokes disagreed with each other (2/12 vs 1/12), which is too unstable to build on. This gates whether a four-backbone sign-flip run is worth several GPU-hours: fewer than three negative-capable entries and that test cannot support a conclusion. 1400 greedy generations, batch 13, ~10 min. COMMIT NOTE: 5.8GB bf16 weights give roughly 7GB commit; the broker reads WorkingSetSize, which understates ROCm jobs by around 12x (my 7B run showed 1.45GB WS against 17.7GB real), so size any arbitration against the commit figure, not the status line. Preemptible and genuinely so: checks the preempt file every batch and flushes each generation to JSONL, so yielding costs one batch." \
    | head -1)
[ -z "$ID" ] && { echo "[queue] request failed"; exit 65; }
echo "[queue] request $ID for $WANT_GPU"

export BROKER_PREEMPT_FILE="${TMPDIR:-/tmp}/broker-preempt-$ID"
rm -f "$BROKER_PREEMPT_FILE"
cleanup() {
    [ -n "${HB_PID:-}" ] && kill "$HB_PID" 2>/dev/null
    "$PY" "$BROKER" release "$ID" >/dev/null 2>&1
    echo "[queue] released $ID"
}
trap cleanup EXIT INT TERM

echo "[queue] waiting for grant (up to $((WAIT_S/3600))h)"
"$PY" "$BROKER" wait "$ID" --timeout "$WAIT_S" || { echo "[queue] not granted"; exit 66; }

GOT=$("$PY" -c "
import json
s=json.load(open(r'$STATE'))
print(next((l.get('gpu') for l in s.get('leases',[]) if l['id']=='$ID'), ''))
")
if [ "$GOT" != "$WANT_GPU" ]; then
    echo "[queue] ABORT: granted '$GOT', need '$WANT_GPU'. Not running on a device"
    echo "[queue] assigned elsewhere. Releasing."
    exit 70
fi
echo "[queue] granted on $GOT -- starting"

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
