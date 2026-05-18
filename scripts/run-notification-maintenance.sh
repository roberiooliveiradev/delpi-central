#!/usr/bin/env sh
# Processa envios agendados vencidos e notificações de aniversário do dia.
# Uso em cron (ex.: a cada 5 min para pending; 1x/dia para birthdays via crontab separado).

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Processando envios agendados..."
"$SCRIPT_DIR/process-pending-notifications.sh"

echo "==> Processando aniversários..."
"$SCRIPT_DIR/run-birthday-notifications.sh"

echo "Manutenção de notificações concluída."
