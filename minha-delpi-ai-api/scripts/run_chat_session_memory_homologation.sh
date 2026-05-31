#!/usr/bin/env bash
# Homologação — memória de sessão (unit + HTTP opcional)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ -d /app && -z "${SMOKE_BASE_URL:-}" ]]; then
  export SMOKE_BASE_URL=http://delpi-gateway
fi
export PYTHONPATH="${PYTHONPATH:-$ROOT}"
"${ROOT}/scripts/run_session_memory_validation.sh"
PY="${PYTHON:-python3}"
[[ -x "${ROOT}/.venv/bin/python" ]] && PY="${ROOT}/.venv/bin/python"
echo ""
echo "== HTTP persistência + follow-up =="
"$PY" scripts/smoke_session_memory_persist.py || echo "Aviso: smoke HTTP indisponível." >&2
echo ""
echo "Homologação memória de sessão: concluída."
