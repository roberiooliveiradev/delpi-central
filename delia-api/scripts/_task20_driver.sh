#!/bin/bash
# Task 20 acceptance driver: 3x main corpus + 3x held-out corpus on the
# SAME frozen candidate. Per-run JSONL logs under .battery/task20/;
# resumes per-scenario on restart. No code may change between runs.
cd /app || exit 1
LOGDIR=/app/.battery/task20
mkdir -p "$LOGDIR"
cp /app/.battery/env.local /tmp/env.local 2>/dev/null || true

MAIN_SIDS=$(grep -ohE '(_x|_product)\("[a-z_0-9]+"|sid="[a-z_0-9]+"' \
      scripts/local_orchestration_reliability_eval.py \
      scripts/semantic_fidelity_eval.py \
      | grep -oE '"[a-z_0-9]+"' | tr -d '"' | grep -v '^ho_' | sort -u)
HELD_SIDS=$(grep -ohE '_x\("ho_[a-z_0-9]+"' \
      scripts/local_orchestration_reliability_eval.py \
      | grep -oE '"ho_[a-z_0-9]+"' | tr -d '"' | sort -u)

warm_gate() {
    for i in $(seq 1 90); do
        python3 -c '
import urllib.request, urllib.error
ok = True
try:
    urllib.request.urlopen(urllib.request.Request(
        "http://delpi-gateway/auth/realms/delpi/protocol/openid-connect/token",
        data=b"x=1", headers={"Host": "localhost"}), timeout=8)
except urllib.error.HTTPError as e:
    ok = e.code in (400, 401, 405)
except Exception:
    ok = False
try:
    urllib.request.urlopen(
        "http://delpi-ollama:11434/api/tags", timeout=8)
except Exception:
    ok = False
exit(0 if ok else 1)
' && break
        sleep 5
    done
    MODEL=${DELIA_LLM_MODEL:-qwen3:4b-instruct-2507-q4_K_M}
    python3 - "$MODEL" <<'PY'
import json, sys, urllib.request
try:
    urllib.request.urlopen(urllib.request.Request(
        "http://delpi-ollama:11434/api/generate",
        data=json.dumps({"model": sys.argv[1], "prompt": "ok",
                         "stream": False,
                         "options": {"num_predict": 1}}).encode()),
        timeout=180)
except Exception:
    pass
PY
}

run_set() {
    local SET=$1 SIDS=$2 REP=$3
    local LOG=$LOGDIR/${SET}_run${REP}.log
    for i in $(seq 1 30); do
        DONE=$(grep -oE '"s": "[a-z_0-9]+"' "$LOG" 2>/dev/null \
               | sed 's/"s": "//;s/"//' | sort -u)
        REMAIN=""
        for s in $SIDS; do
            echo "$DONE" | grep -qx "$s" || REMAIN="$REMAIN,$s"
        done
        REMAIN=${REMAIN#,}
        if [ -z "$REMAIN" ]; then
            echo "DONE $SET rep=$REP attempt=$i" >> "$LOG"
            return 0
        fi
        echo "DRIVER $SET rep=$REP attempt=$i remaining=$(echo "$REMAIN" | tr ',' '\n' | wc -l)" >> "$LOG"
        warm_gate
        CORPUS_SET=$SET python3 scripts/local_orchestration_reliability_eval.py 1 "$REMAIN" >> "$LOG" 2>&1
        cp /tmp/local_reliability_runs.json "$LOGDIR/${SET}_run${REP}.runs.json" 2>/dev/null
        sleep 5
    done
    return 1
}

echo "TASK20_DRIVER start $(date -u +%FT%TZ)" > "$LOGDIR/driver.log"
for rep in 1 2 3; do
    run_set main "$MAIN_SIDS" "$rep"
    run_set heldout "$HELD_SIDS" "$rep"
done
echo "TASK20_DRIVER complete $(date -u +%FT%TZ)" >> "$LOGDIR/driver.log"
