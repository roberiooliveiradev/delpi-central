# Onda A — Inventário de ownership (2026-09-10)

**Status:** ATENDIDO  
**gitSha:** `79f3a21f9b54ff0e0aa16b9f3ada2b0c032c7b92`  
**Escopo:** consumers Python dos nós técnicos prioritários; classificação de destino; estratégia de cutover por plano.  
**Não altera runtime.**

## 1. Resumo executivo

| Área | Autoridade HEAD | Plano | Cutover |
|------|-----------------|-------|---------|
| Cold path action selection | OpenAPI-first (retrieval/planner) | 01 | Residual only |
| Registry markers / `parameters.strategy` | Residual routing + composition + readiness | 01 | Shadow → remove |
| `api_route_domains` path→strategy | Binding residual | 01 / 03 | Binder genérico |
| Intent vocabularies | Authority | 02 | TU authority |
| `turn_understanding` | Shadow | 02 | Promote |
| Follow-up / refinement path markers | Authority residual | 03 | State + schema |
| `capability_registry.action.*` | Discovery/planner | 04 | Action Catalog |
| `capabilities.pathRules` | Removido (D1) | 04 | — |
| Composition `routeIds` | Authority | 05 | Planner + budget |
| `recommendationQueries` | Authority no turno | 06 | Contextual + fallback |
| Presentation path residual | Parcialmente limpo | 07 | Schema-first |
| Skills path hints | Residual | 08 | Runtime lookup |

## 2. `operational_route_registry.json` — fields técnicos

Schema note: rotas usam `id` (não `routeId`); strategy em `parameters.strategy`.

### pathMarkers / operationIdMarkers / excludePathMarkers / pathSuffix / pathExactEnd / method

| Consumer | Classe | Estratégia |
|----------|--------|------------|
| `operational_route_action_resolver_service.py` | routing | Migrar match para Action Catalog / binder |
| `external_action_selection_service.py` (`select_registry_route_id`) | routing | Remover preempção residual |
| `chat_playbook_product_action_readiness_service.py` | readiness | Derivar de catalog allowed actions |
| `operational_route_registry_service.py` (`route_path_marker_for_segment`) | routing | Substituir por actionId/semantic |
| `chat_grounded_capability_planning_service.py` | routing | Plano 05 — goals + catalog |
| `chat_entity_capability_catalog_service.py` | routing | Plano 05 |
| `operational_route_domain_selection_service.py` | routing | KPI synthetic — reavaliar |
| `operational_route_registry_lint_service.py` / generator | lint/test | Atualizar após cutover |
| testes path-marker shadow | lint/test | Manter até cleanup 09 |

### routeSegment / priority / id

| Consumer | Classe | Estratégia |
|----------|--------|------------|
| `operational_route_registry_service.py` | routing | Lookup por actionId |
| `external_action_refinement_route_selection_service.py` | routing | Plano 03 |
| `chat_operational_refinement_pagination_service.py` | routing | Plano 03 |
| composition planners (product/department/anomaly) | routing | Plano 05 |
| `chat_operational_sufficiency_critic_service.py` | routing/policy | Separar policy transversal |
| `chat_tool_context_service.py` (`enrichmentRouteId`) | telemetry | Renomear para actionId quando possível |
| `fallbackPolicies` → sql fallback | **policy** | **KEEP** — não é catálogo técnico |

### parameters.strategy

| Consumer | Classe | Estratégia |
|----------|--------|------------|
| `operational_route_action_resolver_service.py` | routing/binding | Plano 01 E1.S5 — OpenAPI binder |
| `operational_route_vocabulary_matcher_service.py` | routing | Remover dependência |
| lint/generator | lint/test | Atualizar gates |

## 3. `api_route_domains.json`

| Consumer | Role | Estratégia |
|----------|------|------------|
| `ChatOperationalApiDomainService` | path→domain + strategy | Duplicação técnica → binder OpenAPI |
| `OperationalApiParameterBuilderService` | aplica strategies | Preservar só rules transversais justificadas |
| execute metadata / follow-up path classify | telemetry / routing | Telemetry ok; classify via action |
| lint/generator | lint/test | Pós-cutover |

