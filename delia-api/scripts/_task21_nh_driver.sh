#!/bin/bash
# Task 21 — newheldout-only clean reps (GPU). Resumable per scenario.
cd /app || exit 1
LOGDIR=/app/.battery/task21
mkdir -p "$LOGDIR"
cp /app/.battery/env.local /tmp/env.local 2>/dev/null || true

NEW_SIDS=$(grep -ohE '_x\("nh_[a-z_0-9]+"' \
      scripts/local_orchestration_reliability_eval.py \
      | grep -oE '"nh_[a-z_0-9]+"' | tr -d '"' | sort -u)

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
}

for rep in 1 2 3; do
    LOG=$LOGDIR/newheldout_run${rep}.log
    for i in $(seq 1 30); do
        DONE=$(grep -oE '"s": "[a-z_0-9]+"' "$LOG" 2>/dev/null \
               | sed 's/"s": "//;s/"//' | sort -u)
        REMAIN=""
        for s in $NEW_SIDS; do
            echo "$DONE" | grep -qx "$s" || REMAIN="$REMAIN,$s"
        done
        REMAIN=${REMAIN#,}
        if [ -z "$REMAIN" ]; then
            echo "DONE newheldout rep=$rep attempt=$i" >> "$LOG"
            break
        fi
        echo "DRIVER newheldout rep=$rep attempt=$i remaining=$(echo "$REMAIN" | tr ',' '\n' | wc -l)" >> "$LOG"
        warm_gate
        CORPUS_SET=newheldout python3 scripts/local_orchestration_reliability_eval.py 1 "$REMAIN" >> "$LOG" 2>&1
        cp /tmp/local_reliability_runs.json "$LOGDIR/newheldout_run${rep}.runs.json" 2>/dev/null
        sleep 3
    done
done
echo "TASK21_NH_DRIVER complete $(date -u +%FT%TZ)" >> "$LOGDIR/driver.log"
