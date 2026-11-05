#!/usr/bin/env bash
# Instala (ou atualiza) o systemd timer do publicador MyWEG — NÃO habilita automaticamente.
# Ativação produtiva: systemctl enable --now myweg-needs-publisher.timer
# Desativação: systemctl disable --now myweg-needs-publisher.timer
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="${ROOT_DIR}/infra/systemd"
TARGET_DIR="${SYSTEMD_UNIT_DIR:-/etc/systemd/system}"

if [[ ! -d "${UNIT_DIR}" ]]; then
  echo "unit_dir_missing ${UNIT_DIR}" >&2
  exit 2
fi

install -m 0644 "${UNIT_DIR}/myweg-needs-publisher.service" "${TARGET_DIR}/myweg-needs-publisher.service"
install -m 0644 "${UNIT_DIR}/myweg-needs-publisher.timer" "${TARGET_DIR}/myweg-needs-publisher.timer"
chmod +x "${ROOT_DIR}/infra/scripts/run-myweg-needs-publisher-pending.sh"

systemctl daemon-reload

cat <<EOF
Installed units in ${TARGET_DIR}.
Timer NOT enabled yet (ACTIVATION_PENDING until watermark + dry-run smoke).

Next steps (operador@srv-api):
  1) Definir MYWEG_PUBLISHER_ACTIVATION_COLLECTED_AT no infra/.env
     (ISO America/Sao_Paulo do último lote já persistido / marco desejado)
     OU gravar watermark:
       docker compose --profile manual run --rm --no-deps myweg-needs-publisher \\
         --set-activation-watermark '2026-11-04T14:28:27-03:00' --json
  2) Dry-run pending:
       ./infra/scripts/run-myweg-needs-publisher-pending.sh
       # (trocar temporariamente --publish por --dry-run no script OU:
       docker compose --profile manual run --rm --no-deps myweg-needs-publisher \\
         --dry-run --publish-pending --json)
  3) Ativar:
       sudo systemctl enable --now myweg-needs-publisher.timer
  4) Desativar:
       sudo systemctl disable --now myweg-needs-publisher.timer
EOF
