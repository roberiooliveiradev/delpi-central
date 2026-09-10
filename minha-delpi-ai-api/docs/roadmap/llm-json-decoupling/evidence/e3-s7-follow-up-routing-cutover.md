# E3.S7 — Follow-up routing cutover

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** D (plano 03)  
**Harness:** `tests/unit/domain/services/test_e3_s7_follow_up_routing_cutover.py`

## Decisão

```text
ANTES: messageSegmentTerms → routeSegment (authority)
DEPOIS: follow_up_type → routeSegment (authority)
       messageSegmentTerms → observer (segment_from_message_terms)
```

Flag em `operational_follow_up_routing.json`:

```json
"authorityShadow": { "enabled": true, "cutoverEnabled": true }
```

## Owner

| Peça | Path |
|------|------|
| Cutover + APIs | `ChatOperationalFollowUpRoutingService` |
| Shadow log | `FollowUpRoutingAuthorityShadowService` |
| Intent estruturado | `ChatFollowUpIntentService.follow_up_type` |

## Aceite

```text
CUTOVER_ENABLED = PASS
SHIPPING_AGREE = PASS
STRUCTURE_EXCLUSIVITY_VIA_TYPE = PASS
TOPIC_SWITCH_NO_SEGMENT = PASS
PREFERRED_ROUTE_ID_SIBLING = PASS
TERMS_OBSERVER_API = PASS
BASELINE_E3_S2_GREEN = PASS
```

## Nota

DELETE de `messageSegmentTerms` / fields mortos → **E3.S8 / Onda H** (só após evidência estável). Path markers de date inheritance ainda residuais.

## Próximo

**E3.S8** — persist/reload + cleanup de terms mortos (conservador).
