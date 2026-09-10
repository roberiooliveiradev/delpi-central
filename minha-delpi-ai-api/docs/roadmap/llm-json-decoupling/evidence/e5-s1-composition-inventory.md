# E5.S1 — Inventário de decisões de composição

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 05)  
**Fontes:** greps HEAD + JSON `content/pt-BR/assistant/` (sem migração runtime)

## Veredito

```text
FIXED_ROUTE_MAPS_INVENTORIED = PASS
LIVE_EXTRA_TOOL_PATH_IDENTIFIED = PASS
DEAD_JSON_PLANNERS_FLAGGED = PASS
BUDGET_CAPS_LIVE = PASS
NO_RUNTIME_MIGRATION = PASS
```

## Fluxos vivos (tool extra)

| Trigger | Cadeia | Extra tool? |
|---------|--------|-------------|
| Grounded enrich | Orchestration → `ChatGroundedCapabilityPlanningService` / `ChatGroundedEnrichPlanningService` → `artifactToEnrichKey` + `enrichInsightScopes` | Sim ≤ `maxExtraRoutes` |
| Multi-scope na mensagem | `ChatProductMultiScopePlanningService` (`_SCOPE_TO_ROUTE` hardcoded) | Sim |
| Sufficiency pós-tool | `ChatOperationalSufficiencyCriticService` → `followUpRouteIds` | Sim se maxAutoFollowUps>0 |
| Product dossier `composeRouteIds` | `ChatProductEnrichmentCompositionPlanningService.plan` | **DEAD_RUNTIME** (só testes) |
| Department meta `primary`/`compose` | `ChatDepartmentMetaCompositionPlanningService.plan` | **DEAD_RUNTIME** (só testes) |

## Matriz (resumo)

| ID | Artifact | Runtime | Class |
|----|----------|---------|-------|
| C01–C03 | `limits` / fan-out / mode caps | LIVE | DETERMINISTIC_POLICY |
| C04–C05 | `artifactToEnrichKey` / `enrichInsightScopes` | LIVE | SEMANTIC_ROUTING_HEURISTIC |
| C06 | `scopeToRouteId` | DEAD | SEMANTIC_ROUTING_HEURISTIC |
| C07 | `domains.*.capabilities` | DEAD | SEMANTIC_ROUTING_HEURISTIC |
| C08–C11 | department_meta_composition | DEAD | SEMANTIC (+ BUSINESS taxonomia dept) |
| C12–C14 | product_enrichment composeRouteIds | DEAD / orphan analyser | SEMANTIC / POLICY |
| C15–C16 | anomaly follow-up / invoice clarify | SEMI / LIVE chips | SEMANTIC / BUSINESS |
| C17–C18 | sufficiency `followUpRouteIds` + caps | LIVE | SEMANTIC / POLICY |
| C19 | follow_up `preferredRouteId` | LIVE | SEMANTIC (irmão plano 03) |
| C20–C21 | `_SCOPE_TO_ROUTE` / `_scope_to_intent` | LIVE | SEMANTIC (bypass C06) |
| C22 | enrichInsightFactsBudget | LIVE | POLICY (síntese) |

## Ledger R05

| RQ | Estado |
|----|--------|
| R05-01 budget vs routing | PARCIAL — caps vivos; maps C04/C05/C17/C20 vivos |
| R05-02 scope→route | PARCIAL — JSON morto; equivalentes em C05/C20/C21 |
| R05-03 redundância | HIPOTESE → E5.S3 |
| R05-04 enrich sem mapa | BLOQUEADO por C04/C05/C17 |
| R05-05 fan-out/safety | ATENDIDO nos caps |

## Próximo

**E5.S2** — baseline das famílias de composição (live paths + dead planners negativos).
