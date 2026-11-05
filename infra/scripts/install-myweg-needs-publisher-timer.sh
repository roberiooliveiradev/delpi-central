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

Schedule (America/Sao_Paulo): 06:00, 06:15, 06:30, 06:45.
Persistent=true may catch-up outside that window after reboot (exceptional).

Next steps (operador@srv-api):
  1) Confirmar última coleta persistida e permissões de
     /var/lib/delpi/myweg-publisher-state
  2) Definir watermark (último lote já persistido / marco desejado):
       cd infra
       docker compose -f docker-compose.yml --env-file .env --profile manual \\
         run --rm --no-deps myweg-needs-publisher \\
         --set-activation-watermark '2026-11-04T14:28:27-03:00' --json
     # ou MYWEG_PUBLISHER_ACTIVATION_COLLECTED_AT no infra/.env
  3) Dry-run pending (NÃO editar run-myweg-needs-publisher-pending.sh):
       docker compose -f docker-compose.yml --env-file .env --profile manual \\
         run --rm --no-deps myweg-needs-publisher \\
         --dry-run --publish-pending --json
  4) Avaliar eligible / blocked / conflict / before_watermark
  5) Somente se gates OK — ativar:
       sudo systemctl enable --now myweg-needs-publisher.timer
  6) Desativar:
       sudo systemctl disable --now myweg-needs-publisher.timer
EOF
