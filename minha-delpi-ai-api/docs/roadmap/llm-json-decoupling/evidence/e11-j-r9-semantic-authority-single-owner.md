# J-R9 — semantic single owner

**Status:** COMPLETE_GATE = PASS (`SEMANTIC_AUTHORITY_SINGLE_OWNER`)  
**Bloqueio:** A11-10

## Problema

Family mappers (`_TOKEN_RULES` KPI/product/production) + `route_by_production_operational_kind` / `intentBinding` / `catalogToken` formavam **segunda authority** de seleção de action, em paralelo ao Action Catalog OpenAPI.

## Correção

| Item | Decisão |
|---|---|
| `ChatTurnUnderstandingService` | KEEP — goals |
| `ChatIntentRouterService` | KEEP triagem; removido prova via `department_kpi` catalogToken |
| `ChatTurnAnalysisService` | KEEP |
| `ChatTaskPlannerService` | KEEP (sobre candidatos do catálogo) |
| Generic mapper | KEEP |
| Product/Production/KPI `_TOKEN_RULES` | **esvaziados**; resolve live → `None` |
| `select_by_department_kpi` / `select_by_intent` / `select_production_operational` | return `None` (OpenAPI-first) |
| Owner canônico | `ChatSemanticAuthorityOwnershipService` → `openapi_action_catalog` |

Residual J-R8: affinity não rejeita rotas vocabulary só por facet derivado de `route.id`; preferência por path params required preenchidos.

## Testes

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/unit/domain/services/test_j_r9_semantic_authority_single_owner.py \
  tests/unit/domain/services/test_e2_s4_production_kpi_family_cutover.py \
  tests/unit/domain/services/test_e2_s4_product_family_cutover.py \
  tests/unit/application/services/test_external_action_operational_route_selection_service.py
```

| Caso | Esperado |
|---|---|
| positive | ownership matrix `actionSelection=openapi_action_catalog` |
| sibling | force_legacy ainda resolve KPI/production para parity |
| negative | prosa KPI/stock/ops **não** seleciona via mapper/registry |

## Gate

```text
SEMANTIC_AUTHORITY_SINGLE_OWNER = PASS
COMPLETE_GATE (J-R9) = PASS
NEXT = J-R10
```
