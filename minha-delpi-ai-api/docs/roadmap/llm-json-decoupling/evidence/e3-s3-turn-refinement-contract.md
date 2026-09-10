# E3.S3 — Contrato canônico de Turn Refinement

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** D (plano 03)  
**Harness:** `tests/unit/domain/services/test_e3_s3_turn_refinement_contract.py` (7 passed)

## Owner

| Peça | Path |
|------|------|
| DTO + schema | `app/domain/entities/turn_refinement.py` |
| Validator / fallback / ensure | `app/domain/services/turn_refinement_validator_service.py` |
| Adapter legado | `TurnRefinement.from_legacy_operational_refinement` |
| Planners legados | ainda authority (`OperationalRefinement`) — **sem cutover** |

## Contrato

```json
{
  "contractVersion": 1,
  "kind": "argument_delta|presentation_delta|clarify|no_op|unknown",
  "target": {
    "kind": "action|result_set|topic|unknown",
    "actionId": "…",
    "resultSetId": null,
    "topicId": null,
    "ordinal": null
  },
  "argumentDelta": {"page": 2, "branch": "02"},
  "clearedArguments": ["branch"],
  "presentationDelta": {"view": "table"} | null,
  "confidence": 0.0-1.0,
  "clarification": {"reason": "…", "promptHint": "…", "candidates": []} | null,
  "conflicts": [
    {
      "argument": "branch",
      "inheritedValue": "01",
      "proposedValue": "02",
      "resolution": "explicit_wins"
    }
  ],
  "reason": "…",
  "source": "heuristic|legacy_operational_refinement|fallback"
}
```

## Invariantes

- Path / `operationId` / `routeSegment` / `pathContains` **não** entram como chave de decisão semântica (`FORBIDDEN_SEMANTIC_KEYS`).
- Explicit current-turn value vence herdado (`resolution=explicit_wins`) e gera entrada em `conflicts`.
- Malformed → `kind=clarify` fallback.
- Adapter legado mapeia `OperationalRefinement` → contrato **sem** promover `previous_path`/`route_segment`.

## Aceite

```text
SCHEMA_WITHOUT_PATH_DECISION_KEYS = PASS
FROM_DICT_ROUNDTRIP = PASS
MALFORMED_FALLBACK_CLARIFY = PASS
INVALID_KIND_NORMALIZED = PASS
FORBIDDEN_FIELDS_STRIPPED = PASS
CONFLICTING_INHERITED_ARG = PASS
LEGACY_ADAPTER_PAGINATION = PASS
PRESENTATION_AND_CLARIFY_SHAPES = PASS
NO_CUTOVER_OF_PLANNERS = PASS
```

## Próximo

**E3.S4** — schema-driven argument binder (OpenAPI parameters/requestBody como autoridade).
