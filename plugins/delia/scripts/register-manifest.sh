#!/usr/bin/env bash
set -euo pipefail

# Ops helper — does NOT run during C1-T4/T4D1.
# Product Master APPROVED delia.access (C1-T4D1). Core live registration remains
# PENDING until Gateway/Compose publication (C1-T5+) and ops RBAC assignment.
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
