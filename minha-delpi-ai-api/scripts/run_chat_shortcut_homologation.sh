#!/usr/bin/env bash
# Homologação rápida — login, atalhos com {{placeholders}} e chips de follow-up.
#
# Uso (host com gateway em http://localhost):
#   cd minha-delpi-ai-api && PYTHONPATH=. ./scripts/run_chat_shortcut_homologation.sh
#
# Uso (dentro do container da API):
#   PYTHONPATH=/app SMOKE_BASE_URL=http://delpi-gateway ./scripts/run_chat_shortcut_homologation.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-$ROOT}"
export SMOKE_BASE_URL="${SMOKE_BASE_URL:-http://localhost}"
PAUSE="${SMOKE_RATE_LIMIT_PAUSE:-45}"

PY="${PYTHON:-python3}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
fi

run() {
  echo ""
  echo "== $1 =="
  "$PY" scripts/"$2"
}

failed=0
step=0

run_step() {
  if [[ "$step" -gt 0 && "$PAUSE" -gt 0 ]]; then
    echo ""
    echo "(pausa ${PAUSE}s — rate limit chat_messages)"
    sleep "$PAUSE"
  fi
  step=$((step + 1))
  run "$1" "$2" || failed=$((failed + 1))
}

if [[ -x "${ROOT}/scripts/run_search_placeholder_validation.sh" ]]; then
  echo ""
  echo "== Validação placeholder pesquisa web (offline) =="
  "${ROOT}/scripts/run_search_placeholder_validation.sh" || failed=$((failed + 1))
  step=$((step + 1))
else
  run_step "Placeholders no conteúdo (sem código fixo)" smoke_shortcut_placeholders.py
fi
run_step "Login e perfil" smoke_identity_profile.py
run_step "Catálogo e onboarding" smoke_features_catalog.py
if [[ "${SMOKE_SKIP_HTTP_FOLLOW_UP:-}" != "1" ]]; then
  run_step "Chips Próximos passos (API)" smoke_follow_up_chips.py
else
  echo ""
  echo "== Chips Próximos passos (API) =="
  echo "SKIP SMOKE_SKIP_HTTP_FOLLOW_UP=1 (evita rate limit chat_messages)"
fi

if [[ "$failed" -gt 0 ]]; then
  echo ""
  echo "$failed etapa(s) falharam." >&2
  exit 1
fi

echo ""
echo "Homologação atalhos do chat: todas as etapas passaram."
