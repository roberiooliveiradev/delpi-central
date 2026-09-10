# E9.S7 — Architecture audit (residuals)

**Status:** `ATENDIDO` (2026-09-10) — classificados; sem DELETE prematuro  
**Onda:** H (plano 09)  
**Fixture:** `tests/fixtures/intelligence_baseline/e9_s7_architecture_residuals.json`  
**Harness:** `tests/unit/domain/services/test_e9_s7_architecture_residuals.py`  
**Gate:** E9.S6 `deleteAuthorized=false`

## Veredito

```text
CHECKLIST_COVERED = PASS (10 residuals)
EACH_CLASSIFIED = PASS
REMOVE_WHEN_GATES_PASS = 5 (blocked)
JUSTIFIED_OR_REMOVED = PASS
NO_CORE_AUTHORITY_WITHOUT_JUSTIFICATION = PASS
NO_PREMATURE_DELETE = PASS
```

## Disposições

| Residual | Disposition |
|----------|-------------|
| pathMarkers | REMOVE_WHEN_GATES_PASS |
| operationIdMarkers | REMOVE_WHEN_GATES_PASS |
| parameterStrategy_per_endpoint | REMOVE_WHEN_GATES_PASS |
| manual_endpoint_priority | REMOVE_WHEN_GATES_PASS |
| messageSegmentTerms | REMOVE_WHEN_GATES_PASS |
| pathToken_pathContains | JUSTIFIED_POLICY (KPI domain) |
| preferredRouteId | JUSTIFIED_COMPATIBILITY (follow-up) |
| if_path_provider_operationId | JUSTIFIED_COMPATIBILITY (shadow/compat; forbidden as authority) |
| routeHints | REMOVED (E8 audit) |
| scopeToRouteId | REMOVED (E5.S7) |

## Próximo

**E9.S7** — architecture audit — **ATENDIDO** (`e9-s7-architecture-audit.md`).  
**E9.S8** — verify-final — **ATENDIDO_PARCIAL** (`e9-s8-verify-final.md`). Próximo: **E9.S9**.
