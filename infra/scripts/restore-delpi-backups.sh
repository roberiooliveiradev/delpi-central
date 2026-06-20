#!/usr/bin/env bash
# Restaura dumps PostgreSQL gerados por backup (pg_dump -Fc).
set -euo pipefail

BACKUP_DIR="${1:-/mnt/d/delpi-backups/20260620-122158}"
COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "Diretório de backup não encontrado: $BACKUP_DIR" >&2
  exit 1
fi

restore_one() {
  local container="$1"
  local user="$2"
  local db="$3"
  local file="$4"

  if [[ ! -f "$file" ]]; then
    echo "SKIP: $file não existe"
    return 0
  fi

  echo "=== Restaurando $db em $container ==="
  docker exec -i "$container" pg_restore -U "$user" -d "$db" -c --if-exists --no-owner --role="$user" < "$file"
  echo "OK $db"
}

cd "$COMPOSE_DIR"

restore_one delpi-postgres-core delpi delpi_core "$BACKUP_DIR/delpi_core.dump"
restore_one delpi-postgres-plugins plugins_user plugins_hub "$BACKUP_DIR/plugins_hub.dump"
restore_one delpi-keycloak-db keycloak keycloak "$BACKUP_DIR/keycloak.dump"

echo "Restore concluído a partir de $BACKUP_DIR"
