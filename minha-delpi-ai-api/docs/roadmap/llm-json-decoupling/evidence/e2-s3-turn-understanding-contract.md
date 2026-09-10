# E2.S3 — Contrato canônico de Turn Understanding

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** C (plano 02)  
**Harness:** `tests/unit/domain/services/test_e2_s3_turn_understanding_contract.py`

## Owner

| Peça | Path |
|------|------|
| DTO + schema | `app/domain/entities/turn_understanding.py` |
| Validator / fallback | `app/domain/services/turn_understanding_validator_service.py` |
| Producer heurístico | `ChatTurnUnderstandingService.analyze` → `ensure()` |
| Consumers shadow | `shadowTurnUnderstanding`, `ChatTaskPlannerService.build_from_understanding` |

## Contrato

```json
{
  "contractVersion": 1,
  "userGoal": "…",
  "goals": [
    {
      "goalId": "st-1",
      "intent": "consultar estoque…",
      "entities": {"productCode": "10080001"},
      "dependsOn": [],
      "kind": "lookup|action|reasoning|unknown",
      "status": "pending"
    }
  ],
  "presentationIntent": {"view": "table"} | null,
  "needsTool": true | false | null,
  "confidence": 0.0-1.0,
  "source": "heuristic|fallback"
}
```

- `intent` = prosa semântica (não enum de endpoint).
- Entities proíbem `pathToken` / markers / `parameterStrategy`.
- `subtasks` legado continua no `as_dict` para compat.

## Aceite

```text
SCHEMA_GOALS_WITHOUT_PATH_TOKEN = PASS
FROM_DICT_ROUNDTRIP = PASS
MALFORMED_FALLBACK = PASS
MISSING_GOALS_FALLBACK = PASS
FORBIDDEN_ENTITY_STRIPPED = PASS
ANALYZE_EMITS_VALIDATED_CONTRACT = PASS
PRODUCT_CODE_ENTITY_HINT = PASS
NO_ENDPOINT_INTENT_ENUM = PASS
```

## Próximo

E2.S4 shadow-compare (sem cutover) → cutover só com agree estável.
