#!/usr/bin/env bash
# H12 — liga enable_api no GLPI (API legada) e imprime o App-Token do client Document.
# Uso: rodar no host que tem o container MySQL/MariaDB do GLPI (ex.: inventario-ti-glpi).
# Não grava segredo no Git. Depois: exportar GLPI_LEGACY_UPLOAD_ENABLED=true e
# GLPI_LEGACY_APP_TOKEN=<app_token> no .env da helpdesk-api e recriar o serviço.

set -euo pipefail

GLPI_DB_CONTAINER="${GLPI_DB_CONTAINER:-inventario-ti-db-1}"
GLPI_DB_NAME="${GLPI_DB_NAME:-glpi}"
GLPI_DB_USER="${GLPI_DB_USER:-glpi}"
CLIENT_NAME="${GLPI_LEGACY_API_CLIENT_NAME:-minha-delpi-helpdesk-legacy}"

echo "==> Habilitando enable_api=1 em glpi_configs (container=${GLPI_DB_CONTAINER})"
docker exec -i "$GLPI_DB_CONTAINER" mysql -u"$GLPI_DB_USER" -p"${GLPI_DB_PASSWORD:?defina GLPI_DB_PASSWORD}" "$GLPI_DB_NAME" <<'SQL'
UPDATE glpi_configs
SET value = '1'
WHERE context = 'core' AND name = 'enable_api';
SQL

echo "==> Garantindo client API '${CLIENT_NAME}'"
EXISTING="$(docker exec -i "$GLPI_DB_CONTAINER" mysql -N -u"$GLPI_DB_USER" -p"${GLPI_DB_PASSWORD}" "$GLPI_DB_NAME" \
  -e "SELECT app_token FROM glpi_apiclients WHERE name='${CLIENT_NAME}' LIMIT 1;" 2>/dev/null || true)"

if [[ -n "${EXISTING}" ]]; then
  APP_TOKEN="$EXISTING"
  echo "Client já existe."
else
  APP_TOKEN="$(python3 - <<'PY'
import secrets
print(secrets.token_hex(20))
PY
)"
  docker exec -i "$GLPI_DB_CONTAINER" mysql -u"$GLPI_DB_USER" -p"${GLPI_DB_PASSWORD}" "$GLPI_DB_NAME" <<SQL
INSERT INTO glpi_apiclients
  (name, is_active, ipv4_range_start, ipv4_range_end, app_token, dvc_endpoint)
VALUES
  ('${CLIENT_NAME}', 1, INET_ATON('0.0.0.0'), INET_ATON('255.255.255.255'), '${APP_TOKEN}', '');
SQL
  echo "Client criado."
fi

echo
echo "Defina no infra/.env (não commitar o token):"
echo "  GLPI_LEGACY_UPLOAD_ENABLED=true"
echo "  GLPI_LEGACY_APP_TOKEN=${APP_TOKEN}"
echo
echo "Depois: rebuild/recreate helpdesk-api."
echo "App-Token (copie agora): ${APP_TOKEN}"
