#!/usr/bin/env bash
# Smoke — plugin central-agendamento (assets + API recursos).
#
# Uso (exporte o TOKEN antes de rodar):
#   export TOKEN="<jwt sem Bearer>"
#   bash ./scripts/homologacao/check-central-agendamento.sh
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
CORE_API="${BASE_URL}/core-api"
SCHEDULING_API="${BASE_URL}/apps/api-delpi/scheduling"
TOKEN="${TOKEN:-}"

echo "[check] remoteEntry.js"
curl -fsSI "${BASE_URL}/apps/central-agendamento/assets/remoteEntry.js" | head -1

if [ -z "$TOKEN" ]; then
  echo "[skip] API resources (defina TOKEN antes de rodar o script)"
  echo "[OK] check-central-agendamento (parcial — sem JWT)"
  exit 0
fi

AUTH=(-H "Authorization: Bearer ${TOKEN}" -H "X-Delpi-Caller-App: central-agendamento")

echo "[check] JWT (/core-api/me)"
me_code="$(curl -sS -o /tmp/ca-me.json -w "%{http_code}" "${AUTH[@]}" "${CORE_API}/me")"
if [ "$me_code" != "200" ]; then
  echo "[ERRO] TOKEN inválido ou expirado (HTTP ${me_code}). Exporte um JWT novo antes de rodar:" >&2
  echo "  export TOKEN=\"\$(curl -s ... /core-api/me ...)\"" >&2
  cat /tmp/ca-me.json >&2
  exit 1
fi
user_name="$(python3 -c "import json; print(json.load(open('/tmp/ca-me.json'))['name'])")"
echo "      usuário: ${user_name}"

echo "[check] resources API (Filial ES)"
curl -fsS \
  "${SCHEDULING_API}/resources?branch=ES" \
  "${AUTH[@]}" \
  | python3 -c "import json,sys; b=json.load(sys.stdin); assert b.get('success'), b; print('OK resources', len(b.get('data',[])))"

echo "[OK] check-central-agendamento"
