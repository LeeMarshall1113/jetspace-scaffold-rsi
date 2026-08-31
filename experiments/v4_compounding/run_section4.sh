#!/usr/bin/env bash
# Section 4 under a named-GPU lease. Runs after the pool verification.
set -uo pipefail
cd "$(dirname "$0")"
BROKER="C:/Users/hackathon/.compute-broker/broker.py"; PY=/c/Python314/python.exe
M=/c/Users/hackathon/Documents/GitHub/arc-agi-2/models/qwen2.5-coder-3b-instruct
ID=$($PY $BROKER request --project jetspace-scaffold-rsi --min-gb 5 --want-gb 8 \
  --minutes 150 --gpu amd-9070xt --preemptible --match "select.py|v4_compounding" \
  --why "Section 4: independent gating vs oracle selection" \
  --argument "The headline measurement of the paper's setup section: how much performance does independent per-entry gating leave on the table against oracle subset selection? Four procedures over an 18-candidate pool - independent (what SkillGen/SkillOpt do, O(n)), global-effect scoring (same cost, scores total accuracy rather than target field), greedy with re-measurement (O(n*k)), and an oracle ceiling from sampling plus hill-climbing. Roughly 300 unique stores at 60 tasks each, ~90 min, all size-matched to 26 entries so content is not confounded with context length. Every evaluation is cached to disk by store contents, so a preemption costs only the store in flight and a rerun pays nothing for work already done. 3 CPU threads, ~7GB commit - the broker reads WorkingSetSize which understates ROCm jobs about 12x." | head -1)
[ -z "$ID" ] && { echo "[s4] request failed"; exit 65; }
echo "[s4] request $ID"
export BROKER_PREEMPT_FILE="${TMPDIR:-/tmp}/broker-preempt-$ID"; rm -f "$BROKER_PREEMPT_FILE"
cleanup(){ [ -n "${HB_PID:-}" ] && kill "$HB_PID" 2>/dev/null; $PY $BROKER release "$ID" >/dev/null 2>&1; echo "[s4] released $ID"; }
trap cleanup EXIT INT TERM
$PY $BROKER wait "$ID" --timeout 43200 || { echo "[s4] not granted"; exit 66; }
LBL=s4
STATE="C:/Users/hackathon/.compute-broker/state.json"
WANT_GPU=amd-9070xt
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
( while true; do $PY $BROKER heartbeat "$ID" >/dev/null 2>&1; rc=$?
  [ "$rc" = "10" ] || [ "$rc" = "2" ] && touch "$BROKER_PREEMPT_FILE"; sleep 240; done ) & HB_PID=$!
ROCBLAS_USE_HIPBLASLT=0 /c/Users/hackathon/Documents/GitHub/arc-agi-2/.venv-rocm/Scripts/python.exe \
  select.py --model "$M" --tag s4-3b --limit 60 --batch 13 --pad-to 26 \
  --greedy-rounds 6 --oracle-samples 120 2>&1 | grep -vE "Loading weights|UserWarning|_ = torch"
