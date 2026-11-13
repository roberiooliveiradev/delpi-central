#!/usr/bin/env bash
# Provisiona role eng_prc no postgres-plugins PROD (idempotente).
# Uso: prod-provision-eng-prc.sh infra/.env
# Não imprime a senha.

set -euo pipefail

ENV_FILE="${1:-}"
if [[ -z "$ENV_FILE" || ! -f "$ENV_FILE" ]]; then
  echo "[ERRO] informe o caminho de infra/.env" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GRANTS_SQL="$REPO_ROOT/engineering-api/db/eng_prc_grants.sql"
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
pwd = env.get("ENG_PRC_DB_PASSWORD", "").strip()
if not pwd or pwd.startswith("CHANGE_ME"):
    raise SystemExit("ENG_PRC_DB_PASSWORD ausente ou placeholder em .env")
print(pwd)
PY
)"

container="delpi-postgres-plugins"
if ! docker ps --format '{{.Names}}' | grep -qx "$container"; then
  echo "[ERRO] $container não está running." >&2
  exit 1
fi

# Copia SQL e aplica com -v (psql variables) — senha só no stdin do docker.
docker cp "$GRANTS_SQL" "$container:/tmp/eng_prc_grants.sql"
docker exec -i "$container" \
  psql -U plugins_user -d plugins_hub \
  -v ON_ERROR_STOP=1 \
  -v "eng_prc_password=${password}" \
  -f /tmp/eng_prc_grants.sql >/dev/null

# Grants de migrations posteriores (role já existente).
docker exec -i "$container" psql -U plugins_user -d plugins_hub -v ON_ERROR_STOP=1 <<'SQL' >/dev/null
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
    IF EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'engineering'
        AND table_name = 'product_registration_attachments'
    ) THEN
      EXECUTE 'GRANT SELECT, INSERT, UPDATE ON engineering.product_registration_attachments TO eng_prc';
      EXECUTE 'REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES ON engineering.product_registration_attachments FROM eng_prc';
    END IF;
    IF EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'engineering'
        AND table_name = 'product_registration_correction_returns'
    ) THEN
      EXECUTE 'GRANT SELECT, INSERT, UPDATE ON engineering.product_registration_correction_returns TO eng_prc';
      EXECUTE 'GRANT SELECT, INSERT, UPDATE ON engineering.product_registration_correction_targets TO eng_prc';
      EXECUTE 'REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES ON engineering.product_registration_correction_returns FROM eng_prc';
      EXECUTE 'REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES ON engineering.product_registration_correction_targets FROM eng_prc';
    END IF;
  END IF;
END $$;
SQL

docker exec "$container" rm -f /tmp/eng_prc_grants.sql

# Smoke: eng_prc consegue SELECT na fila (sem listar senha).
docker exec -e PGPASSWORD="$password" "$container" \
  psql -U eng_prc -d plugins_hub -v ON_ERROR_STOP=1 \
  -c 'SELECT count(*) FROM engineering.product_registration_requests;' >/dev/null

unset password
echo "PRD_ENG_PRC_PROVISION=PASS"
