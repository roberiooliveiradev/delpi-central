# E10.S1 — Inventário de mapas laterais por path

**Data:** 2026-09-11  
**Política:** `NENHUM MAPA LATERAL DEVE EXISTIR`  
**Plano:** [`../planos/10-zero-lateral-path-maps.md`](../planos/10-zero-lateral-path-maps.md)

## Contrato alvo

```text
OpenAPI importado
→ Action Catalog (path/operationId/tags/delpiMetadata.apiRouteDomain)
→ ApiRouteDomainInferenceService (bridge a partir do path do contrato)
→ consumers (execute / follow-up / affinity)
```

JSON do assistente: UX/copy, parameterStrategies (bindings), labels de domínio — **sem** `pathMarkers` / `pathToken` / `pathContains` / `pathRules` como mapa lateral.

## Inventário (producers → consumers)

| Superfície content | Consumer(s) | Destino E10 |
|---|---|---|
| `api_route_domains.json` domains.*.pathMarkers | `ChatOperationalApiDomainService` | **REMOVED** → `ApiRouteDomainInferenceService` + stamp no import |
| `operational_factual_verdict.json` pathMarkers | factual verdict services | **REMOVED** → `entityKeys` |
| `operational_sufficiency_critic.json` pathMarkers | sufficiency critic | **REMOVED** → profileKeys/anomalyTypes |
| `product_enrichment_composition.json` pathMarkers | anomaly follow-up | **REMOVED** |
| `external_action_responses.json` pathMarkers/pathContains* | candidate prioritization / empty rival | **REMOVED** → operationIdContains / operationIds |
| `department_kpi_rules.json` pathToken | KPI intent | **RENAMED** → `catalogToken` + `domainTag` |
| `column_labels.json` pathContains | column label detect | **REMOVED** → `operationIdContains` / keys |
| `operational_group_by_refinement.json` pathContains | group-by match | **REMOVED** → `operationIdContains` / actionId |
| `presentation_profiles.json` pathRules | presentation resolve | **REMOVED** → entityProfiles + OpenAPI deriver |
| `openapi_tool_routing.json` | gate CI (string proibida) | **KEEP** como padrão proibido (não é mapa) |

## Gate

`tests/unit/domain/services/test_e10_zero_lateral_path_maps.py` — zero object keys proibidas em `app/content/pt-BR/assistant/**/*.json`.

## Status S1

**ATENDIDO** com inventário + gate + contrato alvo.
