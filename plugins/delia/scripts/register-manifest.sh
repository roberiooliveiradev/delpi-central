#!/usr/bin/env bash
set -euo pipefail

# Ops helper — Core live registration for plugins/delia/delpi.manifest.json.
# C1-T6 executed registration via POST /core-api/admin/apps/register (idempotent re-run OK).
# RBAC assignment of delia.access remains an explicit operational decision (not auto-granted).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${MANIFEST:-$SCRIPT_DIR/../delpi.manifest.json}"
BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN (JWT do portal com apps.manage ou superadmin)."
  echo "Exemplo: TOKEN=\$(bash infra/scripts/get-dev-token.sh) $0"
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

echo "[OK] Atribua delia.access no RBAC aos perfis desejados (visibilidade de app)."
