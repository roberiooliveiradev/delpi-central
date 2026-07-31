#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${MANIFEST:-$SCRIPT_DIR/../reports.manifest.json}"
BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN (JWT do portal com apps.manage ou superadmin)."
  exit 1
fi

if [ ! -f "$MANIFEST" ]; then
  echo "[ERRO] Manifesto não encontrado: $MANIFEST"
  exit 1
fi

echo "[register] POST $BASE_URL/core-api/admin/apps/register"
echo "[register] manifest=$(basename "$MANIFEST") version=$(python3 -c "import json;print(json.load(open('$MANIFEST'))['version'])")"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

http_code="$(
  curl -sS -o "$tmp" -w "%{http_code}" -X POST "$BASE_URL/core-api/admin/apps/register" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @"$MANIFEST"
)"

echo "[register] HTTP $http_code"
if [ -s "$tmp" ]; then
  if python3 -m json.tool <"$tmp" 2>/dev/null; then
    :
  else
    echo "[register] body (não-JSON):"
    head -c 2000 "$tmp"
    echo
  fi
else
  echo "[register] body vazio"
fi

if [ "$http_code" != "201" ] && [ "$http_code" != "200" ]; then
  echo "[ERRO] Registro falhou."
  echo "Dicas:"
  echo "  - Precisa de apps.manage (ou superadmin) no portal."
  echo "  - Se a mensagem for plugin.version_already_exists, incremente version no manifest."
  echo "  - Confira BASE_URL (gateway): $BASE_URL"
  exit 1
fi

echo "[OK] Manifest registrado. Atribua reports.view / reports.manage / reports.notes.manage (e filiais) aos perfis."
