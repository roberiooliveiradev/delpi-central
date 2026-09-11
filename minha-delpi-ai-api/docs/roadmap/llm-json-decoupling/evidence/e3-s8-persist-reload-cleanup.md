# E3.S8 — Persist/reload e cleanup

**Status:** `ATENDIDO` (2026-09-11) — Postgres `lastAction` + DELETE terms (E9.S12.A/B)  
**Onda:** D (plano 03)  
**Harness:** `tests/unit/domain/services/test_e3_s8_persist_reload_continuity.py`  
**Overlay:** `PostgresChatSessionMemoryRepository` (`memory_type=working`, `key=lastAction`)

## Feito

| Item | Evidência |
|------|-----------|
| Reload paginação via `previous_messages`/`toolCalls` | teste `reload_pagination_from_history` |
| Reload group-by por `actionId` após rename de path | teste `reload_group_by_via_action_id` |
| Segment follow-up estável pós-cutover E3.S7 | teste `follow_up_segment_stable` |
| Filter schema-bound com inherited | teste `schema_filter_reload` |
| DELETE `messageSegmentTerms` / `playbookPathMarkers` | E9.S12.A/B |
| **Postgres overlay `lastAction`** | sync/load + merge history-wins; sanitize bounded |

## Política de merge

```text
histórico com toolCall ok → lastAction do extractor
histórico vazio + overlay lastAction → preserva overlay (F5 fraco)
clear contexto / marker → lastAction=None + deactivate working row
```

## Aceite

```text
PERSIST_RELOAD_HISTORY = PASS
GROUP_BY_ACTION_ID_RELOAD = PASS
FOLLOW_UP_SEGMENT_STABLE = PASS
SCHEMA_FILTER_INHERITED = PASS
DELETE_TERMS = PASS (E9.S12.A/B)
POSTGRES_LAST_ACTION = PASS
```

## Onda D — fechamento

Plano 03: S1–S8 **ATENDIDO**.
