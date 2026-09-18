#!/usr/bin/env bash
# Provisiona papéis finais do Portal Suprimentos.
# Não recria permissions funcionais antigas.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"
API="$BASE_URL/core-api"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN (JWT com rbac.manage + roles.manage, ou superadmin)." >&2
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
    echo "[grant] $code" >&2
  done
}

ANALISTA_ID="$(ensure_role "Portal Suprimentos - Analista" "uso normal + unidades 01 e 02")"
grant "$ANALISTA_ID" supplies.access supplies.unit.filial-01 supplies.unit.filial-02

COMPRADOR_SC_ID="$(ensure_role "Portal Suprimentos - Comprador SC" "uso normal + unidade 01")"
grant "$COMPRADOR_SC_ID" supplies.access supplies.unit.filial-01

SOLICITANTE_SC_ID="$(ensure_role "Portal Suprimentos - Solicitante SC" "uso normal + unidade 01")"
grant "$SOLICITANTE_SC_ID" supplies.access supplies.unit.filial-01

ADMIN_ID="$(ensure_role "Portal Suprimentos - Admin" "administração; não implica uso normal nem todas as unidades")"
grant "$ADMIN_ID" supplies.manage supplies.unit.filial-01 supplies.unit.filial-02

echo "[OK] Papéis finais provisionados." >&2
