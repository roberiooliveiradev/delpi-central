#!/bin/bash
# Task 22 — audit evals: main-47 x1 + heldout-20 x1 regression,
# t22heldout-21 x3 acceptance. Resumable per scenario.
cd /app || exit 1
LOGDIR=/app/.battery/task22
mkdir -p "$LOGDIR"
cp /app/.battery/env.local /tmp/env.local 2>/dev/null || true

sids_for() {
    case "$1" in
        main)
            # Canonical 47-scenario main list (same as Task 21 driver).
            echo "a_playlist_ctx a_playlist_noctx ambig_proc b_bala_phrase b_faston b_illustrative b_pino biz_bala3 biz_code biz_o2_2 biz_pino c_davi_explicit c_teo_explicit c_teo_proc_id c_vista_explicit cmp_legit cmp_partial cont_explicit cont_nonauth cont_obs cont_prior ctrl_oi ctrl_sipoc d_catalog_exec d_catalog_only disc_candidate disc_exec disc_none e_proc_followup e_prod_followup exhaust guide_caps guide_proc guide_term missing_email neg_inject neg_nobiz neg_planetas neg_scope neg_sentimento neg_write nom_colloq nom_incomplete nom_multi nom_technical ord_latest surf_inquiry" | tr ' ' '\n'
            ;;
        heldout)
            grep -ohE '"ho_[a-z_0-9]+"' \
              scripts/local_orchestration_reliability_eval.py \
              | tr -d '"' | sort -u
            ;;
        t22heldout)
            grep -ohE '"t2_[a-z_0-9]+"' \
              scripts/local_orchestration_reliability_eval.py \
              | tr -d '"' | sort -u
            ;;
    esac
}

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
    urllib.request.urlopen("http://delpi-ollama:11434/api/tags", timeout=8)
except Exception:
    ok = False
exit(0 if ok else 1)
' && break
        sleep 5
    done
}

run_set() {
    local set=$1 rep=$2
    local LOG=$LOGDIR/${set}_run${rep}.log
    local SIDS=$(sids_for "$set")
    for i in $(seq 1 30); do
        local DONE=$(grep -oE '"s": "[a-z_0-9]+"' "$LOG" 2>/dev/null \
            | sed 's/"s": "//;s/"//' | sort -u)
        local REMAIN=""
        for s in $SIDS; do
            echo "$DONE" | grep -qx "$s" || REMAIN="$REMAIN,$s"
        done
        REMAIN=${REMAIN#,}
        if [ -z "$REMAIN" ]; then
            echo "DONE $set rep=$rep attempt=$i" >> "$LOG"
            return
        fi
        echo "DRIVER $set rep=$rep attempt=$i remaining=$(echo "$REMAIN" | tr ',' '\n' | wc -l)" >> "$LOG"
        warm_gate
        CORPUS_SET=$set python3 scripts/local_orchestration_reliability_eval.py 1 "$REMAIN" >> "$LOG" 2>&1
        cp /tmp/local_reliability_runs.json "$LOGDIR/${set}_run${rep}.runs.json" 2>/dev/null
        sleep 3
    done
}

run_set main 1
run_set heldout 1
run_set t22heldout 1
run_set t22heldout 2
run_set t22heldout 3
echo "TASK22_DRIVER complete $(date -u +%FT%TZ)" >> "$LOGDIR/driver.log"
