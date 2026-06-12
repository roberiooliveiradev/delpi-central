#!/usr/bin/env bash
# Smoke test — gateway expõe maintenance-api (JSON, não HTML do portal).
#
# Uso:
#   bash scripts/homologacao/check-maintenance-prod.sh
#   BASE_URL=https://minhadelpi.com.br bash scripts/homologacao/check-maintenance-prod.sh
set -euo pipefail

BASE_URL="${BASE_URL:-https://minhadelpi.com.br}"
HEALTH_URL="${BASE_URL}/apps/maintenance-api/maintenance/health"
MFE_URL="${BASE_URL}/apps/maintenance/assets/remoteEntry.js"

fail() {
  echo "[ERRO] $*" >&2
  exit 1
}

echo "=== check-maintenance-prod (${BASE_URL}) ==="

echo "[1/3] GET maintenance-api health"
BODY="$(mktemp)"
CODE="$(curl -sS -o "$BODY" -w "%{http_code}" "$HEALTH_URL")"
if [ "$CODE" != "200" ]; then
  fail "${HEALTH_URL} → HTTP ${CODE}"
fi
if head -c 20 "$BODY" | grep -qi '<!doctype\|<html'; then
  echo "Resposta (início):" >&2
  head -c 200 "$BODY" >&2
  echo "" >&2
  fail "Gateway devolve HTML do portal em ${HEALTH_URL}. Recrie gateway + maintenance-api no servidor."
fi
python3 -c "
import json, sys
p = json.load(open('$BODY'))
assert p.get('module') == 'maintenance' or p.get('status'), p
" || fail "JSON inesperado em ${HEALTH_URL}"
rm -f "$BODY"
echo "      OK JSON maintenance/health"

echo "[2/3] GET maintenance MFE remoteEntry"
CODE="$(curl -sS -o /dev/null -w "%{http_code}" "$MFE_URL")"
if [ "$CODE" != "200" ]; then
  fail "${MFE_URL} → HTTP ${CODE}"
fi
echo "      OK remoteEntry.js"

echo "[3/3] GET /apps/maintenance-api/health (serviço)"
ROOT_HEALTH="${BASE_URL}/apps/maintenance-api/health"
BODY="$(mktemp)"
CODE="$(curl -sS -o "$BODY" -w "%{http_code}" "$ROOT_HEALTH")"
if [ "$CODE" != "200" ]; then
  fail "${ROOT_HEALTH} → HTTP ${CODE}"
fi
if head -c 20 "$BODY" | grep -qi '<!doctype\|<html'; then
  fail "Gateway devolve HTML em ${ROOT_HEALTH}"
fi
python3 -c "
import json, sys
p = json.load(open('$BODY'))
assert p.get('service') == 'maintenance-api', p
" || fail "JSON inesperado em ${ROOT_HEALTH}"
rm -f "$BODY"
echo "      OK JSON service health"

echo ""
echo "[OK] maintenance-api exposta no gateway"
