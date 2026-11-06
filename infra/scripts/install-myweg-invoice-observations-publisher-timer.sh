#!/usr/bin/env bash
# Instala (ou atualiza) o systemd timer do publicador fiscal MyWEG — NÃO habilita automaticamente.
# Ativação produtiva exige watermark + dry-run + autorização explícita do operador.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="${ROOT_DIR}/infra/systemd"
TARGET_DIR="${SYSTEMD_UNIT_DIR:-/etc/systemd/system}"

if [[ ! -d "${UNIT_DIR}" ]]; then
  echo "unit_dir_missing ${UNIT_DIR}" >&2
  exit 2
fi

install -m 0644 \
  "${UNIT_DIR}/myweg-invoice-observations-publisher.service" \
  "${TARGET_DIR}/myweg-invoice-observations-publisher.service"
install -m 0644 \
  "${UNIT_DIR}/myweg-invoice-observations-publisher.timer" \
  "${TARGET_DIR}/myweg-invoice-observations-publisher.timer"
chmod +x "${ROOT_DIR}/infra/scripts/run-myweg-invoice-observations-publisher-pending.sh"

systemctl daemon-reload

cat <<EOF
Installed units in ${TARGET_DIR}.
Timer NOT enabled yet (ACTIVATION_PENDING until watermark + dry-run smoke).

Schedule (America/Sao_Paulo): 08:00, 10:00, 12:00, 14:00, 16:00, 18:00.
Persistent=true may catch-up outside that window after reboot (exceptional).
Independent from myweg-needs-publisher.timer / state.

Next steps (operador@srv-api):
  1) Confirmar mount RO de notas-fiscais e permissões de
     /var/lib/delpi/myweg-invoice-publisher-state
  2) Registrar a observação manual já aceita (05/11/2026) no estado local
     OU definir marco no dia seguinte ao último document_date publicado:
       cd infra
       docker compose -f docker-compose.yml --env-file .env --profile manual \\
         run --rm --no-deps myweg-invoice-observations-publisher \\
         --record-published-success \\
         --collection-id '20261106T143350Z_2c04d5f7613d' \\
         --document-date '2026-11-05' \\
         --payload-sha256 '<payload_sha256_da_observacao>' \\
         --semantic-sha256 '012fa5498e92b1b0bea17eec0f7c6b27b8df15b5f36635b90996d30328c0bae3' \\
         --observation-id 'f4145bb5-f124-4d6a-ab34-40415dd43c83' \\
         --json
       # e/ou:
       docker compose -f docker-compose.yml --env-file .env --profile manual \\
         run --rm --no-deps myweg-invoice-observations-publisher \\
         --set-activation-document-date '2026-11-05' --json
     # Alternativa fail-closed: marco 2026-11-06 (após o dia já publicado).
  3) Dry-run pending:
       docker compose -f docker-compose.yml --env-file .env --profile manual \\
         run --rm --no-deps myweg-invoice-observations-publisher \\
         --dry-run --publish-pending --json
  4) Avaliar eligible / equivalent_skipped / conflict / before_watermark / blocked
  5) One-shot produtivo autorizado (se houver elegível):
       infra/scripts/run-myweg-invoice-observations-publisher-pending.sh
  6) Somente se gates OK — ativar:
       sudo systemctl enable --now myweg-invoice-observations-publisher.timer
  7) Desativar:
       sudo systemctl disable --now myweg-invoice-observations-publisher.timer
EOF
