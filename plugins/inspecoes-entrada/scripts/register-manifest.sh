#!/usr/bin/env bash
# Registra ou atualiza o plugin na Core API (requer apps.manage ou superadmin).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${MANIFEST:-$SCRIPT_DIR/../inspecoes-entrada.manifest.json}"
BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN (JWT do portal com apps.manage ou superadmin)."
  echo "Exemplo: export TOKEN=\"\$(bash infra/scripts/get-dev-token.sh)\""
  echo "         bash plugins/inspecoes-entrada/scripts/register-manifest.sh"
  exit 1
fi

if [ ! -f "$MANIFEST" ]; then
  echo "[ERRO] Manifesto não encontrado: $MANIFEST"
  exit 1
fi

echo "[register] POST $BASE_URL/core-api/admin/apps/register"
curl -fsS -X POST "$BASE_URL/core-api/admin/apps/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @"$MANIFEST" | python3 -m json.tool

echo "[OK] Manifesto enviado. Atribua inspecoes-entrada.view.filial-01|02 (ou inspecoes-entrada.view) ao perfil desejado no RBAC."
