#!/usr/bin/env bash
# Section 6 under a named-GPU lease. Shares section 4's evaluation cache.
set -uo pipefail
cd "$(dirname "$0")"
BROKER="C:/Users/hackathon/.compute-broker/broker.py"; PY=/c/Python314/python.exe
STATE="C:/Users/hackathon/.compute-broker/state.json"; WANT_GPU=amd-9070xt; LBL=s6
M=/c/Users/hackathon/Documents/GitHub/arc-agi-2/models/qwen2.5-coder-3b-instruct
ID=$($PY $BROKER request --project jetspace-scaffold-rsi --min-gb 5 --want-gb 8 \
  --minutes 180 --gpu amd-9070xt --preemptible --match "compound.py|v4_compounding" \
  --why "Section 6: does selection error compound across generations?" \
  --argument "The paper's central experiment. Self-evolving agents select what context to keep every generation, using per-entry evaluation against a fixed reference while the deployed store grows around it. Tests whether the gap to oracle selection WIDENS with generation count or stays flat - a flat gap falsifies the compounding claim and is reported either way. Three batch orderings because greedy is order-dependent by construction and how much that matters is itself a measurement. Shares section 4's evaluation cache, so overlapping stores cost nothing; expect well under the ~180 min requested. 3 CPU threads, ~7GB commit - the broker reads WorkingSetSize which understates ROCm jobs about 12x." | head -1)
[ -z "$ID" ] && { echo "[s6] request failed"; exit 65; }
echo "[s6] request $ID"
export BROKER_PREEMPT_FILE="${TMPDIR:-/tmp}/broker-preempt-$ID"; rm -f "$BROKER_PREEMPT_FILE"
cleanup(){ [ -n "${HB_PID:-}" ] && kill "$HB_PID" 2>/dev/null; $PY $BROKER release "$ID" >/dev/null 2>&1; echo "[s6] released $ID"; }
trap cleanup EXIT INT TERM
$PY $BROKER wait "$ID" --timeout 43200 || { echo "[s6] not granted"; exit 66; }
GOT=""
for _try in 1 2 3 4 5; do
    GOT=$($PY -I -c "
import json
s = json.load(open(r'$STATE'))
print(next((l.get('gpu') or '' for l in s.get('leases', []) if l['id'] == '$ID'), ''))
" 2>/dev/null)
    [ -n "$GOT" ] && break
    echo "[$LBL] device read $_try/5 empty, retrying"; sleep 3
done
[ -z "$GOT" ] && { echo "[$LBL] ABORT: could not read granted device"; exit 71; }
[ "$GOT" != "$WANT_GPU" ] && { echo "[$LBL] ABORT: granted '$GOT'"; exit 70; }
echo "[$LBL] granted on $GOT"
( while true; do $PY $BROKER heartbeat "$ID" >/dev/null 2>&1; rc=$?
  [ "$rc" = "10" ] || [ "$rc" = "2" ] && touch "$BROKER_PREEMPT_FILE"; sleep 240; done ) & HB_PID=$!
ROCBLAS_USE_HIPBLASLT=0 /c/Users/hackathon/Documents/GitHub/arc-agi-2/.venv-rocm/Scripts/python.exe \
  compound.py --model "$M" --tag s6-3b --limit 60 --batch 13 --pad-to 26 \
  --gen-batch 3 --generations 6 --orderings 3 2>&1 | grep -vE "Loading weights|UserWarning|_ = torch"
