# E3.S6 — Pagination/filter fast paths (schema-bound)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** D (plano 03)  
**Harness:** `tests/unit/application/services/test_e3_s6_schema_driven_pagination_filter.py` (6 passed)

## Owner

| Peça | Path |
|------|------|
| Fast path | `app/application/services/schema_driven_pagination_filter_service.py` |
| Parsers | `ChatOperationalRefinementService` (page/size/next/prev) |
| Binder | `SchemaDrivenArgumentBinderService` (E3.S4) |

## Fluxo

```text
message
→ extract_argument_delta (determinístico)
→ TurnRefinement.argumentDelta
→ SchemaDrivenArgumentBinderService
→ só params declarados no OpenAPI
```

## Guardrails

- `branch` só se a mensagem contém `filial` (evita falso positivo «página 3» → branch `03`).
- `warehouse` só com menção a armazém.
- Campo extraído mas ausente do schema → strip (não inventa binding).

## Aceite

```text
EXACT_PAGE_PHRASE = PASS
PAGE_SIZE_PHRASE = PASS
NEXT_PAGE = PASS
BRANCH_FILTER = PASS
FREE_PHRASE_DETERMINISTIC = PASS
FIELD_NOT_IN_SCHEMA_STRIPPED = PASS
NO_SIGNAL_NONE = PASS
```

## Próximo

**E3.S7** — cutover de `operational_follow_up_routing` (legado → shadow).
