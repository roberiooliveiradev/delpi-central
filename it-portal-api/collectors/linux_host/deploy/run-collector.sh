#!/usr/bin/env bash
# Wrapper do coletor Linux — falha explícita se o env técnico estiver ausente.
set -euo pipefail

INSTALL_ROOT="${IT_PORTAL_COLLECTOR_ROOT:-/opt/delpi/it-portal-collector}"
ENV_FILE="${IT_PORTAL_COLLECTOR_ENV_FILE:-/etc/delpi/it-portal-linux-collector.env}"
PYTHON_BIN="${INSTALL_ROOT}/venv/bin/python"
COMMAND="${1:-}"

if [[ -z "${COMMAND}" ]]; then
  echo "uso: run-collector diagnose|submit" >&2
  exit 2
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "arquivo de ambiente obrigatório ausente: ${ENV_FILE}" >&2
  exit 2
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "python do venv ausente: ${PYTHON_BIN} (execute o instalador)" >&2
  exit 2
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

export PYTHONPATH="${INSTALL_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${INSTALL_ROOT}"
exec "${PYTHON_BIN}" -m collectors.linux_host "${COMMAND}"
