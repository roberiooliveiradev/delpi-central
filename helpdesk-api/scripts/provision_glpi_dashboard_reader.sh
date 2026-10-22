#!/usr/bin/env bash
# Provisiona a conta GLPI minha-delpi-dashboard-reader.
# Perfil exclusivo: ticket READALL (1024). Entidades 0, 1 e 2 sem recursão.
# Não imprime App-Token nem User-Token. Não altera a conta de upload.
# O leitor permanece desligado (GLPI_DASHBOARD_READER_ENABLED=false).

set -euo pipefail

GLPI_CONTAINER="${GLPI_CONTAINER:-inventario-ti-glpi-1}"
ENV_FILE="${ENV_FILE:-infra/.env}"
CLIENT_NAME="minha-delpi-dashboard-reader"
USER_NAME="minha-delpi-dashboard-reader"
PROFILE_NAME="Dashboard Reader"
READALL=1024

keep_tokens=0
if [[ -f "$ENV_FILE" ]] && grep -q '^GLPI_DASHBOARD_READER_APP_TOKEN=.' "$ENV_FILE" && grep -q '^GLPI_DASHBOARD_READER_USER_TOKEN=.' "$ENV_FILE"; then
  keep_tokens=1
fi

cred_in_container="/tmp/glpi-dashboard-reader.credentials"
docker exec "$GLPI_CONTAINER" rm -f "$cred_in_container"

docker exec -e KEEP_TOKENS="$keep_tokens" -e READALL="$READALL" "$GLPI_CONTAINER" php -r "
chdir('/var/www/glpi');
require 'vendor/autoload.php';
\$kernel = new Glpi\Kernel\Kernel('production');
\$kernel->boot();
global \$DB;

\$now = date('Y-m-d H:i:s');
\$readAll = (int) getenv('READALL');
\$keep = getenv('KEEP_TOKENS') === '1';
\$forbidden = 2 | 4 | 8 | 16 | 8192 | 16384 | 32768 | 65536;

