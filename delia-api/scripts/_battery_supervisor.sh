#!/bin/bash
# Resumable reliability-battery supervisor.
# Appends per-scenario JSONL lines to the log; on restart (container or
# WSL bounce) it re-enters, skips completed scenario ids, and resumes.
cd /app || exit 1
LOG=/app/.battery/eval.log
mkdir -p /app/.battery
cp /app/.battery/env.local /tmp/env.local 2>/dev/null || true

ALL=$(grep -ohE '(_x|_product)\("[a-z_0-9]+"|sid="[a-z_0-9]+"' \
      scripts/local_orchestration_reliability_eval.py \
      scripts/semantic_fidelity_eval.py \
      | grep -oE '"[a-z_0-9]+"' | tr -d '"' | sort -u)

warm_gate() {
    # Wait for Keycloak, delia-api and a warm Ollama before burning a
    # scenario on cold-model timeouts.
    for i in $(seq 1 90); do
        python3 -c '
import urllib.request, urllib.error, os
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
    # Warm the model: a 1-token generate forces the weights into memory.
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

for i in $(seq 1 30); do
    DONE=$(grep -oE '"s": "[a-z_0-9]+"' "$LOG" 2>/dev/null \
           | sed 's/"s": "//;s/"//' | sort -u)
    REMAIN=""
    for s in $ALL; do
        echo "$DONE" | grep -qx "$s" || REMAIN="$REMAIN,$s"
    done
    REMAIN=${REMAIN#,}
    if [ -z "$REMAIN" ]; then
        echo "ALL_DONE attempt=$i" >> "$LOG"
        break
    fi
    echo "SUPERVISOR attempt=$i remaining=$(echo "$REMAIN" | tr ',' '\n' | wc -l)" >> "$LOG"
    warm_gate
    python3 scripts/local_orchestration_reliability_eval.py 1 "$REMAIN" >> "$LOG" 2>&1
    cp /tmp/local_reliability_runs.json /app/.battery/runs_latest.json 2>/dev/null
    sleep 5
done
