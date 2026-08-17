#!/usr/bin/env bash
# Regressão unitária do contrato tríade de meta SI (todas as camadas).
# Exit ≠ 0 se qualquer pacote falhar.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0

run_step() {
  local label="$1"
  shift
  echo ""
  echo "=== ${label} ==="
  if "$@"; then
    echo "OK: ${label}"
  else
    echo "FAIL: ${label}" >&2
    fail=1
  fi
}

run_step "strategic-indicators-api" \
  bash -c "cd strategic-indicators-api && .venv/bin/python -m pytest \
    tests/test_si_goal_contract_cases.py \
    tests/test_dashboard_indicator_metric_use_case.py \
    tests/test_dashboard_goals_by_source_keys.py \
    tests/test_branch_scoped_goals.py \
    tests/test_dashboard_department_indicators_use_case.py -q"

run_step "api-delpi" \
  bash -c "cd api-delpi && .venv/bin/python -m pytest \
    tests/test_si_goal_contract_regression.py \
    tests/test_dashboard_goal_enrichment.py -q"

run_step "tv-dashboard-api" \
  bash -c "cd tv-dashboard-api && .venv/bin/python -m pytest \
    tests/test_comunicado_data_enrichment.py -k 'si_meta or si_scalar or distinct_goal' \
    tests/test_tv_data_route_catalog.py -k 'exposes_si or si_meta or lmp_summary' \
    tests/test_field_key_humanize.py -q"

run_step "tv-dashboard-presentation (vitest)" \
  bash -c "cd plugins/tv-dashboard-presentation && npx vitest run src/fieldKeyHumanize.test.ts"

run_step "minha-delpi-ai-api" \
  bash -c "cd minha-delpi-ai-api && .venv/bin/python -m pytest \
    tests/unit/domain/services/test_chat_presentation_scalar_field_commentary_service.py -k si_goal \
    tests/unit/domain/services/test_external_action_column_label_service.py -k si_goal -q"

run_step "plugin-ui (vitest)" \
  bash -c "cd plugins/plugin-ui && npx vitest run \
    src/utils/goalDisplay.test.ts \
    src/components/layout/KpiCard.test.tsx"

echo ""
if [[ "$fail" -ne 0 ]]; then
  echo "check_si_goal_contract: FAILED" >&2
  exit 1
fi
echo "check_si_goal_contract: PASSED"
exit 0
