#!/usr/bin/env bash
# Smoke — Pulso de Produção (remoteEntry + health + API autenticada).
#
# Uso:
#   export TOKEN="<jwt portal sem Bearer>"   # preferido
#   bash ./scripts/homologacao/check-production-pulse.sh
#
# Fallback: se TOKEN vazio, usa API_DELPI_INTERNAL_SERVICE_TOKEN de infra/.env
# (aceito pela production-pulse-api; /core-api/me pode retornar 401 — validamos via /summary).
#
# Live ESP (E6.S2 — opcional):
#   export PP_LIVE_ESP=1
#   export PP_LIVE_ESP_IP=192.168.20.2
#
# Variáveis opcionais:
#   BASE_URL=http://localhost
#   BRANCH=01
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BASE_URL="${BASE_URL:-http://localhost}"
CORE_API="${BASE_URL}/core-api"
PP_API="${BASE_URL}/apps/production-pulse-api"
TOKEN="${TOKEN:-}"
BRANCH="${BRANCH:-01}"
CALLER="production-pulse"
PP_LIVE_ESP="${PP_LIVE_ESP:-0}"
PP_LIVE_ESP_IP="${PP_LIVE_ESP_IP:-192.168.20.2}"

resolve_token() {
  if [ -n "${TOKEN}" ]; then
    return 0
  fi
  local env_file="${REPO_ROOT}/infra/.env"
  if [ -f "${env_file}" ]; then
    TOKEN="$(grep '^API_DELPI_INTERNAL_SERVICE_TOKEN=' "${env_file}" | cut -d= -f2- || true)"
  fi
}

resolve_token

echo "[1/8] remoteEntry.js (MFE)"
curl -fsSI "${BASE_URL}/apps/production-pulse/assets/remoteEntry.js" | head -1

echo "[2/8] health (API)"
health_json="$(curl -fsS "${PP_API}/health")"
python3 -c "import json,sys; b=json.loads(sys.argv[1]); assert b.get('success'), b; assert b['data'].get('service')=='production-pulse-api', b" "$health_json"
echo "      OK production-pulse-api"

if [ -z "${TOKEN}" ]; then
  echo "[skip] rotas autenticadas (defina TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN em infra/.env)"
  echo "[OK] check-production-pulse (parcial — sem token)"
  exit 0
fi

AUTH=(-H "Authorization: Bearer ${TOKEN}" -H "X-Delpi-Caller-App: ${CALLER}")

echo "[3/8] autenticação"
me_code="$(curl -sS -o /tmp/pp-me.json -w "%{http_code}" "${AUTH[@]}" "${CORE_API}/me")"
if [ "$me_code" = "200" ]; then
  user_name="$(python3 -c "import json; print(json.load(open('/tmp/pp-me.json'))['name'])")"
  echo "      JWT portal OK — usuário: ${user_name}"
else
  summary_code="$(curl -sS -o /tmp/pp-auth-probe.json -w "%{http_code}" \
    "${PP_API}/summary?branch=${BRANCH}" "${AUTH[@]}")"
  if [ "$summary_code" = "200" ]; then
    echo "      service token OK (skip /core-api/me — HTTP ${me_code})"
  else
    echo "[ERRO] token rejeitado — /core-api/me=${me_code}, /summary=${summary_code}" >&2
    cat /tmp/pp-me.json >&2 2>/dev/null || true
    cat /tmp/pp-auth-probe.json >&2 2>/dev/null || true
    exit 1
  fi
fi

echo "[4/8] summary (filial ${BRANCH})"
curl -fsS "${PP_API}/summary?branch=${BRANCH}" "${AUTH[@]}" \
  | python3 -c "import json,sys; b=json.load(sys.stdin); assert b.get('success'), b; print('OK summary', list((b.get('data') or {}).keys())[:4])"

echo "[5/8] list devices"
curl -fsS "${PP_API}/devices?branch=${BRANCH}" "${AUTH[@]}" \
  | python3 -c "import json,sys; b=json.load(sys.stdin); assert b.get('success'), b; items=(b.get('data') or {}).get('items') or []; print('OK devices', len(items))"

