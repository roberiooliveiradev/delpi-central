#!/usr/bin/env bash
# Gate H13 (CI) — catálogo de evals do agente GPT PAC (Onda 5.4).
# Homologação manual: rodar EVAL01–EVAL20 no Custom GPT e pontuar com --score-file.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PAC_REPO="${PAC_QUALITY_REPO:-$(cd "${REPO_ROOT}/../api-pac-quality" 2>/dev/null && pwd || true)}"

if [ -z "${PAC_REPO}" ] || [ ! -f "${PAC_REPO}/scripts/run_pac_agent_eval.py" ]; then
  echo "[fail] api-pac-quality não encontrado. Defina PAC_QUALITY_REPO." >&2
  exit 1
fi

PYTHON="${PAC_REPO}/.venv/bin/python"
if [ ! -x "${PYTHON}" ]; then
  PYTHON=python3
fi

echo "[check] H13 — catálogo de evals (${PAC_REPO})"
"${PYTHON}" "${PAC_REPO}/scripts/run_pac_agent_eval.py" --check-catalog

echo "[check] H13 — testes unitários do runner"
"${PYTHON}" -m pytest \
  "${PAC_REPO}/tests/unit/test_pac_agent_eval_cases.py" \
  "${PAC_REPO}/tests/unit/test_run_pac_agent_eval_script.py" \
  -q

if [ -n "${PAC_EVAL_RESPONSES_FILE:-}" ]; then
  echo "[check] H13 — pontuação (${PAC_EVAL_RESPONSES_FILE})"
  MIN_RATE="${PAC_EVAL_MIN_PASS_RATE:-0.9}"
  "${PYTHON}" "${PAC_REPO}/scripts/run_pac_agent_eval.py" \
    --score-file "${PAC_EVAL_RESPONSES_FILE}" \
    --min-pass-rate "${MIN_RATE}"
else
  echo "[skip] Pontuação manual — defina PAC_EVAL_RESPONSES_FILE após rodar EVAL01–EVAL20 no GPT"
fi

echo "[OK] check-pac-agent-eval (gate CI H13)"
