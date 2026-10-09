#!/usr/bin/env bash
# G5 — Runtime acceptance: Transformômetro ↔ BPMN Modeler (explicit reference).
# LOCAL INTEGRATION RUNTIME only. Requires gateway + Keycloak + both APIs up.
# Identities: ~/.bpmn-e2e-env (BPMN_E2E_USER_*/BPMN_E2E_PASS_*).
#
# Contract under test (ADR-005):
#   reference = (model_id, revision_number) stored in transformometro schema;
#   write is fail-closed on Modeler resolution; read degrades gracefully;
#   replace exposes only the *new* reference in the response — the previous
#   value is authoritative in audit_logs (old_reference/new_reference).
set -u

BASE="${G5_BASE_URL:-http://localhost}"
TM="$BASE/apps/transformometro-api/transformometro"
BPMN="$BASE/apps/bpmn-modeler-api"
KC_TOKEN="$BASE/auth/realms/delpi/protocol/openid-connect/token"
PG="docker exec delpi-postgres-plugins psql -U plugins_user -d plugins_hub -t -A -c"

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf 'ok %02d — %s\n' "$1" "$2"; }
fail() { FAIL=$((FAIL+1)); printf 'FAIL %02d — %s :: %s\n' "$1" "$2" "$3"; }

# shellcheck disable=SC1091
source ~/.bpmn-e2e-env

token() {
  local user="$1" pass="$2"
  curl -s "$KC_TOKEN" -d "client_id=delpi-central" -d grant_type=password \
    -d "username=$user" -d "password=$pass" | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])'
}
jget() { python3 -c "import json,sys;d=json.loads(sys.argv[1]);print($2)" "$1"; }

MGR=$(token "$BPMN_E2E_USER_MANAGER" "$BPMN_E2E_PASS_MANAGER")
VWR=$(token "$BPMN_E2E_USER_VIEWER" "$BPMN_E2E_PASS_VIEWER")
[ -n "$MGR" ] && [ -n "$VWR" ] || { echo "token grant failed"; exit 2; }

AUTH_MGR="Authorization: Bearer $MGR"
AUTH_VWR="Authorization: Bearer $VWR"
CT="Content-Type: application/json"

# ---- fixture setup ------------------------------------------------------
RESP=$(curl -s "$TM/processos" -X POST -H "$AUTH_MGR" -H "$CT" \
  -d '{"nome_processo":"G5 ACC Processo","status_processo":"ativo"}')
PID=$(jget "$RESP" 'd["data"]["processo_id"]' 2>/dev/null || echo "")
if [ -n "$PID" ]; then ok 1 "fixture: processo criado ($PID)"; else fail 1 "create processo" "$RESP"; fi

RESP=$(curl -s "$BPMN/models" -X POST -H "$AUTH_MGR" -H "$CT" \
  -d '{"display_name":"G5 ACC Modelo A"}')
MID=$(jget "$RESP" 'd["data"]["model_id"]' 2>/dev/null || echo "")
if [ -n "$MID" ]; then ok 2 "fixture: modelo BPMN criado ($MID)"; else fail 2 "create model" "$RESP"; fi

WC='<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="d_g5acc" targetNamespace="urn:g5acc"><bpmn:process id="p1"><bpmn:startEvent id="s1"/><bpmn:task id="t1"/><bpmn:endEvent id="e1"/><bpmn:sequenceFlow id="f1" sourceRef="s1" targetRef="t1"/><bpmn:sequenceFlow id="f2" sourceRef="t1" targetRef="e1"/></bpmn:process></bpmn:definitions>'
VER=$(curl -s "$BPMN/models/$MID" -H "$AUTH_MGR" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["version"])')
RESP=$(curl -s "$BPMN/models/$MID/working-copy" -X PUT -H "$AUTH_MGR" \
  -H "If-Match: \"v$VER\"" -H "Content-Type: application/xml" -d "$WC")
if echo "$RESP" | grep -q '"success": *true\|version'; then ok 3 "fixture: working copy salvo"; else fail 3 "save working copy" "$RESP"; fi

VER=$(curl -s "$BPMN/models/$MID" -H "$AUTH_MGR" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["version"])')
RESP=$(curl -s -w '\n%{http_code}' "$BPMN/models/$MID/revisions" -X POST -H "$AUTH_MGR" \
  -H "If-Match: \"v$VER\"" -H "$CT" -d '{"name":"R1 acceptance"}')
