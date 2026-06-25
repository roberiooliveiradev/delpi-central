#!/usr/bin/env bash
# Gate de fechamento Onda 1 — operação NC ponta a ponta (plugin via api-delpi).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PAC_REPO="${PAC_QUALITY_REPO:-$(cd "${REPO_ROOT}/../api-pac-quality" 2>/dev/null && pwd || true)}"

echo "[onda1] Template 8D mínimo (fixture CI)"
python3 "${REPO_ROOT}/api-delpi/scripts/generate_rnc_8d_template_fixture.py"

echo "[onda1] Testes export 8D"
docker exec delpi-api-delpi python -m pytest tests/test_rnc_8d_excel_export_service.py -q

echo "[onda1] Gate OpenAPI api-delpi (chat skill / plugin)"
cd "${REPO_ROOT}/minha-delpi-ai-api"
.venv/bin/python scripts/audit_api_delpi_pac_onda1.py --check

if [ -n "${TOKEN:-}" ] || [ -f "${REPO_ROOT}/infra/.env" ]; then
  export TOKEN="${TOKEN:-$(grep '^API_DELPI_INTERNAL_SERVICE_TOKEN=' "${REPO_ROOT}/infra/.env" | cut -d= -f2)}"
  echo "[onda1] Smoke H1"
  python3 "${SCRIPT_DIR}/run_h1_api_smoke.py"
  echo "[onda1] Casos anonimizados (1.10)"
  python3 "${SCRIPT_DIR}/run_onda1_anonymized_cases.py"
else
  echo "[skip] TOKEN ausente — smoke H1 e casos anonimizados"
fi

if [ -n "${PAC_REPO}" ] && [ -f "${PAC_REPO}/scripts/audit_pac_onda1_openapi_parity.py" ]; then
  echo "[onda1] Paridade OpenAPI api-pac (checkout local — requer servidor ou skip)"
  if [ -n "${PAC_OPENAPI_URL:-}" ]; then
    "${PAC_REPO}/.venv/bin/python" "${PAC_REPO}/scripts/audit_pac_onda1_openapi_parity.py" --check
  else
    echo "[skip] PAC_OPENAPI_URL não definido"
  fi
fi

echo "[onda1] Plugin build"
cd "${REPO_ROOT}/plugins/quality-action-plans" && npm run build

echo "[OK] run_onda1_gate"
