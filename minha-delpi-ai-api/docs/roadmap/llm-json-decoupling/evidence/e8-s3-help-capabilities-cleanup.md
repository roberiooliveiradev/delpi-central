# E8.S3 — Help/capabilities availability (actionId-first)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 08)  
**Harness:** `tests/unit/application/services/test_e8_s3_help_capabilities_action_id_match.py`

## Veredito

```text
HELP_REFLECTS_ALLOWED_CAPABILITIES = PASS
ACTION_ID_MATCH_PREFERRED = PASS
PATH_SUBSTRING_FALLBACK = PASS
UNAUTHORIZED_ACTION_ABSENT = PASS
E4_DYNAMIC_VIEW_UNTOUCHED = PASS
```

## Feito

1. **`AssistantCapabilitiesRegistry._matches_actions`** — dual-run:
   - tokens não-path → match exato em `allowed_action_ids`
   - tokens path-like (`/…`) → substring em `path|operationId` (legado)
2. **Piloto** `stock_lookup.requiredActions`: `["/stock", "get_product_stock"]`
3. Copy HTTP em `capabilities.json` (H02) **não** alterada → S6/doc se necessário
4. `format_action_catalog` (E4) **não** tocado

## Cascata

```text
requiredActions actionId/capability key
→ allowed_action_ids da sessão
→ (fallback) path substring legado
→ buckets availableNow / requiresPermission / requiresAgent
```

## Próximo

**E8.S4** — mixed bundles (`external_action_responses.actionSelection`).
