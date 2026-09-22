#!/usr/bin/env bash
# H12 — liga enable_api no GLPI e provisiona App-Token + user técnico (cifrados via GLPIKey).
# Rodar no host do container inventario-ti-glpi-1. Não grava segredo no Git.

set -euo pipefail

GLPI_CONTAINER="${GLPI_CONTAINER:-inventario-ti-glpi-1}"
CLIENT_NAME="${GLPI_LEGACY_API_CLIENT_NAME:-minha-delpi-helpdesk-legacy}"
UPLOAD_USER="${GLPI_LEGACY_UPLOAD_USER:-minha-delpi-upload}"
ENV_FILE="${ENV_FILE:-infra/.env}"

echo "==> enable_api=1 + client '${CLIENT_NAME}' + user '${UPLOAD_USER}'"

OUT="$(docker exec "$GLPI_CONTAINER" php -r "
chdir('/var/www/glpi');
require 'vendor/autoload.php';
\$kernel = new Glpi\Kernel\Kernel('production');
\$kernel->boot();
global \$DB, \$CFG_GLPI;

\$DB->update('glpi_configs', ['value' => '1'], ['context' => 'core', 'name' => 'enable_api']);

\$plainApp = Toolbox::getRandomString(40);
\$encApp = (new GLPIKey())->encrypt(\$plainApp);
\$it = \$DB->request(['FROM' => 'glpi_apiclients', 'WHERE' => ['name' => '$CLIENT_NAME']]);
\$row = \$it->current();
if (\$row) {
  \$DB->update('glpi_apiclients', [
    'app_token' => \$encApp,
    'app_token_date' => date('Y-m-d H:i:s'),
    'is_active' => 1,
    'ipv4_range_start' => 0,
    'ipv4_range_end' => 4294967295,
    'date_mod' => date('Y-m-d H:i:s'),
  ], ['id' => \$row['id']]);
} else {
  \$DB->insert('glpi_apiclients', [
    'entities_id' => 0,
    'is_recursive' => 1,
    'name' => '$CLIENT_NAME',
    'is_active' => 1,
    'ipv4_range_start' => 0,
    'ipv4_range_end' => 4294967295,
    'app_token' => \$encApp,
    'app_token_date' => date('Y-m-d H:i:s'),
    'dolog_method' => 0,
    'date_mod' => date('Y-m-d H:i:s'),
    'date_creation' => date('Y-m-d H:i:s'),
  ]);
}

\$plainUser = Toolbox::getRandomString(40);
\$encUser = (new GLPIKey())->encrypt(\$plainUser);
\$uit = \$DB->request(['FROM' => 'glpi_users', 'WHERE' => ['name' => '$UPLOAD_USER']]);
\$urow = \$uit->current();
if (\$urow) {
  \$uid = (int)\$urow['id'];
  \$DB->update('glpi_users', [
    'api_token' => \$encUser,
    'api_token_date' => date('Y-m-d H:i:s'),
    'is_active' => 1,
  ], ['id' => \$uid]);
} else {
  \$DB->insert('glpi_users', [
    'name' => '$UPLOAD_USER',
    'password' => '',
    'api_token' => \$encUser,
    'api_token_date' => date('Y-m-d H:i:s'),
    'is_active' => 1,
    'authtype' => 1,
    'date_mod' => date('Y-m-d H:i:s'),
    'date_creation' => date('Y-m-d H:i:s'),
  ]);
  \$uid = (int)\$DB->insertId();
}
\$hasProfile = \$DB->request(['FROM' => 'glpi_profiles_users', 'WHERE' => ['users_id' => \$uid]])->count();
if (!\$hasProfile) {
  \$DB->insert('glpi_profiles_users', [
    'users_id' => \$uid,
    'profiles_id' => 1,
    'entities_id' => 0,
    'is_recursive' => 1,
    'is_dynamic' => 0,
    'is_default_profile' => 1,
  ]);
}

echo 'APP=' . \$plainApp . PHP_EOL;
echo 'USER=' . \$plainUser . PHP_EOL;
")"

APP_TOKEN="$(printf '%s\n' "$OUT" | sed -n 's/^APP=//p' | tail -1)"
USER_TOKEN="$(printf '%s\n' "$OUT" | sed -n 's/^USER=//p' | tail -1)"
docker exec "$GLPI_CONTAINER" php /var/www/glpi/bin/console cache:clear -n >/dev/null

python3 - <<PY
from pathlib import Path
path = Path("$ENV_FILE")
updates = {
    "GLPI_LEGACY_UPLOAD_ENABLED": "true",
    "GLPI_LEGACY_APP_TOKEN": "$APP_TOKEN",
    "GLPI_LEGACY_USER_TOKEN": "$USER_TOKEN",
    "GLPI_LEGACY_MAX_UPLOAD_BYTES": "20971520",
}
text = path.read_text() if path.exists() else ""
lines = text.splitlines(True) if text else []
seen = set()
out = []
for line in lines:
    if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
        out.append(line)
        continue
    key = line.split("=", 1)[0].strip()
    if key in updates:
        out.append(f"{key}={updates[key]}\n")
        seen.add(key)
    else:
        out.append(line)
        seen.add(key)
for key, value in updates.items():
    if key not in seen:
        out.append(f"{key}={value}\n")
path.write_text("".join(out))
print(f"updated {path}")
PY

echo "Pronto. Recrie helpdesk-api para ler o .env."
