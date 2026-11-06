#!/usr/bin/env bash
# One-shot: publica coletas fiscais MyWEG pendentes (Compose profile manual).
# Independente do timer/estado de necessidades. Sem token no script.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INFRA_DIR="${ROOT_DIR}/infra"
COMPOSE_FILE="${INFRA_DIR}/docker-compose.yml"
ENV_FILE="${INFRA_DIR}/.env"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "compose_not_found path=${COMPOSE_FILE}" >&2
  exit 2
fi
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "env_not_found path=${ENV_FILE}" >&2
  exit 2
fi

cd "${INFRA_DIR}"

# flock no host evita duas execuções do timer/serviço fiscal ao mesmo tempo.
LOCK_FILE="${MYWEG_INVOICE_PUBLISHER_HOST_RUN_LOCK:-/var/lib/delpi/myweg-invoice-publisher-state/host_run.lock}"
mkdir -p "$(dirname "${LOCK_FILE}")"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo '{"ok":true,"status":"busy","message":"host run lock held"}'
  exit 0
fi

# shellcheck disable=SC2086
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" --profile manual \
  run --rm --no-deps myweg-invoice-observations-publisher \
  --publish \
  --publish-pending \
  --json \
  ${MYWEG_INVOICE_PUBLISHER_EXTRA_ARGS:-}
