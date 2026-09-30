#!/usr/bin/env bash
# Provisiona identidades E2E do BPMN Modeler no Keycloak de DEV + grants
# no core RBAC (delpi_core.user_permissions). Nunca rodar em produção.
#
# Requer:
#   KC_ADMIN / KC_ADMIN_PASSWORD   (Keycloak master admin)
#   KC_URL                         (default: http://localhost/auth)
#   BPMN_E2E_PASS_VIEWER|EDITOR|MANAGER (senhas dos usuários de teste)
#   docker container delpi-postgres-core acessível (core RBAC)
set -euo pipefail

KC=${KC_URL:-http://localhost/auth}
KC_ADMIN=${KC_ADMIN:?KC_ADMIN ausente}
KC_ADMIN_PASSWORD=${KC_ADMIN_PASSWORD:?KC_ADMIN_PASSWORD ausente}
CORE_PG=${CORE_PG_CONTAINER:-delpi-postgres-core}
CORE_DB=${CORE_DB:-delpi_core}
CORE_DB_USER=${CORE_DB_USER:-delpi}

ADMIN_TOKEN=$(curl -sf "$KC/realms/master/protocol/openid-connect/token" \
  -d "client_id=admin-cli&grant_type=password&username=$KC_ADMIN&password=$KC_ADMIN_PASSWORD" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

mk_user() {
  local uname=$1 perm_list=$2 pw=$3
  local uid
  uid=$(curl -sf -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$KC/admin/realms/delpi/users?username=$uname&exact=true" \
    | python3 -c 'import sys,json;u=json.load(sys.stdin);print(u[0]["id"] if u else "")')
  if [ -z "$uid" ]; then
    local loc
    loc=$(curl -sf -D - -o /dev/null -X POST "$KC/admin/realms/delpi/users" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H 'Content-Type: application/json' \
      -d "{\"username\":\"$uname\",\"enabled\":true,\"email\":\"$uname@delpi.e2e\",\"firstName\":\"E2E\",\"lastName\":\"$uname\",\"emailVerified\":true}" \
      | tr -d '\r' | awk '/^location:/ {print $2}')
    uid=${loc##*/}
    echo "[e2e] created $uname uid=$uid"
  else
    echo "[e2e] exists $uname uid=$uid"
  fi
  curl -sf -X PUT "$KC/admin/realms/delpi/users/$uid/reset-password" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H 'Content-Type: application/json' \
    -d "{\"type\":\"password\",\"value\":\"$pw\",\"temporary\":false}" -o /dev/null
  docker exec -i "$CORE_PG" psql -U "$CORE_DB_USER" -d "$CORE_DB" -v ON_ERROR_STOP=1 <<SQL
INSERT INTO users (id, name, email, active, is_superadmin)
VALUES ('$uid', 'E2E $uname', '$uname@delpi.e2e', true, false)
ON CONFLICT (id) DO NOTHING;
DELETE FROM user_permissions WHERE user_id = '$uid';
INSERT INTO user_permissions (user_id, permission_id, granted)
SELECT '$uid', p.id, true FROM permissions p WHERE p.code IN ($perm_list);
-- consent de primeiro acesso (mesmos purposes da política vigente)
INSERT INTO user_consents (id, user_id, purpose, granted, granted_at)
SELECT gen_random_uuid(), '$uid', purpose, true, now()
FROM (VALUES ('data_processing'), ('usage_tracking'), ('birthday_notifications'), ('analytics'), ('ai_context')) AS v(purpose)
ON CONFLICT DO NOTHING;
SQL
  echo "[e2e] granted [$perm_list] -> $uname"
}

mk_user "${BPMN_E2E_USER_VIEWER:-e2e-viewer}"   "'bpmn-modeler.view'"                                  "${BPMN_E2E_PASS_VIEWER:?}"
mk_user "${BPMN_E2E_USER_EDITOR:-e2e-editor}"   "'bpmn-modeler.view','bpmn-modeler.edit'"               "${BPMN_E2E_PASS_EDITOR:?}"
mk_user "${BPMN_E2E_USER_MANAGER:-e2e-manager}" "'bpmn-modeler.view','bpmn-modeler.edit','bpmn-modeler.manage'" "${BPMN_E2E_PASS_MANAGER:?}"
echo "[e2e] done."