CODE=$(tail -1 <<<"$RESP")
if [ "$CODE" = "201" ]; then ok 4 "fixture: revisão R1 criada"; else fail 4 "create revision R1" "$RESP"; fi

# ---- contract checks ----------------------------------------------------
RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -H "$AUTH_MGR")
if [ "$(jget "$RESP" 'd["data"]["reference"]' 2>/dev/null)" = "None" ]; then ok 5 "GET reference — vazio"; else fail 5 "empty reference" "$RESP"; fi

RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -X PUT -H "$AUTH_MGR" -H "$CT" \
  -d "{\"model_id\":\"$MID\",\"revision_number\":1}")
if [ "$(jget "$RESP" 'd["data"]["reference"]["revision_number"]' 2>/dev/null)" = "1" ]; then
  ok 6 "PUT link A/R1"
else fail 6 "link A/R1" "$RESP"; fi

RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -H "$AUTH_MGR")
STATE=$(jget "$RESP" 'd["data"]["resolved"]["state"]' 2>/dev/null)
REV=$(jget "$RESP" 'd["data"]["reference"]["revision_number"]' 2>/dev/null)
NAME=$(jget "$RESP" 'd["data"]["resolved"]["model_display_name"]' 2>/dev/null)
if [ "$STATE" = "resolved" ] && [ "$REV" = "1" ] && [ "$NAME" = "G5 ACC Modelo A" ]; then
  ok 7 "read-back resolved: A/R1 display_name derivado"
else fail 7 "resolved read-back" "$RESP"; fi

RESP=$(curl -s -w '\n%{http_code}' "$TM/processos/$PID/bpmn-reference" -X PUT -H "$AUTH_MGR" -H "$CT" \
  -d "{\"model_id\":\"$MID\",\"revision_number\":999}")
CODE=$(tail -1 <<<"$RESP")
BACK=$(curl -s "$TM/processos/$PID/bpmn-reference" -H "$AUTH_MGR" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["reference"]["revision_number"])')
if [ "$CODE" -ge 400 ] && [ "$BACK" = "1" ]; then ok 8 "revisão inexistente rejeitada, vínculo intacto"; else fail 8 "missing revision" "$RESP"; fi

RESP=$(curl -s -w '\n%{http_code}' "$TM/processos/$PID/bpmn-reference" -X PUT -H "$AUTH_VWR" -H "$CT" \
  -d "{\"model_id\":\"$MID\",\"revision_number\":1}")
CODE=$(tail -1 <<<"$RESP")
if [ "$CODE" -ge 400 ] && [ "$CODE" != "500" ]; then ok 9 "cross-owner/foreign PUT negado (HTTP $CODE, sem leak)"; else fail 9 "viewer PUT" "$RESP"; fi

# create R2 — exige mudança no working copy (BPMN recusa NO_CHANGES)
WC2="${WC/t1\"\/>/t1\" name=\"Etapa rev2\"\/>}"
VER=$(curl -s "$BPMN/models/$MID" -H "$AUTH_MGR" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["version"])')
curl -s -o /dev/null "$BPMN/models/$MID/working-copy" -X PUT -H "$AUTH_MGR" \
  -H "If-Match: \"v$VER\"" -H "Content-Type: application/xml" -d "$WC2"
VER=$(curl -s "$BPMN/models/$MID" -H "$AUTH_MGR" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["version"])')
RESP=$(curl -s -w '\n%{http_code}' "$BPMN/models/$MID/revisions" -X POST -H "$AUTH_MGR" \
  -H "If-Match: \"v$VER\"" -H "$CT" -d '{"name":"R2 acceptance"}')
CODE=$(tail -1 <<<"$RESP")
if [ "$CODE" = "201" ]; then ok 10 "fixture: revisão R2 criada"; else fail 10 "create revision R2" "$RESP"; fi

RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -H "$AUTH_MGR")
REV=$(jget "$RESP" 'd["data"]["reference"]["revision_number"]')
LATEST=$(jget "$RESP" 'd["data"]["resolved"]["latest_revision_number"]')
if [ "$REV" = "1" ] && [ "$LATEST" = "2" ]; then ok 11 "NO auto-follow: linked=R1 latest=R2"; else fail 11 "auto-follow" "$RESP"; fi

RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -X PUT -H "$AUTH_MGR" -H "$CT" \
  -d "{\"model_id\":\"$MID\",\"revision_number\":2}")
if [ "$(jget "$RESP" 'd["data"]["reference"]["revision_number"]')" = "2" ]; then ok 12 "replace explícito → R2 (response contém apenas o novo)"; else fail 12 "replace R2" "$RESP"; fi

RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -H "$AUTH_MGR")
if [ "$(jget "$RESP" 'd["data"]["reference"]["revision_number"]')" = "2" ]; then ok 13 "authoritative read-back R2"; else fail 13 "read-back R2" "$RESP"; fi

AUDIT=$($PG "SELECT action || '|' || COALESCE(payload_json->'old_reference'->>'revision_number','null') || '->' || COALESCE(payload_json->'new_reference'->>'revision_number','null') FROM transformometro.audit_logs WHERE entity_type='processo_bpmn_reference' AND entity_id='$PID' ORDER BY created_at" | tr '\n' ';')
echo "  audit: $AUDIT"
if echo "$AUDIT" | grep -q 'update|1->2'; then ok 14 "audit update: old=R1 new=R2"; else fail 14 "audit old/new" "$AUDIT"; fi

RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -X DELETE -H "$AUTH_MGR")
if [ "$(jget "$RESP" 'd["data"]["reference"]' 2>/dev/null)" = "None" ]; then ok 15 "unlink → referência removida"; else fail 15 "unlink" "$RESP"; fi

RESP=$(curl -s -o /dev/null -w '%{http_code}' "$BPMN/models/$MID" -H "$AUTH_MGR")
if [ "$RESP" = "200" ]; then ok 16 "unlink não altera Modeler (model A intacto)"; else fail 16 "model intact" "$RESP"; fi

# ---- Modeler-down behaviour (LOCAL INTEGRATION RUNTIME) ------------------
docker stop delpi-bpmn-modeler-api >/dev/null 2>&1
sleep 2

CODE=$(curl -s -o /dev/null -w '%{http_code}' "$TM/processos/$PID" -H "$AUTH_MGR")
if [ "$CODE" = "200" ]; then ok 17 "Modeler down: GET processo sobrevive"; else fail 17 "process read w/ modeler down" "$CODE"; fi

RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -H "$AUTH_MGR")
# relink first to have a stored reference during outage
docker start delpi-bpmn-modeler-api >/dev/null 2>&1
sleep 4
curl -s "$TM/processos/$PID/bpmn-reference" -X PUT -H "$AUTH_MGR" -H "$CT" \
  -d "{\"model_id\":\"$MID\",\"revision_number\":2}" >/dev/null
docker stop delpi-bpmn-modeler-api >/dev/null 2>&1
sleep 2
RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -H "$AUTH_MGR")
STATE=$(jget "$RESP" 'd["data"]["resolved"]["state"]' 2>/dev/null)
REV=$(jget "$RESP" 'd["data"]["reference"]["revision_number"]' 2>/dev/null)
if [ "$STATE" = "unavailable" ] && [ "$REV" = "2" ]; then ok 18 "Modeler down: referência preservada + resolved=unavailable"; else fail 18 "degraded read" "$RESP"; fi

CODE=$(curl -s -o /dev/null -w '%{http_code}' "$TM/processos/$PID/bpmn-reference" -X PUT -H "$AUTH_MGR" -H "$CT" \
  -d "{\"model_id\":\"$MID\",\"revision_number\":2}")
if [ "$CODE" = "503" ]; then ok 19 "Modeler down: PUT fail-closed 503"; else fail 19 "write fail-closed" "$CODE"; fi

docker start delpi-bpmn-modeler-api >/dev/null 2>&1
sleep 4
RESP=$(curl -s "$TM/processos/$PID/bpmn-reference" -H "$AUTH_MGR")
STATE=$(jget "$RESP" 'd["data"]["resolved"]["state"]' 2>/dev/null)
if [ "$STATE" = "resolved" ]; then ok 20 "recovery: resolved novamente"; else fail 20 "recovery" "$RESP"; fi

echo "----------------------------------------"
echo "G5 RUNTIME ACCEPTANCE: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
