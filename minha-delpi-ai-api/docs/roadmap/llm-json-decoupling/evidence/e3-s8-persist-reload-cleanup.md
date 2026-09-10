# E3.S8 — Persist/reload e cleanup (parcial)

**Status:** `ATENDIDO_PARCIAL` (2026-09-10)  
**Onda:** D (plano 03)  
**Harness:** `tests/unit/domain/services/test_e3_s8_persist_reload_continuity.py`

## Feito

| Item | Evidência |
|------|-----------|
| Reload paginação via `previous_messages`/`toolCalls` | teste `reload_pagination_from_history` |
| Reload group-by por `actionId` após rename de path | teste `reload_group_by_via_action_id` |
| Segment follow-up estável pós-cutover E3.S7 | teste `follow_up_segment_stable` |
| Filter schema-bound com inherited | teste `schema_filter_reload` |
| `messageSegmentTerms` marcado observer + delete deferred | `authorityShadow.deleteDeferredToWaveH` |

## Não feito (explícito)

- **DELETE** de `messageSegmentTerms` / `playbookPathMarkers` mortos → **Onda H / plano 09** (mesmo padrão do registry E1).
- Materialização Postgres de `lastAction`/`resultSets` — F5 continua dependente do histórico de mensagens (inventário E3.S1).

## Aceite

```text
PERSIST_RELOAD_HISTORY = PASS
GROUP_BY_ACTION_ID_RELOAD = PASS
FOLLOW_UP_SEGMENT_STABLE = PASS
SCHEMA_FILTER_INHERITED = PASS
DELETE_TERMS = DEFERRED_WAVE_H
```

## Onda D — fechamento

Plano 03: S1–S7 **ATENDIDO**; S8 **ATENDIDO_PARCIAL**.  
Próxima onda material do programa: E (caps/composition) ou H (cleanup DELETE) conforme ledger.
