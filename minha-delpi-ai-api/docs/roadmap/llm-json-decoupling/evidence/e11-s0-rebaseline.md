# E11.S0 — Rebaseline / inventário / freeze

**Status:** COMPLETE_GATE  
**BASE_GIT_SHA:** `8bc84fc6d1cea3edc8cd0c08dceee90f9303e777`  
**Data:** 2026-09-11  
**Métricas:** [`e11-s0-debt-metrics.json`](./e11-s0-debt-metrics.json)

## Working tree preservada (não-AI / fora do escopo)

Não tocar nestes paths nesta onda:

- `M .cursor/rules/production-pulse-admin-hub.mdc`
- `M docs/12-roadmap-e-evolucao/production-pulse/**`
- `M production-pulse-api/**` (+ untracked deletion services)
- `M minha-delpi-ai-api/docs/knowledge/_generated/api-delpi-openapi-catalog.md` (generated drift)
- `?? evidence/e10-latency-audit-live.{json,md}` (auditoria prévia; escopo separado)

## Freeze corpus candidate Onda J

| Artefato | Version | SHA-256 |
|---|---|---|
| `tests/fixtures/intelligence_baseline/routing_cases.json` | `intelligence_baseline/routing_cases.json@v1` | `7ff3733293815064c9dd346a74b848623ade2113d987b4690adf81a3388e039d` |
| `tests/fixtures/intelligence_baseline/r1_r11_corpus_v1.json` | `r1_r11_corpus_v1` | `371f0cfa802188c805f986ff15452e152a5f98e636132fa81145fad7cfcf26b8` |
| Baseline histórico Onda A | `onda-a-baseline/manifest.json` | datasetHash igual ao routing_cases acima |

**Regra:** PASS A–I = baseline/histórico. Candidate final só em E11.S9 no HEAD pós-cleanup, mesmo corpus/config.

## Métricas de dívida (resumo HEAD)

| Métrica | Valor aprox. |
|---|---|
| PATH_COUPLED_RUNTIME_RULES | 250 |
| OPERATION_ID_COUPLED_RUNTIME_RULES | 189 |
| ENDPOINT_STRATEGY_RULES | 37 |
| MANUAL_INTENT_RULES | 18 |
| TECHNICAL_CATALOG_ENTRIES | 84 routes / 96 operationIds; 13 recommendationQueries profiles |
| HARDCODED_SMOKE_CREDENTIAL_DEFAULTS | 166 |
| DOMAIN_SERVICES_WITH_INFRA_IO | 19 |
| APPLICATION_SERVICES_COMPOSING_INFRA_DIRECTLY | 111 |
| CONTENT_LATERAL_PATH_KEYS (`pathMarkers` etc.) | **0** (JSON limpo; dívida migrou para Python) |

## Inventário D11 (CONFIRMADO_NO_CODIGO)

| Drift | Producer | Consumers (principais) | Fallback | Tests | Docs |
|---|---|---|---|---|---|
| D11-01 | `api_route_domain_inference_service.py` `_DOMAIN_RULES` | importer stamp; `ChatOperationalApiDomainService`; execute UC; route selection; follow-up; memory; product evidence | explicit metadata → markers → `generic` | `test_e10_api_route_domain_inference.py` | Plano 11/10 |

> **Supersessão pós-E11.S2:** `_DOMAIN_RULES` / path authority **removidos** (`SEMANTIC_PATH_DOMAIN_MAP=0`). Producer vigente = metadata semântica (`apiRouteDomain` / entity / `semanticBindings`). Detalhe: [`e11-s2-api-route-domain-semantic.md`](./e11-s2-api-route-domain-semantic.md). A linha D11-01 acima permanece como inventário do freeze S0.
| D11-02 | `ParameterStrategyInferenceService` | action resolver; vocabulary matcher; execute UC; registry generator; domain service | route.parameters.strategy → path/oid → semantic | `test_e9_s12e_parameter_strategy_inference.py` | E11.S3 |
| D11-03 | `RouteSegmentInferenceService` + inventory FS | registry service; domain selection; action resolver | map vazio; path-tail keys | `test_route_segment_inference_service.py` | E11.S4 |
| D11-04 | `operational_route_registry.json` `operationIds` + `select_registry_route_id` | resolver; selection facades; playbook readiness | pathMarkers/opIdMarkers compat | `test_e1_s4_*`, `test_e1_s6b_*` | E11.S5 |
| D11-05 | `ChatTurnAnalysisService` ∥ `ChatTurnUnderstanding*` ∥ `ChatIntentRouter` ∥ mappers | router overlay; product/KPI/production intent; task planner; shadow | dials off → heurística | `test_e2_s4_*`, `test_e2_s5_*` | E11.S6 |
| D11-06 | `recommendationQueries` + contextual producer | humanized response; smoke oracle E9.S15 | LEGACY_FALLBACK se candidate vazio | `test_e6_s4_*` | E11.S7 |
| D11-07 | `ChatCapabilityDiscoveryService` defaults `read`/`low`/`parallelSafe` | task planner; prep discovery | registry JSON não authority | `test_e4_s2_*` | E11.S7 |
| D11-08 | domain FS (`route_segment_*`, registry); app→infra ×111 | send/stream use cases; assembly; admin health | N/A | clean-arch lint | E11.S8 |
| D11-09 | `SMOKE_USER=rober` / `SMOKE_PASSWORD=1234` defaults | ~84 scripts smoke/eval | env override | higiene | E11.S8 |
| D11-10 | evidência E9.S10 pré-E10 domain motor | docs/gates reusando unknown PASS | — | `test_e9_s10_*` histórico | E11.S9 |

## Classificação evidências A–I

| Onda | Classificação | Motivo |
|---|---|---|
| A | BASELINE_HISTORICO | freeze/corpus |
| B | INVALIDAS_PARA_CANDIDATE | D11-04 residual |
| C | INVALIDAS_PARA_CANDIDATE | D11-05 |
| D | INVALIDAS_PARA_CANDIDATE | D11-02/03 |
| E | INVALIDAS_PARA_CANDIDATE | D11-07 |
| F | INVALIDAS_PARA_CANDIDATE | D11-06 |
| G | BASELINE_HISTORICO | revalidar em S9; sem D11 dedicado |
| H | INVALIDAS_PARA_CANDIDATE | PASS pré-drifts; D11-10 |
| I | INVALIDAS_PARA_CANDIDATE | `_DOMAIN_RULES` = substituto; D11-01 |

## READY_TO_EXECUTE E11.S1

- [x] CURRENT confirmado no HEAD `8bc84fc6…`
- [x] drifts D11-01..10 com producer/consumer/fallback/test/doc
- [x] métricas §4 capturadas
- [x] corpus frozen
- [x] PASS históricos não usados como candidate
- [x] próximo passo = Architecture Enforcement contra substitutos semânticos (gate vermelho no baseline)
