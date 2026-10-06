#!/usr/bin/env bash
# READ-ONLY audit helper — connects to TOTVS SQL Server using infra/.env credentials.
# Usage: q.sh -Q "SELECT ..."   or   q.sh -i file.sql -o out.txt
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC2046
export $(grep -E '^TOTVS_DB_(HOST|PORT|USER|PASSWORD|DATABASE)=' "$ROOT/infra/.env" | xargs -d '\n')
exec sqlcmd -S "$TOTVS_DB_HOST,$TOTVS_DB_PORT" -U "$TOTVS_DB_USER" -P "$TOTVS_DB_PASSWORD" \
  -d "$TOTVS_DB_DATABASE" -C -l 30 -h -1 -W -s"|" "$@"