foreach ([0, 1, 2] as \$entityId) {
  \$found = \$DB->request(['FROM' => 'glpi_entities', 'WHERE' => ['id' => \$entityId]])->count();
  if (!\$found) {
    fwrite(STDERR, \"missing entity \$entityId\n\");
    exit(1);
  }
}

\$profile = \$DB->request(['FROM' => 'glpi_profiles', 'WHERE' => ['name' => '$PROFILE_NAME']])->current();
if (!\$profile) {
  \$DB->insert('glpi_profiles', [
    'name' => '$PROFILE_NAME',
    'interface' => 'central',
    'is_default' => 0,
    'helpdesk_hardware' => 0,
    'helpdesk_item_type' => '[]',
    'comment' => 'Read-only dashboard. Entities 0,1,2. No recursion.',
    'date_mod' => \$now,
    'date_creation' => \$now,
  ]);
  \$profileId = (int) \$DB->insertId();
} else {
  \$profileId = (int) \$profile['id'];
}

\$DB->delete('glpi_profilerights', ['profiles_id' => \$profileId]);
\$DB->insert('glpi_profilerights', [
  'profiles_id' => \$profileId,
  'name' => 'ticket',
  'rights' => \$readAll,
]);

\$user = \$DB->request(['FROM' => 'glpi_users', 'WHERE' => ['name' => '$USER_NAME']])->current();
\$plainUser = '';
if (!\$user) {
  \$plainUser = Toolbox::getRandomString(40);
  \$DB->insert('glpi_users', [
    'name' => '$USER_NAME',
    'password' => password_hash(Toolbox::getRandomString(40), PASSWORD_DEFAULT),
    'api_token' => (new GLPIKey())->encrypt(\$plainUser),
    'api_token_date' => \$now,
    'is_active' => 1,
    'is_deleted' => 0,
    'authtype' => 1,
    'profiles_id' => \$profileId,
    'entities_id' => 0,
    'date_mod' => \$now,
    'date_creation' => \$now,
  ]);
  \$userId = (int) \$DB->insertId();
  echo \"USER=created\n\";
} else {
  \$userId = (int) \$user['id'];
  if (!\$keep) {
    \$plainUser = Toolbox::getRandomString(40);
    \$DB->update('glpi_users', [
      'api_token' => (new GLPIKey())->encrypt(\$plainUser),
      'api_token_date' => \$now,
      'is_active' => 1,
      'profiles_id' => \$profileId,
      'entities_id' => 0,
    ], ['id' => \$userId]);
  } else {
    \$DB->update('glpi_users', [
      'is_active' => 1,
      'profiles_id' => \$profileId,
      'entities_id' => 0,
    ], ['id' => \$userId]);
  }
  echo \"USER=present\n\";
}

\$DB->delete('glpi_profiles_users', ['users_id' => \$userId]);
foreach ([0, 1, 2] as \$entityId) {
  \$DB->insert('glpi_profiles_users', [
    'users_id' => \$userId,
    'profiles_id' => \$profileId,
    'entities_id' => \$entityId,
    'is_recursive' => 0,
    'is_dynamic' => 0,
    'is_default_profile' => \$entityId === 0 ? 1 : 0,
  ]);
}

\$plainApp = '';
\$client = \$DB->request(['FROM' => 'glpi_apiclients', 'WHERE' => ['name' => '$CLIENT_NAME']])->current();
if (!\$client) {
  \$plainApp = Toolbox::getRandomString(40);
  \$DB->insert('glpi_apiclients', [
    'entities_id' => 0,
    'is_recursive' => 1,
    'name' => '$CLIENT_NAME',
    'is_active' => 1,
    'ipv4_range_start' => 0,
    'ipv4_range_end' => 4294967295,
    'app_token' => (new GLPIKey())->encrypt(\$plainApp),
    'app_token_date' => \$now,
    'dolog_method' => 0,
    'comment' => 'Dashboard reader only. User rights stay on profiles_users.',
    'date_mod' => \$now,
    'date_creation' => \$now,
  ]);
  echo \"APP_CLIENT=created\n\";
} elseif (!\$keep) {
  \$plainApp = Toolbox::getRandomString(40);
  \$DB->update('glpi_apiclients', [
    'app_token' => (new GLPIKey())->encrypt(\$plainApp),
    'app_token_date' => \$now,
    'is_active' => 1,
  ], ['id' => \$client['id']]);
  echo \"APP_CLIENT=rotated\n\";
} else {
  echo \"APP_CLIENT=present\n\";
}

\$rights = iterator_to_array(\$DB->request(['FROM' => 'glpi_profilerights', 'WHERE' => ['profiles_id' => \$profileId]]));
if (count(\$rights) !== 1 || \$rights[0]['name'] !== 'ticket' || (int) \$rights[0]['rights'] !== \$readAll) {
  fwrite(STDERR, \"profile rights diverged\n\");
  exit(1);
}
if (((int) \$rights[0]['rights']) & \$forbidden) {
  fwrite(STDERR, \"profile contains a write bit\n\");
  exit(1);
}
\$links = [];
foreach (\$DB->request(['FROM' => 'glpi_profiles_users', 'WHERE' => ['users_id' => \$userId]]) as \$link) {
  \$links[] = ((int) \$link['entities_id']) . ':' . ((int) \$link['is_recursive']);
}
sort(\$links);
if (\$links !== ['0:0', '1:0', '2:0']) {
  fwrite(STDERR, \"entity links diverged\n\");
  exit(1);
}
echo 'PROFILE_RIGHTS=ticket:' . \$readAll . \"\n\";
echo 'ENTITIES=' . implode(',', \$links) . \"\n\";
echo 'RECURSION=disabled' . \"\n\";

if (\$plainApp !== '' || \$plainUser !== '') {
  \$payload = json_encode(['app' => \$plainApp, 'user' => \$plainUser]);
  file_put_contents('$cred_in_container', \$payload);
  chmod('$cred_in_container', 0600);
}
"

docker exec "$GLPI_CONTAINER" php /var/www/glpi/bin/console cache:clear -n >/dev/null

tmp="$(mktemp)"
cleanup() {
  rm -f "$tmp"
  docker exec "$GLPI_CONTAINER" rm -f "$cred_in_container" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if docker exec "$GLPI_CONTAINER" test -f "$cred_in_container"; then
  docker cp "$GLPI_CONTAINER:$cred_in_container" "$tmp" >/dev/null
  python3 - "$ENV_FILE" "$tmp" <<'PY'
import json
import sys
from pathlib import Path
env_path, cred_path = Path(sys.argv[1]), Path(sys.argv[2])
payload = json.loads(cred_path.read_text(encoding="utf-8"))
updates = {
    "GLPI_DASHBOARD_READER_ENABLED": "false",
    "GLPI_DASHBOARD_READER_ENTITY_IDS": "0,1,2",
    "GLPI_DASHBOARD_READER_GROUP_IDS": "",
    "GLPI_DASHBOARD_READER_ALLOW_ROOT": "true",
}
if payload.get("app"):
    updates["GLPI_DASHBOARD_READER_APP_TOKEN"] = payload["app"]
if payload.get("user"):
    updates["GLPI_DASHBOARD_READER_USER_TOKEN"] = payload["user"]
text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
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
for key, value in updates.items():
    if key not in seen:
        out.append(f"{key}={value}\n")
env_path.write_text("".join(out), encoding="utf-8")
print("ENV_TOKENS=written")
print("ENV_ENABLED=false")
PY
else
  python3 - "$ENV_FILE" <<'PY'
import sys
from pathlib import Path
env_path = Path(sys.argv[1])
updates = {
    "GLPI_DASHBOARD_READER_ENABLED": "false",
    "GLPI_DASHBOARD_READER_ENTITY_IDS": "0,1,2",
    "GLPI_DASHBOARD_READER_GROUP_IDS": "",
    "GLPI_DASHBOARD_READER_ALLOW_ROOT": "true",
}
text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
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
for key, value in updates.items():
    if key not in seen:
        out.append(f"{key}={value}\n")
env_path.write_text("".join(out), encoding="utf-8")
print("ENV_TOKENS=kept")
print("ENV_ENABLED=false")
PY
fi

chmod 600 "$ENV_FILE" || true
echo "GLPI_READER=provisioned"
