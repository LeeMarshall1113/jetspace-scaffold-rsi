#!/usr/bin/env bash
# Lease-gated runner for the v4 instrument.
#
# Two ordering rules this encodes, both learned the hard way:
#   1. The release trap is set BEFORE the wait. An inline version of this script
#      set it after, so when the wait timed out it exited without releasing and
#      left a queue entry with no process behind it -- which would then be granted
#      to nobody.
#   2. The wait timeout must exceed how long the card can plausibly be held. 3600s
#      was shorter than a segmenter run and produced exactly that zombie.
set -uo pipefail
BROKER="C:/Users/hackathon/.compute-broker/broker.py"
STATE="C:/Users/hackathon/.compute-broker/state.json"
PY="${PY:-/c/Python314/python.exe}"
WANT_GPU="${WANT_GPU:-amd-9070xt}"
WAIT_S="${WAIT_S:-32400}"
MODEL="${MODEL:?set MODEL}"; TAG="${TAG:?set TAG}"
BATCH="${BATCH:-13}"; MEM_FRAC="${MEM_FRAC:-0.90}"; MINUTES="${MINUTES:-45}"; LIMIT="${LIMIT:-60}"

ID=$("$PY" "$BROKER" request \
  --project jetspace-scaffold-rsi --min-gb 5 --want-gb 8 --minutes "$MINUTES" \
  --gpu "$WANT_GPU" --preemptible --match "run.py|v4_compounding" \
  --why "v4 instrument: $TAG" \
  --argument "Tests the single premise the v4 instrument rests on: does a plausible-but-wrong entry, added to a store that ALREADY HOLDS the correct entry, cost accuracy? v3 failed here - its wrong entries contradicted confident behaviour and were ignored, so its coverage gate returned 1/12 against a threshold of 3. If this premise fails too, that is four instruments failing the same requirement and the compounding experiment should not be built on it. All stores size-matched to a fixed entry count, which is the control PR #1 identified as missing from v3. ${LIMIT} tasks x 13 conditions, greedy. Roughly 7GB commit; the broker reads WorkingSetSize, which understates ROCm jobs about 12x, so arbitrate on commit." \
  | head -1)
[ -z "$ID" ] && { echo "[v4] request failed"; exit 65; }
echo "[v4] request $ID for $WANT_GPU ($TAG)"

export BROKER_PREEMPT_FILE="${TMPDIR:-/tmp}/broker-preempt-$ID"
rm -f "$BROKER_PREEMPT_FILE"
cleanup() {
    [ -n "${HB_PID:-}" ] && kill "$HB_PID" 2>/dev/null
    "$PY" "$BROKER" release "$ID" >/dev/null 2>&1
    echo "[v4] released $ID"
}
trap cleanup EXIT INT TERM          # BEFORE the wait, deliberately

"$PY" "$BROKER" wait "$ID" --timeout "$WAIT_S" || { echo "[v4] not granted"; exit 66; }
LBL=v4
# Device verification, retried. A transient interpreter failure here once
# produced an empty GOT, which the old code read as "wrong device" and aborted --
# silently discarding a lease that had queued four hours for the card. Distinguish
# "could not read" from "read, and it is wrong": only the latter is a real abort.
# -I isolates the interpreter from CWD and PYTHONPATH, which is where that class
# of import failure comes from.
GOT=""
for _try in 1 2 3 4 5; do
    GOT=$("$PY" -I -c "
import json
s = json.load(open(r'$STATE'))
print(next((l.get('gpu') or '' for l in s.get('leases', []) if l['id'] == '$ID'), ''))
" 2>/dev/null)
    [ -n "$GOT" ] && break
    echo "[$LBL] device read $_try/5 empty, retrying"
    sleep 3
done
if [ -z "$GOT" ]; then
    echo "[$LBL] ABORT: could not read granted device after 5 tries"; exit 71
fi
if [ "$GOT" != "$WANT_GPU" ]; then
    echo "[$LBL] ABORT: granted '$GOT', need '$WANT_GPU'"; exit 70
fi
echo "[$LBL] granted on $GOT"

( while true; do
    "$PY" "$BROKER" heartbeat "$ID" >/dev/null 2>&1; rc=$?
    [ "$rc" = "10" ] && { echo "[v4] preempt"; touch "$BROKER_PREEMPT_FILE"; }
    [ "$rc" = "2" ]  && { echo "[v4] lease lost"; touch "$BROKER_PREEMPT_FILE"; }
    sleep 240
  done ) & HB_PID=$!

cd "$(dirname "$0")"
ROCBLAS_USE_HIPBLASLT=0 /c/Users/hackathon/Documents/GitHub/arc-agi-2/.venv-rocm/Scripts/python.exe \
  run.py --model "$MODEL" --tag "$TAG" --limit "$LIMIT" --batch "$BATCH" --mem-frac "$MEM_FRAC" 2>&1 \
  | grep -vE "Loading weights|UserWarning|_ = torch" | tail -4
