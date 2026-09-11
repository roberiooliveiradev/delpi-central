# J-R7 — zero path semantic affinity

**Status:** COMPLETE_GATE = PASS (`NO_PATH_SEMANTIC_AFFINITY`)  
**HEAD_BEFORE:** `402db060b`  
**Bloqueio:** A11-07

## Problema

`OperationalRouteActionResolverService._action_fits_route_affinity` decidia fit com:

- `"/products/" in path and "search" in path`
- `"supplier" in path` / `by-supplier-part-number`
- facet obrigatoriamente contida no path HTTP (`_facet_hits_path`)
- soft gate `"search" in path`

## Correção

Affinity passa a usar apenas:

```text
domain / intentBinding / continuity facets
+ parametersSchema
+ summary / description / whenToUse / tags
+ operationId (identidade no Action Catalog)
```

`path` permanece parâmetro de compatibilidade; **não** entra na decisão.

Soft pathMarkers/suffix só quando **não** há rota semântica; removido o gate `"search" in path`.

## Testes

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/unit/application/services/test_j_r7_zero_path_semantic_affinity.py \
  tests/unit/application/services/test_e11_s5_registry_operation_ids_cutover.py
```

| Caso | Esperado |
|---|---|
| structure vs stock sem `/products/` no path | facet/summary decide |
| search por schema `description` em path `/catalog/...` | PASS |
| source sem `"/products/" in` / `_facet_hits_path` | PASS |

## Gate

```text
NO_PATH_SEMANTIC_AFFINITY = PASS
COMPLETE_GATE (J-R7) = PASS
NEXT = J-R8
```
