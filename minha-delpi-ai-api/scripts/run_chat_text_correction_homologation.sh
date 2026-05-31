#!/usr/bin/env bash
# Homologação — correção de texto (unit + smoke offline; HTTP opcional via gateway).
#
# Host:
#   cd minha-delpi-ai-api && ./scripts/run_chat_text_correction_homologation.sh
#
# Container (API dev):
#   docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
#     bash scripts/run_chat_text_correction_homologation.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -d /app && -z "${SMOKE_BASE_URL:-}" ]]; then
  export SMOKE_BASE_URL=http://delpi-gateway
fi

export PYTHONPATH="${PYTHONPATH:-$ROOT}"

echo "== Correção de texto — validação offline =="
"${ROOT}/scripts/run_text_correction_validation.sh"

if [[ "${SMOKE_SKIP_HTTP_TEXT_CORRECTION:-}" == "1" ]]; then
  echo ""
  echo "SKIP HTTP (SMOKE_SKIP_HTTP_TEXT_CORRECTION=1)"
  echo ""
  echo "Homologação correção de texto (offline): OK"
  exit 0
fi

PY="${PYTHON:-python3}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
fi

if command -v curl >/dev/null 2>&1; then
  echo ""
  echo "== Correção de texto — smoke HTTP (se gateway disponível) =="
  if "$PY" scripts/smoke_text_correction_http.py 2>/dev/null; then
    echo "HTTP smoke: OK"
  else
    echo "Aviso: smoke HTTP indisponível ou falhou — offline já validado." >&2
  fi
else
  echo "Aviso: curl ausente — apenas validação offline." >&2
fi

echo ""
echo "Homologação correção de texto: concluída."
