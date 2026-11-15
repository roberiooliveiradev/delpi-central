#!/usr/bin/env bash
# Provisiona role eng_nc no postgres-plugins HML (idempotente).
# Uso: hml-provision-eng-nc.sh infra/.env.hml
# Não imprime a senha. Sem ENG_NC_REPOSITORY=postgres → skip (fail-honest).

set -euo pipefail

ENV_FILE="${1:-}"
if [[ -z "$ENV_FILE" || ! -f "$ENV_FILE" ]]; then
  echo "[ERRO] informe o caminho de infra/.env.hml" >&2
  exit 1
fi

repository="$(
  python3 - <<PY
from pathlib import Path
env = {}
for line in Path("$ENV_FILE").read_text().splitlines():
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    env[k] = v
print(env.get("ENG_NC_REPOSITORY", "").strip())
PY
)"
if [[ "$repository" != "postgres" ]]; then
  echo "[hml-provision-eng-nc] ENG_NC_REPOSITORY != postgres — skip (fail-honest)."
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GRANTS_SQL="$REPO_ROOT/engineering-api/db/eng_nc_grants.sql"
if [[ ! -f "$GRANTS_SQL" ]]; then
  echo "[ERRO] ausente: $GRANTS_SQL" >&2
  exit 1
fi

password="$(
  python3 - <<PY
from pathlib import Path
env = {}
for line in Path("$ENV_FILE").read_text().splitlines():
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    env[k] = v
pwd = env.get("ENG_NC_DB_PASSWORD", "").strip()
if not pwd or pwd.startswith("CHANGE_ME"):
    raise SystemExit("ENG_NC_DB_PASSWORD ausente ou placeholder em .env.hml")
print(pwd)
PY
)"

container="delpi-hml-postgres-plugins"
if ! docker ps --format '{{.Names}}' | grep -qx "$container"; then
  echo "[ERRO] $container não está running." >&2
  exit 1
fi

# Copia SQL e aplica com -v (psql variables) — senha só no stdin do docker.
docker cp "$GRANTS_SQL" "$container:/tmp/eng_nc_grants.sql"
docker exec -i "$container" \
  psql -U plugins_user -d plugins_hub \
  -v ON_ERROR_STOP=1 \
  -v "eng_nc_password=${password}" \
  -f /tmp/eng_nc_grants.sql >/dev/null

echo "[hml-provision-eng-nc] role eng_nc provisionada (grants NC aplicados)."