echo "[6/8] catalog drivers"
curl -fsS "${PP_API}/catalog/drivers" "${AUTH[@]}" \
  | python3 -c "import json,sys; b=json.load(sys.stdin); assert b.get('success'), b; drivers=(b.get('data') or {}).get('drivers') or []; assert drivers, 'sem drivers'; print('OK drivers', len(drivers))"

echo "[7/8] operator placements (403 = sem permissão operator)"
op_code="$(curl -sS -o /tmp/pp-op.json -w "%{http_code}" \
  "${PP_API}/operator/placements?branch=${BRANCH}" "${AUTH[@]}")"
if [ "$op_code" = "200" ]; then
  python3 -c "import json; b=json.load(open('/tmp/pp-op.json')); assert b.get('success'), b; print('OK operator placements', len(b.get('data') or []))"
elif [ "$op_code" = "403" ]; then
  echo "      skip operator (403)"
else
  echo "[ERRO] operator/placements HTTP ${op_code}" >&2
  cat /tmp/pp-op.json >&2
  exit 1
fi

echo "[8/8] CRUD smoke (create + delete)"
suffix="$(python3 -c 'import random; print(random.randint(2,250))')"
probe_ip="192.168.250.${suffix}"
create_body="$(cat <<EOF
{"name":"Homologação smoke","branch":"${BRANCH}","ipAddress":"${probe_ip}","driverKey":"esp8266_counter_v1","pollIntervalSeconds":30,"enabled":true}
EOF
)"
create_code="$(curl -sS -o /tmp/pp-create.json -w "%{http_code}" \
  -X POST "${PP_API}/devices" \
  -H "Content-Type: application/json" \
  "${AUTH[@]}" \
  -d "${create_body}")"
if [ "$create_code" = "201" ]; then
  device_id="$(python3 -c "import json; print(json.load(open('/tmp/pp-create.json'))['data']['id'])")"
  echo "      created device ${device_id} (${probe_ip})"
  delete_code="$(curl -sS -o /tmp/pp-delete.json -w "%{http_code}" \
    -X DELETE "${PP_API}/devices/${device_id}" "${AUTH[@]}")"
  if [ "$delete_code" != "200" ]; then
    echo "[ERRO] DELETE device HTTP ${delete_code}" >&2
    cat /tmp/pp-delete.json >&2
    exit 1
  fi
  echo "      deleted (soft) OK"
elif [ "$create_code" = "403" ]; then
  echo "      skip CRUD (403 — sem production-pulse.devices.manage)"
else
  echo "[ERRO] POST /devices HTTP ${create_code}" >&2
  cat /tmp/pp-create.json >&2
  exit 1
fi

if [ "${PP_LIVE_ESP}" = "1" ]; then
  echo "[live] test-probe ESP piloto (${PP_LIVE_ESP_IP})"
  probe_body="$(cat <<EOF
{"branch":"${BRANCH}","ipAddress":"${PP_LIVE_ESP_IP}","driverKey":"esp8266_counter_v1"}
EOF
)"
  probe_code="$(curl -sS -o /tmp/pp-probe.json -w "%{http_code}" \
    -X POST "${PP_API}/devices/test-probe" \
    -H "Content-Type: application/json" \
    "${AUTH[@]}" \
    -d "${probe_body}")"
  if [ "$probe_code" = "200" ]; then
    python3 -c "
import json, sys
b = json.load(open('/tmp/pp-probe.json'))
assert b.get('success'), b
data = b.get('data') or {}
if not data.get('online'):
    err = data.get('error') or 'offline'
    print(f'[ERRO] ESP {sys.argv[1]} inacessível ({err})', file=sys.stderr)
    sys.exit(1)
counter = (data.get('metrics') or {}).get('counter')
assert isinstance(counter, int), b
print('OK live counter', counter)
" "${PP_LIVE_ESP_IP}"
  elif [ "$probe_code" = "403" ]; then
    echo "      skip live probe (403 — sem manage)"
  else
    echo "[AVISO] test-probe ESP HTTP ${probe_code} — verifique rede LAN / network_mode: host" >&2
    cat /tmp/pp-probe.json >&2
    exit 1
  fi
fi

echo "[OK] check-production-pulse"
