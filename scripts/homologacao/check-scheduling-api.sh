#!/usr/bin/env bash
# Homologação Fase 2 — API operacional Central de Agendamento (curl ponta a ponta).
# Uso:
#   export TOKEN="<jwt sem Bearer>"
#   bash ./scripts/homologacao/check-scheduling-api.sh
#
# Variáveis opcionais:
#   BASE_URL=http://localhost
#   BRANCH=ES|SC
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
API="${BASE_URL}/apps/api-delpi/scheduling"
CORE_API="${BASE_URL}/core-api"
BRANCH="${BRANCH:-ES}"
TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN (JWT do Portal — DevTools → GET /core-api/me → Authorization)." >&2
  exit 1
fi

AUTH=(-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -H "X-Delpi-Caller-App: central-agendamento")

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
      -H "Authorization: Bearer ${TOKEN}" \
      -H "X-Delpi-Caller-App: central-agendamento")"
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

SUFFIX="$(date +%s)"
START_ISO="$(python3 -c "from datetime import datetime, timedelta, timezone; s=datetime.now(timezone.utc)+timedelta(days=7); s=s.replace(hour=10, minute=0, second=0, microsecond=0); print(s.isoformat().replace('+00:00','Z'))")"
END_ISO="$(python3 -c "from datetime import datetime, timedelta, timezone; s=datetime.now(timezone.utc)+timedelta(days=7); s=s.replace(hour=11, minute=0, second=0, microsecond=0); print(s.isoformat().replace('+00:00','Z'))")"
OVERLAP_ISO="$(python3 -c "from datetime import datetime, timedelta, timezone; s=datetime.now(timezone.utc)+timedelta(days=7); s=s.replace(hour=10, minute=30, second=0, microsecond=0); print(s.isoformat().replace('+00:00','Z'))")"

echo "=== check-scheduling-api (filial ${BRANCH}) ==="

echo "[1/7] GET /core-api/me"
ME_JSON="$(curl_json GET "${CORE_API}/me")"
USER_NAME="$(python3 -c "import json,sys; print(json.load(sys.stdin)['name'])" <<<"$ME_JSON")"
echo "      usuário: ${USER_NAME}"

echo "[2/7] POST /resources (recurso homolog ${SUFFIX})"
RESOURCE_JSON="$(curl_json POST "${API}/resources" "$(cat <<EOF
{
  "branch_code": "${BRANCH}",
  "name": "Sala Homolog ${SUFFIX}",
  "resource_type": "meeting_room",
  "description": "Recurso criado pelo check-scheduling-api",
  "capacity": 8
}
EOF
)")"
assert_success_json "$RESOURCE_JSON"
RESOURCE_ID="$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])" <<<"$RESOURCE_JSON")"
echo "      resource_id: ${RESOURCE_ID}"

echo "[3/7] GET /resources?branch=${BRANCH}"
LIST_JSON="$(curl_json GET "${API}/resources?branch=${BRANCH}")"
assert_success_json "$LIST_JSON"

echo "[4/7] POST /bookings (reserva principal)"
BOOKING_JSON="$(curl_json POST "${API}/bookings" "$(cat <<EOF
{
  "branch_code": "${BRANCH}",
  "resource_id": "${RESOURCE_ID}",
  "title": "Homolog ${SUFFIX}",
  "notes": "check-scheduling-api",
  "start_at": "${START_ISO}",
  "end_at": "${END_ISO}"
}
EOF
)")"
assert_success_json "$BOOKING_JSON"
BOOKING_ID="$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])" <<<"$BOOKING_JSON")"
echo "      booking_id: ${BOOKING_ID}"

echo "[5/7] POST /bookings (conflito esperado 409)"
curl_json POST "${API}/bookings" "$(cat <<EOF
{
  "branch_code": "${BRANCH}",
  "resource_id": "${RESOURCE_ID}",
  "title": "Conflito ${SUFFIX}",
  "start_at": "${OVERLAP_ISO}",
  "end_at": "${END_ISO}"
}
EOF
)" "409" >/dev/null

echo "[6/7] PATCH /bookings/${BOOKING_ID}/cancel"
CANCEL_JSON="$(curl_json PATCH "${API}/bookings/${BOOKING_ID}/cancel")"
assert_success_json "$CANCEL_JSON"

echo "[7/7] PATCH /resources/${RESOURCE_ID} (desativar)"
DEACTIVATE_JSON="$(curl_json PATCH "${API}/resources/${RESOURCE_ID}" '{"active": false}')"
assert_success_json "$DEACTIVATE_JSON"

echo "[OK] check-scheduling-api"
