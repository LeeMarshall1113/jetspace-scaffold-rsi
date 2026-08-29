#!/usr/bin/env bash
# Replicate the off-target-effects measurement on the three remaining backbones.
# Sequential: each waits for amd-9070xt by name, takes its own lease, releases it.
# Cheapest first, so a partial result is still a useful one.
set -uo pipefail
cd "$(dirname "$0")"
M=/c/Users/hackathon/Documents/GitHub/arc-agi-2/models

run() {  # name path batch mem minutes
    echo "=========== $1 ==========="
    MODEL="$2" TAG="v3-$1" BATCH="$3" MEM_FRAC="$4" MINUTES="$5" bash queued_run.sh
    echo "=========== $1 exit=$? ==========="
}

run gemma4-e2b  "$M/gemma-4-e2b-it"            8 0.90  40
run qwen35-4b   "$M/qwen3.5-4b"                8 0.90 180
run qwen25c-7b  "$M/qwen2.5-coder-7b-instruct" 2 0.92 220
echo "ALL DONE"
