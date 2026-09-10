# E2.S1 — Inventário das árvores heurísticas de intent

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** C (plano 02)  
**Fonte:** Onda A §6 + greps HEAD (sem migração de runtime)

## Veredito

```text
HEURISTIC_TREE_INVENTORY = PASS
AUTHORITY_VS_SHADOW_DISTINGUISHED = PASS
CLASSIFICATION_MATRIX = PASS
NO_RUNTIME_MIGRATION = PASS
```

## Matriz por bundle

| Bundle | Authority? | Classe(s) | Impacto em routing/tool |
|--------|------------|-----------|-------------------------|
| `product_query_intent.json` | **YES** | SEMANTIC_ROUTING_HEURISTIC, VOCABULARY, FAST_PATH; UX_COPY=`directAnswerHeaders` | intent enum, route predicates, skip LLM tools |
| `production_operational_intent.json` | **YES** | SEMANTIC_ROUTING_HEURISTIC (+ pathTokens residual) | kind→route/action; SQL preempt |
| `department_kpi_rules.json` | **YES** | BUSINESS_RULE + SEMANTIC_ROUTING_HEURISTIC | rota virtual KPI |
| `analysis_intent_vocabulary.json` | **YES** | VOCABULARY → SEMANTIC_ROUTING_HEURISTIC | no-tool / compare / email-from-data |
| `intent_router.json` | **YES** | SEMANTIC_ROUTING_HEURISTIC | família top-level (RAG/web/presentation/meta) |
| `operational_pipeline_vocabulary.json` | **YES** (FP) | FAST_PATH, VOCABULARY | optimize operacional; format refinement |
| `turn_understanding.json` | **SHADOW** | LLM_COMPOSITION_CANDIDATE | metadata/admin only (`analyze_shadow`) |

## Consumers materiais (file:symbol)

### product_query_intent
- `ChatProductQueryIntentDetectionService.detect` / `refine_operational_intent_from_full`
- `ChatProductQueryIntentService` (facade)
- `ChatOperationalSubIntentService.resolve`
- `ChatIntentRouterHeuristicsService` (operational sub-intent)
- `OperationalRouteDomainSelectionService.select_*`
- `ChatOperationalIntentFastPathService` (FAST_PATH)
- `ChatProductQueryIntentCodeService.extract_product_code` — **VOCABULARY/entity KEEP** (R02-02)

### production_operational_intent
- `ChatProductionOperationalIntentService.resolve` / `path_token_for` / `matches_rest_route`
- `OperationalRouteDomainSelectionService.select_production_operational`
- `ChatProductionOperationalActionReadinessService`
- `ExternalActionSelectionPreflightService` / SQL fallback policy

### department_kpi_rules
- `ChatDepartmentKpiIntentService.resolve`
- `OperationalRouteDomainSelectionService.select_by_department_kpi`
- `ExternalActionRouteSelectionService.select_department_kpi`
- `ChatIntentRouterHeuristicsService.resolve_department_kpi`

### analysis_intent_vocabulary
- `ChatAnalysisIntentService.is_comparison_or_insight_request` / data interpretation / email-from-data
- Gates em `chat_turn_preparation_tool_routing_service`, preflight, intelligence pipeline

### intent_router
- `ChatIntentRouterClassifyService.classify` / `ChatIntentRouterHeuristicsService`
- Wired em `chat_turn_preparation_turn_analysis_service`

### operational_pipeline_vocabulary
- `ChatOperationalPipelineService.should_optimize`
- `ChatPresentationFormatRefinementIntentService` (presentation path)

### turn_understanding (shadow)
- `ChatTurnUnderstandingService.analyze` / `analyze_shadow`
- Flag `turnUnderstandingShadow` em `conversational_intelligence.json`
- Preparação grava `workspace_context["shadowTurnUnderstanding"]` — **não** altera tool choice

## Padrão residual (ainda authority)

```text
mensagem
→ normalização
→ terms/regex/excludes
→ anyOf/allOf/noneOf/customPredicate
→ intent/domain/path hint
→ routing
```

## Fora de escopo E2.S1

- Migrar/apagar listas
- Promover TU a authority
- Dump literal de todas as strings de cada pipeline

## Próximo

**E2.S2** — baseline corpus authority vs shadow TU (`evidence/e2-s2-understanding-baseline.md`).
