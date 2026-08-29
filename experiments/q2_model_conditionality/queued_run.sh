#!/usr/bin/env bash
# Run one backbone's v3 measurement under a lease for a NAMED GPU.
#
# History: broker.py's --gpu was a boolean and schedule() assigned from the pool
# by availability, so a caller could not ask for a specific device. This ROCm venv
# can only use amd-9070xt, so an nvidia grant was a lease for a card we would not
# touch while quietly using one the broker believed free -- which collided with a
# converged segmenter run. Fixed upstream (e98e16c): `--gpu <name>` now requires
# that device and QUEUES rather than substituting.
#
# The post-grant verification stays anyway. It costs nothing and it is the check
# that would have caught the original bug.
#
# Usage:  MODEL=<path> TAG=<name> [BATCH=8] [MEM_FRAC=0.90] [MINUTES=60] ./queued_run.sh
set -uo pipefail

BROKER="C:/Users/hackathon/.compute-broker/broker.py"
STATE="C:/Users/hackathon/.compute-broker/state.json"
PY="${PY:-/c/Python314/python.exe}"
WANT_GPU="${WANT_GPU:-amd-9070xt}"
WAIT_S="${WAIT_S:-32400}"          # 9h: may sit behind other jobs and its siblings

MODEL="${MODEL:?set MODEL}"
TAG="${TAG:?set TAG}"
BATCH="${BATCH:-13}"
MEM_FRAC="${MEM_FRAC:-0.90}"
MINUTES="${MINUTES:-60}"

ARGUMENT="Replicating a measured result on backbone ${TAG}. The finding: context entries change model accuracy on fields they never mention -- state 0.02 to 0.74, dob 0.48 to 0.00, from entries with no reference to those fields -- which makes the independent per-entry validation used by published systems unsound. It currently rests on ONE backbone; this takes it to four across two lineages, which is the difference between a demonstration and a result. 1400 greedy generations at n=50. COMMIT NOTE: the broker reads WorkingSetSize, which understates ROCm jobs by roughly 12x (a 7B run here showed 1.45GB WS against 17.7GB real commit), so arbitrate against commit, not the status line. Queued by device name rather than sharing the card -- sharing nearly cost solar-filament a converged run earlier. Genuinely preemptible: checks the preempt file every batch and flushes each generation, so yielding costs one batch and resumes in place."

ID=$("$PY" "$BROKER" request \
    --project jetspace-scaffold-rsi --min-gb 5 --want-gb 8 --minutes "$MINUTES" \
    --gpu "$WANT_GPU" --preemptible \
    --match "run_loo|q2_model_conditionality" \
    --why "Q2 v3 off-target replication at n=50 (${TAG})" \
    --argument "$ARGUMENT" | head -1)
[ -z "$ID" ] && { echo "[queue] request failed"; exit 65; }
echo "[queue] request $ID for $WANT_GPU ($TAG)"

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
echo "[queue] granted on $GOT -- starting $TAG"

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
    --model "$MODEL" --tag "$TAG" --limit 50 --batch "$BATCH" \
    --max-new 160 --mem-frac "$MEM_FRAC" 2>&1 \
  | grep -vE "Loading weights|UserWarning|_ = torch" | tail -4
