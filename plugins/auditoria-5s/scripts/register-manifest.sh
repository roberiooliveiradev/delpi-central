#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${MANIFEST:-$SCRIPT_DIR/../auditoria-5s.manifest.json}"
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
curl -fsS -X POST "$BASE_URL/core-api/admin/apps/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @"$MANIFEST" | python3 -m json.tool

echo "[OK] Atribua auditoria-5s.view/audit/admin.filial-XX aos perfis (register com versão nova)."
