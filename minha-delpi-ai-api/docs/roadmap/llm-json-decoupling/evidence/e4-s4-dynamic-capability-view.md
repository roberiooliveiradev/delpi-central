# E4.S4 — Dynamic capability view

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 04)

## Owner

| Superfície | Fonte |
|------------|--------|
| Help «o que você pode fazer?» | `ChatCapabilitiesService.build_direct_answer` + `format_action_catalog` (Action Catalog + `allowed_action_ids`) |
| Copy/seções | `capabilities.json` (UX, não authority técnica) |
| Não-OpenAPI | registry `rag`/`web`/`skill`/`transform` (discovery) |

## Aceite

```text
DYNAMIC_ALLOWED_CAPABILITIES = PASS
AUTHORIZED_ONLY = PASS
PATHRULES_NOT_REQUIRED = PASS
```

Help nunca lista action fora de `allowed_action_ids` (E4.S2 + `test_chat_capabilities_service`).
