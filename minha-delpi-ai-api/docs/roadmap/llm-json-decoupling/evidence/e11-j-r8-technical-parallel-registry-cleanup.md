# J-R8 — cleanup registry/content técnico

**Status:** COMPLETE_GATE = PASS  
**Gates:** `TECHNICAL_PARALLEL_REGISTRY=0` (manual) + `JUSTIFIED_NON_SEMANTIC` (autoTierC CI) · `ASSISTANT_CONTENT_TECHNICAL_DUPLICATION=0`  
**Bloqueio:** A11-08 / residual pós J-R6 (84 catalogs)

## Problema

`operational_route_registry.json` mantinha arrays `operationIds` como catálogo técnico paralelo ao Action Catalog, mesmo com `operationIdsRuntimeAuthority=false`.  
`api_route_domains.json` ainda tinha `domains.*.method` e `pathPrefixToDepartmentId`.

## Correção

| Superfície | Ação |
|---|---|
| `route.operationIds` (manual) | esvaziados (84→0 findings) |
| `cleanupMeta` | `operationIdsEmptiedAt=J-R8`, `operationIdsObserverCount=0`, `operationIdsRole=removed` |
| `domains.*.method` | removidos (22) |
| `pathPrefixToDepartmentId` | removido |
| department resolve | token semântico / `departmentIdAliases` (sem mapa path) |
| autoTierC CI | regenerado (503) como mirror CI-only + `JUSTIFIED_NON_SEMANTIC` |

Runtime de seleção continua OpenAPI / Action Catalog — registry manual não ensina operationId.

## Testes / audit

```bash
python3 scripts/ci/audit_architecture_phase3.py --check-semantic-debt
# totals_by_rule={} total=0

PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/unit/domain/services/test_j_r8_technical_parallel_registry_cleanup.py \
  tests/unit/domain/services/test_operational_route_registry_generator_service.py \
  tests/unit/domain/services/test_operational_route_path_marker_shadow_lint.py \
  ../scripts/ci/test_audit_architecture_phase3.py
```

| Caso | Esperado |
|---|---|
| positive | todos `operationIds` manuais `[]`; debt catalog = 0 |
| sibling | department via `domain_prefix` semântico |
| negative | domínio desconhecido → `None`; pathPrefix map ausente |
| CI mirror | autoTierC `JUSTIFIED_NON_SEMANTIC`, `runtimeAuthority=false` |

## Gate

```text
SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG = 0
TECHNICAL_PARALLEL_REGISTRY = 0 (manual) | JUSTIFIED_NON_SEMANTIC (autoTierC CI)
ASSISTANT_CONTENT_TECHNICAL_DUPLICATION = 0
COMPLETE_GATE (J-R8) = PASS
NEXT = J-R9
```
