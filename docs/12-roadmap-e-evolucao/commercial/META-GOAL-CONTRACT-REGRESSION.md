# Regressão — contrato tríade de meta SI

> **Status:** canônico · suite unitária transversal  
> **Runner:** [`scripts/check_si_goal_contract.sh`](../../../scripts/check_si_goal_contract.sh)

## Contrato

| Campo | Significado | Mês parcial |
|-------|-------------|-------------|
| `goal_value` | Meta **cadastrada** | ≠ prorata |
| `comparable_goal` | Meta **do período** | prorata / soma / média |
| `reference_goal` | Meta mês (referência) | standard = `goal_value`; curva = média dos meses |
| `value` (rotas `*_meta`) | Alias de `comparable_goal` | pode ser prorata — **não** é cadastrada |

Labels PT: Meta cadastrada / Meta do período / Meta mês (referência).

## Matriz A–H

| Letra | Cenário | Assert principal |
|-------|---------|------------------|
| A | exact (mês fechado) | tríade igual; UI 1 linha «Meta» |
| B | partial | cadastrada ≠ comparable; Meta parcial + Meta mês |
| C | accumulated (YTD) | `goal_value` intacto; prefixo acumulada |
| D | consolidado com metas 01+02 e `branch_value_aggregation` rollup | UI **com** números de meta (SI agrega); hint só se rollup impossível (<2 filiais ou `source_consolidated` sem meta `''`) |
| E | chat | tríade nos highlights; ausente de `skipFieldKeys` |
| F | TV valores iguais | 1 kpiMetric `value` |
| G | TV `value` ≠ `goal_value` | métricas distintas; cadastrada = `goal_value` |
| H | hubs enrich | flatten preserva cadastrada ≠ comparable |

Fixtures locais (sem lib cross-app):

- `strategic-indicators-api/tests/fixtures/si_goal_contract_cases.py`
- `api-delpi/tests/fixtures/si_goal_contract_cases.py`
- `tv-dashboard-api/tests/fixtures/si_goal_contract_cases.py`

## Comandos por pacote

```bash
# SI
cd strategic-indicators-api && .venv/bin/python -m pytest \
  tests/test_si_goal_contract_cases.py \
  tests/test_dashboard_indicator_metric_use_case.py \
  tests/test_dashboard_goals_by_source_keys.py \
  tests/test_branch_scoped_goals.py \
  tests/test_dashboard_department_indicators_use_case.py -q

# api-delpi
cd api-delpi && .venv/bin/python -m pytest \
  tests/test_si_goal_contract_regression.py \
  tests/test_dashboard_goal_enrichment.py -q

# TV
cd tv-dashboard-api && .venv/bin/python -m pytest \
  tests/test_comunicado_data_enrichment.py -k 'si_meta or si_scalar' \
  tests/test_tv_data_route_catalog.py -k 'exposes_si or si_meta or lmp_summary' \
  tests/test_field_key_humanize.py -q
cd plugins/tv-dashboard-presentation && npx vitest run src/fieldKeyHumanize.test.ts

# Chat
cd minha-delpi-ai-api && .venv/bin/python -m pytest \
  tests/unit/domain/services/test_chat_presentation_scalar_field_commentary_service.py -k si_goal \
  tests/unit/domain/services/test_external_action_column_label_service.py -k si_goal -q

# plugin-ui
cd plugins/plugin-ui && npx vitest run \
  src/utils/goalDisplay.test.ts \
  src/components/layout/KpiCard.test.tsx
```

Ou tudo: `./scripts/check_si_goal_contract.sh` (a partir da raiz do monorepo).

## Rebuild (após fix de produto)

```bash
./infra/scripts/up-dev-sequential.sh --build strategic-indicators-api api-delpi tv-dashboard-api minha-delpi-ai-api plugin-ui
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
```

## Fora de escopo

Dual-line visual na TV · redesign admin SI · e2e Playwright.
