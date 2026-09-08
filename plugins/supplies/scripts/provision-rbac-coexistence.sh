#!/usr/bin/env bash
# Provisiona papéis de coexistência do Portal Suprimentos (permissions canônicas).
# Não remove permissions legadas. Não atribui usuários automaticamente.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"
API="$BASE_URL/core-api"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN (JWT com rbac.manage + roles.manage, ou superadmin)." >&2
  echo "Dev: TOKEN=\$(bash infra/scripts/get-dev-token.sh) $0" >&2
  exit 1
fi

auth=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")

ensure_role() {
  local name="$1"
  local description="$2"
  local existing
  existing="$(curl -fsS "${auth[@]}" "$API/admin/rbac/roles?page_size=200" \
    | python3 -c "import sys,json; name=sys.argv[1]; data=json.load(sys.stdin).get('data') or [];
print(next((r['id'] for r in data if r.get('name')==name), ''))" "$name")"
  if [ -n "$existing" ]; then
    echo "[role] exists $name -> $existing" >&2
    printf '%s' "$existing"
    return
  fi
  local created
  created="$(curl -fsS -X POST "${auth[@]}" "$API/admin/rbac/roles" \
    -d "$(python3 -c "import json,sys; print(json.dumps({'name':sys.argv[1],'description':sys.argv[2]}))" "$name" "$description")" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")"
  echo "[role] created $name -> $created" >&2
  printf '%s' "$created"
}

grant() {
  local role_id="$1"
  shift
  local code
  for code in "$@"; do
    curl -fsS -X POST "${auth[@]}" "$API/admin/rbac/roles/$role_id/permissions" \
      -d "$(python3 -c "import json,sys; print(json.dumps({'id':sys.argv[1]}))" "$code")" >/dev/null
    echo "[grant] $role_id <- $code" >&2
  done
}

ANALISTA_ID="$(ensure_role "Portal Suprimentos - Analista" "portal + analytics + units SC/ES")"
grant "$ANALISTA_ID" \
  supplies.portal.access \
  supplies.analytics.access \
  supplies.unit.filial-01 \
  supplies.unit.filial-02

COMPRADOR_SC_ID="$(ensure_role "Portal Suprimentos - Comprador SC" "portal + operations + unit SC")"
grant "$COMPRADOR_SC_ID" \
  supplies.portal.access \
  supplies.operations.access \
  supplies.analytics.access \
  supplies.unit.filial-01

SOLICITANTE_SC_ID="$(ensure_role "Portal Suprimentos - Solicitante SC" "portal + SC + unit SC")"
grant "$SOLICITANTE_SC_ID" \
  supplies.portal.access \
  supplies.purchase-requests.access \
  supplies.unit.filial-01

ADMIN_ID="$(ensure_role "Portal Suprimentos - Admin" "administration + units explícitas (não implica all units)")"
grant "$ADMIN_ID" \
  supplies.portal.access \
  supplies.administration.manage \
  supplies.unit.filial-01 \
  supplies.unit.filial-02

echo "[OK] Papéis canônicos provisionados. Atribua usuários via Admin RBAC." >&2
echo "Comprador ES: criar papel equivalente com supplies.unit.filial-02 quando houver usuário operacional." >&2
