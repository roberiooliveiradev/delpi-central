# E3.S4 — Schema-driven argument binder

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** D (plano 03)  
**Harness:** `tests/unit/application/services/test_e3_s4_schema_driven_argument_binder.py` (7 passed)

## Owner

| Peça | Path |
|------|------|
| Orquestrador | `app/application/services/schema_driven_argument_binder_service.py` |
| Contrato entrada | `TurnRefinement` (E3.S3) |
| Coerção | `ChatOpenApiArgumentCoercionService` |
| Strip schema | `ChatToolParameterGroundingService.retain_declared_parameters` |
| Validação | `ValidateActionArgumentsService` + `ExternalActionExecutionPolicy` |

**Não** estende `ParameterStrategyShadowService` (ownership E1/strategy).  
**Não** cutover dos planners `OperationalRefinement` (E3.S5–S7).

## Fluxo

```text
TurnRefinement.argumentDelta + clearedArguments
+ inherited parameters/body
→ merge (explicit wins)
→ retain OpenAPI-declared names only
→ coerce (date/int determinístico)
→ ValidateActionArgumentsService
→ {ok, parameters, body} | clarify(missing/invalid)
```

## Aceite

```text
REQUIRED_PRESENT = PASS
REQUIRED_MISSING_CLARIFY = PASS
PATH_QUERY_UNKNOWN_STRIPPED = PASS
INVALID_ENUM = PASS
INVALID_TYPE = PASS
DATE_FORMAT = PASS
BODY_REQUIRED = PASS
ADDITIONAL_PROPERTIES_FALSE = PASS
CONFLICTING_INHERITED_EXPLICIT_WINS = PASS
NO_INVENTED_REQUIRED = PASS
NO_PLANNER_CUTOVER = PASS
```

## Próximo

**E3.S5** — group-by/refetch sem `pathContains` (capability/schema).
