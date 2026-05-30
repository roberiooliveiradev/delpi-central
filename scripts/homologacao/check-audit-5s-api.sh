#!/usr/bin/env bash
# Homologação Fase 2 — API operacional Auditoria 5S (curl ponta a ponta).
# Uso:
#   export TOKEN="<jwt sem Bearer>"
#   bash ./scripts/homologacao/check-audit-5s-api.sh
#
# Variáveis opcionais:
#   BASE_URL=http://localhost
#   BRANCH=01|02
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
API="${BASE_URL}/apps/api-delpi/quality/audit-5s"
CORE_API="${BASE_URL}/core-api"
BRANCH="${BRANCH:-01}"
TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN (JWT do Portal — DevTools → GET /core-api/me → Authorization)." >&2
  exit 1
fi

AUTH=(-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json")

fail() {
  echo "[ERRO] $*" >&2
  exit 1
}

curl_json() {
  local method="$1"
  local url="$2"
  local data="${3:-}"
  local expect="${4:-200}"

  local body_file
  body_file="$(mktemp)"
  local http_code

  if [ -n "$data" ]; then
    http_code="$(curl -sS -o "$body_file" -w "%{http_code}" -X "$method" "$url" \
      "${AUTH[@]}" -d "$data")"
  else
    http_code="$(curl -sS -o "$body_file" -w "%{http_code}" -X "$method" "$url" \
      -H "Authorization: Bearer ${TOKEN}")"
  fi

  if [ "$http_code" != "$expect" ]; then
    echo "[ERRO] ${method} ${url} → HTTP ${http_code} (esperado ${expect})" >&2
    cat "$body_file" >&2
    rm -f "$body_file"
    exit 1
  fi

  cat "$body_file"
  rm -f "$body_file"
}

assert_success_json() {
  python3 -c "
import json, sys
b = json.load(sys.stdin)
assert b.get('success') is True, b
" <<<"$1"
}

echo "=== check-audit-5s-api (filial ${BRANCH}) ==="

echo "[1/8] GET /core-api/me"
ME_JSON="$(curl_json GET "${CORE_API}/me")"
USER_ID="$(python3 -c "import json,sys; print(json.load(sys.stdin)['id'])" <<<"$ME_JSON")"
USER_NAME="$(python3 -c "import json,sys; print(json.load(sys.stdin)['name'])" <<<"$ME_JSON")"
echo "      usuário: ${USER_NAME} (${USER_ID})"

echo "[2/8] GET /criteria (48 critérios)"
CRITERIA_JSON="$(curl_json GET "${API}/criteria")"
assert_success_json "$CRITERIA_JSON"
CRITERIA_COUNT="$(python3 -c "import json,sys; print(len(json.load(sys.stdin)['data']))" <<<"$CRITERIA_JSON")"
if [ "$CRITERIA_COUNT" != "48" ]; then
  fail "esperado 48 critérios, obteve ${CRITERIA_COUNT}"
fi
echo "      OK criteria ${CRITERIA_COUNT}"

echo "[3/8] POST /areas"
AREA_NAME="Homolog API ${BRANCH} $(date +%Y%m%d-%H%M%S)"
AREA_JSON="$(curl_json POST "${API}/areas" "$(python3 -c "
import json
print(json.dumps({'branch_code': '${BRANCH}', 'name': '''${AREA_NAME}'''}))
")")"
assert_success_json "$AREA_JSON"
AREA_ID="$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])" <<<"$AREA_JSON")"
echo "      área: ${AREA_NAME} (${AREA_ID})"

echo "[4/8] POST /audits"
AUDIT_DATE="$(date +%Y-%m-%d)"
AUDIT_JSON="$(curl_json POST "${API}/audits" "$(python3 -c "
import json
print(json.dumps({
  'branch_code': '${BRANCH}',
  'audit_date': '${AUDIT_DATE}',
  'area_id': '${AREA_ID}',
  'area_responsible': 'Responsável Homologação',
  'shift': 'TURNO_1',
  'auditors': [{'user_id': '${USER_ID}', 'display_name': '''${USER_NAME}'''}],
}))
")")"
assert_success_json "$AUDIT_JSON"
AUDIT_ID="$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])" <<<"$AUDIT_JSON")"
AUDIT_CODE="$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['audit_code'])" <<<"$AUDIT_JSON")"
PENDING="$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['progress']['pending'])" <<<"$AUDIT_JSON")"
echo "      auditoria: ${AUDIT_CODE} (${AUDIT_ID}), pendentes=${PENDING}"

echo "[5/8] POST /complete-evaluation (deve falhar — notas incompletas)"
BLOCK_BODY="$(mktemp)"
BLOCK_CODE="$(curl -sS -o "$BLOCK_BODY" -w "%{http_code}" -X POST \
  "${API}/audits/${AUDIT_ID}/complete-evaluation" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{}")"
if [ "$BLOCK_CODE" != "422" ]; then
  echo "[ERRO] esperava HTTP 422, obteve ${BLOCK_CODE}" >&2
  cat "$BLOCK_BODY" >&2
  rm -f "$BLOCK_BODY"
  exit 1
fi
rm -f "$BLOCK_BODY"
echo "      OK bloqueio HTTP 422"

echo "[6/8] PUT respostas (48 critérios — nota 5)"
echo "$AUDIT_JSON" > /tmp/a5s_audit_create.json
python3 -c "
import json
audit = json.load(open('/tmp/a5s_audit_create.json'))['data']
json.dump([c['id'] for c in audit['criteria']], open('/tmp/a5s_criterion_ids.json', 'w'))
"

SCORED=0
for CRITERION_ID in $(python3 -c "import json; print(' '.join(json.load(open('/tmp/a5s_criterion_ids.json'))))"); do
  RESP_JSON="$(curl_json PUT "${API}/audits/${AUDIT_ID}/responses/${CRITERION_ID}" \
    '{"score":5,"is_not_applicable":false,"version":null}')"
  assert_success_json "$RESP_JSON"
  SCORED=$((SCORED + 1))
done
echo "      OK ${SCORED} respostas gravadas"

echo "[7/8] POST /complete-evaluation"
COMPLETE_JSON="$(curl_json POST "${API}/audits/${AUDIT_ID}/complete-evaluation" "{}")"
assert_success_json "$COMPLETE_JSON"
STATUS="$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['status'])" <<<"$COMPLETE_JSON")"
OVERALL="$(python3 -c "import json,sys; d=json.load(sys.stdin)['data']; print(d.get('scores',{}).get('overall_percentual'))" <<<"$COMPLETE_JSON")"
if [ "$STATUS" != "evaluation_complete" ]; then
  fail "status esperado evaluation_complete, obteve ${STATUS}"
fi
echo "      OK status=${STATUS}, % geral=${OVERALL}"

echo "[8/8] GET /audits/{id}"
DETAIL_JSON="$(curl_json GET "${API}/audits/${AUDIT_ID}")"
assert_success_json "$DETAIL_JSON"
DETAIL_PENDING="$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['progress']['pending'])" <<<"$DETAIL_JSON")"
if [ "$DETAIL_PENDING" != "0" ]; then
  fail "esperado 0 pendentes no detalhe, obteve ${DETAIL_PENDING}"
fi
echo "      OK detalhe confirmado (0 pendentes)"

rm -f /tmp/a5s_criterion_ids.json /tmp/a5s_audit_create.json

echo ""
echo "[OK] check-audit-5s-api"
echo "     audit_code=${AUDIT_CODE}"
echo "     audit_id=${AUDIT_ID}"
echo "     area=${AREA_NAME}"