**Classificação do nó:** `TECHNICAL_CONTRACT_DUPLICATION`.

## 4. Capabilities / registry actions

| Nó | Estado | Classificação | Plano |
|----|--------|---------------|-------|
| `capabilities.pathRules` | **REMOVIDO** | DEAD_CONTENT | 04 R04-02 ATENDIDO |
| `capability_registry.action.*` whenToUse/description | Authority discovery | SEMANTIC_ROUTING_HEURISTIC (+ paths no texto) | 04 |
| `capability_registry.routeHints` | Zero reads | DEAD_CONTENT | 04 cleanup |
| `capabilities.json` help/detection | UX | UX_COPY / VOCABULARY / FAST_PATH | 04/08 KEEP copy |

## 5. `recommendationQueries`

| Consumer | Role |
|----------|------|
| `chat_data_insight_service.py` | **Authority** no turno (delta LLM=0) |
| humanized response / coverage / quality | Fallback + gates |
| testes profile coverage | Gate D2 |

**Classificação:** `SEMANTIC_PRESENTATION_METADATA` — plano 06 rebaixa a LEGACY_FALLBACK.

## 6. Intents / Turn Understanding

| Bundle | Authority? | Classificação | Plano |
|--------|------------|---------------|-------|
| `product_query_intent` | Authority | VOCABULARY + SEMANTIC_ROUTING_HEURISTIC | 02 |
| `production_operational_intent` | Authority | SEMANTIC + pathTokens técnicos | 02 |
| `department_kpi_rules` | Authority | BUSINESS_RULE + path tokens | 02 |
| `analysis_intent_vocabulary` | Authority | VOCABULARY | 02 |
| `intent_router` | Authority | SEMANTIC_ROUTING_HEURISTIC | 02 |
| `operational_pipeline_vocabulary` | Authority / FAST_PATH | VOCABULARY / FAST_PATH | 02 |
| `turn_understanding` | **Shadow** | LLM_COMPOSITION_CANDIDATE | 02 |

## 7. Classificação consolidada (Onda A §4)

| Classificação | Exemplos |
|--------------|----------|
| TECHNICAL_CONTRACT_DUPLICATION | registry markers, api_route_domains strategy, pathTokens, routeHints text paths |
| SEMANTIC_ROUTING_HEURISTIC | intent terms, whenToUse, match predicates |
| SEMANTIC_PRESENTATION_METADATA | recommendationQueries, residual presentation maps |
| LLM_COMPOSITION_CANDIDATE | turn_understanding (promote), contextual recommendations |
| DETERMINISTIC_POLICY | fallbackPolicies SQL, RBAC/sensitivity |
| BUSINESS_RULE | department_kpi kinds |
| UX_COPY | capabilities help, skills editorial |
| VOCABULARY | analysis/pipeline vocab |
| FAST_PATH | pipeline vocabulary shortcuts |
| DEAD_CONTENT | pathRules (gone), routeHints unread |

## 8. Gaps conhecidos (não bloqueiam Onda A)

1. Corpus offline de freeze = 6 casos product_search — **insuficiente** para R1–R11 release (plano 09 E9.S1 amplia).
2. `openApiSchemaHash` / `actionCatalogHash` exigem snapshot do catálogo persistido (runtime/DB) — marcados `PENDING_RUNTIME` no manifest.
3. Não há harness único R1–R11 com pasta `docs/testing/evidence/runs/` — Onda A grava sob `llm-json-decoupling/evidence/`.

## 9. Pós-condição Onda A

```text
INVENTORY_COMPLETE = PASS
CONTENT_NODES_CLASSIFIED = PASS
BASELINE_OFFLINE_ROUTING_FROZEN = PASS (manifest + harness 6/6)
BASELINE_FLOW_FAMILY_MATRIX = PASS (25 cases)
OPENAPI_ACTION_CATALOG_HASH = PENDING_RUNTIME (plano 09)
R1_R11_FULL_CORPUS = PENDING (plano 09 E9.S1–S2)
```
