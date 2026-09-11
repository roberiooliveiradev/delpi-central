# E11.S1 — Architecture Enforcement contra substitutos semânticos

**Status:** COMPLETE_GATE  
**BASE_GIT_SHA (início S1):** `8bc84fc6d1cea3edc8cd0c08dceee90f9303e777`  
**Evidência machine:** [`e11-s1-semantic-debt-gate.json`](./e11-s1-semantic-debt-gate.json)

## O que foi feito

Estendido `scripts/ci/audit_architecture_phase3.py` (mesmo sistema Phase 3):

| Regra | Conceito |
|---|---|
| `SEMANTIC_PATH_DOMAIN_MAP` | `_DOMAIN_RULES` / path→domain |
| `SEMANTIC_ENDPOINT_PARAMETER_STRATEGY` | `ParameterStrategyInferenceService` + branches path/oid |
| `SEMANTIC_PATH_ROUTE_SEGMENT` | `RouteSegmentInferenceService` / path-tail |
| `SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG` | `operationIds` manuais no registry |
| `SEMANTIC_SMOKE_CREDENTIAL_DEFAULT` | `SMOKE_USER`/`PASSWORD` com default literal |
| `SEMANTIC_CONTENT_LATERAL_PATH_KEY` | reintrodução `pathMarkers`/equivalentes |

Modos:

- `--check-semantic-debt` — full-tree; **vermelho no baseline** (274 findings)
- `--check` (diff-aware) — também bloqueia *novas* linhas com os mesmos padrões

CI: unittest cobre positive/sibling/negative; workflow reporta debt com `continue-on-error` até cleanup (não mascara com exceção ampla).

## Provas

| Caso | Resultado |
|---|---|
| Positive `_DOMAIN_RULES` | detectado |
| Sibling `pathMarkers` em content/runtime | detectado (4 hits residuais em Python) |
| Negative `action.get("path")` HTTP | não flag |
| Negative fixture sob `/tests/` | fora de escopo |
| Baseline workspace | exit 1; rules obrigatórias presentes |

## totals_by_rule (baseline)

```text
SEMANTIC_PATH_DOMAIN_MAP: 2
SEMANTIC_ENDPOINT_PARAMETER_STRATEGY: 16
SEMANTIC_PATH_ROUTE_SEGMENT: 8
SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG: 84
SEMANTIC_SMOKE_CREDENTIAL_DEFAULT: 160
SEMANTIC_CONTENT_LATERAL_PATH_KEY: 4
total: 274
```

**Atenção:** não “corrigir” o gate para verde antes do cleanup E11.S2–S8/S10.
