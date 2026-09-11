# Ledger de execução — llm-json-decoupling

**Fonte:** markdowns desta pasta (não `.cursor/plans`).  
**Atualizado:** 2026-09-11 — auditoria corretiva  
**Baseline histórico:** [`onda-a-baseline/manifest.json`](./onda-a-baseline/manifest.json) (`runId=0249db78-d6fd-45b3-84bf-d11abcd17a6a`)  
**Plano ativo:** [`../planos/11-corrective-cutover-generalization-cleanup.md`](../planos/11-corrective-cutover-generalization-cleanup.md)

> Os estados A–I abaixo registram o que foi declarado/concluído nos candidates históricos. A auditoria pós-implementação encontrou drifts que invalidam seu uso como aceite do estado atual. A única onda ativa para fechamento do programa é a **J**.

## Ondas

| Onda | Planos | Status vigente | Próxima subetapa | Notas |
|------|--------|----------------|------------------|-------|
| A — baseline/contratos | inventário + freeze | **HISTÓRICO / BASELINE** | — | Evidência preservada |
| B — routing universal | 01 | **HISTÓRICO / REVALIDAR NA J** | — | Registry/operationIds residual entra em E11.S5 |
| C — entendimento | 02 | **HISTÓRICO / REABERTO** | — | Semantic authority/heuristics entram em E11.S6 |
| D — multi-turn/args | 03 | **HISTÓRICO / REABERTO** | — | Path/operation continuity + strategy entram em E11.S3/S4 |
| E — caps/composition | 04, 05 | **HISTÓRICO / REVALIDAR NA J** | — | Capability metadata entra em E11.S7 |
| F — UX inteligente | 06 | **HISTÓRICO / REABERTO** | — | `recommendationQueries`/contextual cutover entra em E11.S7 |
| G — presentation/skills | 07, 08 | **HISTÓRICO / REVALIDAR NA J** | — | Candidate final E11.S9 |
| H — cutover/cleanup | 09 | **PASS HISTÓRICO; NÃO RELEASE VIGENTE** | — | Candidate evidence anterior a drifts posteriores |
| I — zero mapa lateral | 10 | **ACEITE INVALIDADO POR DRIFT** | — | Substitutos semânticos encontrados em runtime |
| J — correção arquitetural | 11 | **ABERTO / VERIFY_FINAL_FAILED** | **E11.S3** | E11.S0–S2 ATENDIDO; path→domain removido |

## Protocolo por subetapa

```text
abrir plano 11
→ revalidar HEAD + git status
→ READY_TO_EXECUTE?
→ baseline/precondition
→ implementar menor escopo no owner canônico
→ wiring real
→ unit/contract
→ positive + sibling + negative
→ generalization/metamorphic/unknown quando aplicável
→ adversarial diff review
→ semantic residual search
→ postconditions
→ COMPLETE_GATE
→ atualizar STATUS/evidência
→ só então avançar dependente
```

## Regras de fechamento

Não marcar `ATENDIDO/COMPLETED/100%` se item material permanecer em:

```text
PARTIAL
ATENDIDO_PARCIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
DEFERRED sem justificativa
TODO/FIXME/HACK/TEMPORARY
flag/fallback sem exit criteria
```

Qualquer mudança material posterior ao candidate invalida as dimensões de evidence afetadas até rerun no novo HEAD.

## Proibições

- Não criar `.plan.md` paralelo para este programa.
- Não remover catálogo/heurística e recriar a mesma authority em Python/TS/JSON/prompt/metadata.
- Não DELETE de authority antes de cutover + generalização aplicável.
- Não reintroduzir `pathRules` / `capabilityGroup` por endpoint.
- Não usar mensagem nonsense como prova de unknown external API.
- Não reaproveitar PASS de SHA/config anterior como candidate final depois de alteração material.
- Drift material → `EXECUTION_DRIFT` no Plano 11 + STOP-THE-LINE no subgrafo.

## Registro de progresso histórico

| Data | Evento |
|------|--------|
| 2026-09-10 | Drifts documentais 01/02/04/06/roadmap/README/prompt |
| 2026-09-10 | Onda A ATENDIDA (inventário + baseline offline + matrix 25) |
| 2026-09-10 | Ledger B–H materializado; execução = markdowns |
| 2026-09-10 | Onda B E1.S3 documentado GAPS_BLOCKING (sem cutover runtime) |
| 2026-09-10 | E1.S3 PASS — harness top-K 9/9 (families + metamorphic) |
| 2026-09-10 | E1.S4 SHADOW_ON — `registrySelectionShadow` metadata (sem cutover) |
| 2026-09-10 | E1.S4 — product intent/segment shadow + observability log |
| 2026-09-10 | E1.S5 SHADOW_ON — parameterStrategy none/semantic/sale_orders |
| 2026-09-10 | E1.S5 CUTOVER_PARTIAL — authority OpenAPI binder (flag cutoverEnabled) |
| 2026-09-10 | E1.S5 — cutover supplier_part_number + supplies_stock (sem pular) |
| 2026-09-10 | E1.S5 **ATENDIDO** — cutover completo (fila resolver; sql fora) |
| 2026-09-10 | E1.S6 **PARTIAL** — fatia A: binder permanente + switch tipado removido (sem DELETE registry) |
| 2026-09-10 | E1.S4 **AGREE_AGG_ON** — audit snapshot + `GET /admin/metrics/registry-selection-shadow/summary` |
| 2026-09-10 | E1.S6B **ATENDIDO** — cutover seleção OpenAPI-first (`cutoverEnabled`) |
| 2026-09-10 | Onda B **ATENDIDO_PARCIAL** — DELETE JSON registry deferred (ledger / Onda H) |
| 2026-09-10 | E2.S1 **ATENDIDO** — inventário heurísticas intent (Onda C) |
| 2026-09-10 | E2.S2 **ATENDIDO** — baseline authority vs shadow TU (10 famílias) |
| 2026-09-10 | E2.S3 **ATENDIDO** — contrato canônico TU (schema/validator/fallback) |
| 2026-09-10 | E2.S4 **SHADOW_ON** — authority vs TU (sem cutover) |
| 2026-09-10 | Onda C **ATENDIDO_PARCIAL** — cutover/DELETE intents deferred |
| 2026-09-10 | E3.S1 **ATENDIDO** — inventário grafo multi-turn (Onda D) |
| 2026-09-10 | E3.S2 **ATENDIDO** — baseline follow-up/refinement (10 famílias) |
| 2026-09-10 | Onda D **EM_ANDAMENTO** — próxima E3.S3 |
| 2026-09-10 | E3.S3 **ATENDIDO** — contrato canônico Turn Refinement (sem cutover planners) |
| 2026-09-10 | Onda D **EM_ANDAMENTO** — próxima E3.S4 |
| 2026-09-10 | E3.S4 **ATENDIDO** — schema-driven argument binder (OpenAPI authority) |
| 2026-09-10 | Onda D **EM_ANDAMENTO** — próxima E3.S5 |
| 2026-09-10 | E3.S5 **ATENDIDO** — group-by schema/actionId (pathContains só fallback) |
| 2026-09-10 | Onda D **EM_ANDAMENTO** — próxima E3.S6 |
| 2026-09-10 | E3.S6 **ATENDIDO** — pagination/filter fast path schema-bound |
| 2026-09-10 | Onda D **EM_ANDAMENTO** — próxima E3.S7 |
| 2026-09-10 | E3.S7 **ATENDIDO** — cutover follow_up_type→routeSegment (terms observer) |
| 2026-09-10 | Onda D **EM_ANDAMENTO** — próxima E3.S8 |
| 2026-09-10 | E3.S8 **ATENDIDO_PARCIAL** — reload via histórico; DELETE terms → Onda H |
| 2026-09-10 | Onda D **ATENDIDO_PARCIAL** — plano 03 S1–S7 OK |
| 2026-09-10 | E4.S1 **ATENDIDO** — inventário capabilities/registry (Onda E) |
| 2026-09-10 | E4.S2 **ATENDIDO** — baseline discovery + help allowed_ids |
| 2026-09-10 | Onda E **EM_ANDAMENTO** — próxima E4.S3 |
| 2026-09-10 | E4.S3 **ATENDIDO** — contrato uxCapability (path não-authority) |
| 2026-09-10 | Onda E **EM_ANDAMENTO** — próxima E4.S4 |
| 2026-09-10 | E4.S4–S5 **ATENDIDO** — dynamic help + remove action.* mini-catalog |
| 2026-09-10 | Plano 04 **ATENDIDO** — Onda E segue no plano 05 |
| 2026-09-10 | E5.S1 **ATENDIDO** — inventário decisões de composição |
| 2026-09-10 | E5.S2 **ATENDIDO** — baseline composition (6 famílias + enrich/budget) |
| 2026-09-10 | E5.S3 **ATENDIDO** — contrato Goal Coverage (fulfilled/partial/blocked/needs_more_data) |
| 2026-09-10 | E5.S4 **ATENDIDO** — planner-driven enrichment (coverage retry allowed-only) |
| 2026-09-10 | E5.S5 **ATENDIDO** — department composition goals+retrieval (route maps deprecated) |
| 2026-09-10 | E5.S6 **ATENDIDO** — entity enrichment goals (enrich maps deprecated; caps mantidos) |
| 2026-09-10 | E5.S7 **ATENDIDO** — DELETE maps mortos entity/department; caps preservados |
| 2026-09-10 | Plano 05 / Onda E **ATENDIDO** — próxima Onda F (plano 06) |
| 2026-09-10 | E6.S1 **ATENDIDO** — inventário + baseline recommendations/composer (6 famílias) |
| 2026-09-10 | Onda F **EM_ANDAMENTO** — próxima E6.S2 (grounding contract) |
| 2026-09-10 | E6.S2 **ATENDIDO** — RecommendationGroundingContext + caps (sem cutover producer) |
| 2026-09-10 | Onda F **EM_ANDAMENTO** — próxima E6.S3 (contextual producer) |
| 2026-09-10 | E6.S3 **ATENDIDO** — producer contextual + wiring attach (delta LLM=0) |
| 2026-09-10 | Onda F **EM_ANDAMENTO** — próxima E6.S4 (queries → LEGACY_FALLBACK) |
| 2026-09-10 | E6.S4 **ATENDIDO** — recommendationQueries LEGACY_FALLBACK + dual-run |
| 2026-09-10 | Onda F **EM_ANDAMENTO** — próxima E6.S5 (composer contextual) |
| 2026-09-10 | E6.S5 **ATENDIDO** — composer cache + allowlist + entities (sem LLM/tecla) |
| 2026-09-10 | Onda F **EM_ANDAMENTO** — próxima E6.S6 (cleanup) |
| 2026-09-10 | E6.S6 **ATENDIDO** — cleanup seguro; plano 06 / Onda F fechados |
| 2026-09-10 | Próxima **Onda G** (planos 07/08) |
| 2026-09-10 | E7.S1 **ATENDIDO** — inventário residual presentation (path/entity vs shape) |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E7.S2 (baseline presentation) |
| 2026-09-10 | E7.S2 **ATENDIDO** — baseline shape families + path rename unknown |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E7.S3 (shape defaults path principal) |
| 2026-09-10 | E7.S3 **ATENDIDO** — shape-only derive + unknown fallback + payload infer |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E7.S4 (path/entity cleanup) |
| 2026-09-10 | E7.S4 **ATENDIDO** — −29 pathRules + −23 table pathContains; orphans DELETE |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E7.S5 (labels/formats) |
| 2026-09-10 | E7.S5 **ATENDIDO** — formats schema-first no build; labels preservados |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E7.S6 (titles/framing) |
| 2026-09-10 | E7.S6 **ATENDIDO** — titles write-once + framing separado; F5 sem reinferência |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E7.S7 (MFE render-only) |
| 2026-09-10 | E7.S7 **ATENDIDO** — remove espelho product_operational_content do MFE |
| 2026-09-10 | Plano 07 **ATENDIDO** — Onda G segue no plano 08 (skills) |
| 2026-09-10 | E8.S1 **ATENDIDO** — inventário residual skills/help (freeze + classes) |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E8.S2 (skill catalog cleanup) |
| 2026-09-10 | E8.S2 **ATENDIDO** — hints path-like → capability keys neutras |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E8.S3 (help/capabilities) |
| 2026-09-10 | E8.S3 **ATENDIDO** — help availability actionId-first + path fallback |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E8.S4 (mixed bundles EAR) |
| 2026-09-10 | E8.S4 **ATENDIDO** — actionSelectionCopy; policy/PATH intactos |
| 2026-09-10 | Onda G **EM_ANDAMENTO** — próxima E8.S5 (audit gate) |
| 2026-09-10 | E8.S5 **ATENDIDO** — audit gate assistant technical duplication |
| 2026-09-10 | E8.S6 **ATENDIDO** — cleanup documental content README |
| 2026-09-10 | Plano 08 / Onda G **ATENDIDO** — próxima plano 09 / Onda H |
| 2026-09-10 | E9.S1 **ATENDIDO** — corpus R1–R11 v1 (20 classes) + manifesto imutável |
| 2026-09-10 | Onda H **EM_ANDAMENTO** — próxima E9.S2 (baseline R1–R11) |
| 2026-09-10 | E9.S2 **ATENDIDO_PARCIAL** — baseline offline 16 módulos / 99 passed no corpus v1 |
| 2026-09-10 | Onda H **EM_ANDAMENTO** — próxima E9.S3 (candidate por plano) |
| 2026-09-10 | E9.S3 **ATENDIDO** — candidate offline planos 01–08; globalPass=false (dims INCONCLUSIVE) |
| 2026-09-10 | Onda H **EM_ANDAMENTO** — próxima E9.S4 (shadow divergence) |
| 2026-09-10 | E9.S4 **ATENDIDO** — inventário 6 shadows críticos + gate owner/reasonFields (sem dual-run novo) |
| 2026-09-10 | Onda H **EM_ANDAMENTO** — próxima E9.S5 (canary/default cutover) |
| 2026-09-10 | E9.S5 **ATENDIDO** — inventário cutover/canary; cohort/agent ABSENT; dials globais + rollback |
| 2026-09-10 | Onda H **EM_ANDAMENTO** — próxima E9.S6 (cleanup gates) |
| 2026-09-10 | E9.S6 **ATENDIDO_PARCIAL** — 9 gates; deleteAuthorized=false; 4 candidates BLOCKED |
| 2026-09-10 | Onda H **EM_ANDAMENTO** — próxima E9.S7 (architecture audit) |
| 2026-09-10 | E9.S7 **ATENDIDO** — residuals classificados (REMOVE_WHEN_GATES_PASS / JUSTIFIED / REMOVED) |
| 2026-09-10 | Onda H **EM_ANDAMENTO** — próxima E9.S8 (verify-final) |
| 2026-09-10 | E9.S8 **ATENDIDO_PARCIAL** — matriz 10 objetivos; globalReleasePass=false (INCONCLUSIVE) |
| 2026-09-10 | Onda H **EM_ANDAMENTO** — próxima E9.S9 (documentação) |
| 2026-09-10 | E9.S9 **ATENDIDO_PARCIAL** — ponte docs canônicas; roadmap mantido; aceite final aberto |
| 2026-09-10 | Plano 09 / Onda H **ATENDIDO_PARCIAL** — próximo: live dims + DELETE gated + re-verify |
| 2026-09-10 | E9.S10 **ATENDIDO** — unknown/legacy/parity offline; latency INCONCLUSIVE; DELETE ainda bloqueado |
| 2026-09-10 | Onda H **ATENDIDO_PARCIAL** — próximo: live Ollama/gateway (latency/cost) → DELETE gated |
| 2026-09-10 | E9.S11 **ATENDIDO** — efficiency live Kimi p50/p95; provider=openai_compatible; sem Ollama |
| 2026-09-10 | Onda H **ATENDIDO_PARCIAL** — próximo: elevar dims PASS_OFFLINE→PASS ou autorizar DELETE com política explícita |
| 2026-09-10 | E9.S12.A **ATENDIDO** — DELETE `messageSegmentTerms`; authority permanente follow_up_type; playbookPathMarkers/registry ainda BLOCKED |
| 2026-09-10 | Onda H **ATENDIDO_PARCIAL** — próximo: E9.S12.B (`playbookPathMarkers`) |
| 2026-09-10 | E9.S12.B **ATENDIDO** — DELETE playbookPathMarkers + narrative path families; registry/strategy/TU STOP-THE-LINE |
| 2026-09-10 | Onda H **ATENDIDO_PARCIAL** — próximo: migrar resolve_route_action (E9.S12.C) antes de DELETE registry |
| 2026-09-10 | E9.S12.C **ATENDIDO** — DELETE path/op markers do registry; `operationIds` canônicos; routeSegment/strategy ainda residual |
| 2026-09-10 | Onda H **ATENDIDO_PARCIAL** — próximo: E9.S12.E (`parameters.strategy`) ou E9.S12.D (`routeSegment`) |
| 2026-09-10 | E9.S12.E **ATENDIDO** — DELETE parameters.strategy / domain parameterStrategy; inferência OpenAPI |
| 2026-09-10 | Onda H **ATENDIDO_PARCIAL** — próximo: E9.S12.D (`routeSegment`) ou cutover TU |
| 2026-09-10 | E9.S12.D **ATENDIDO** — DELETE registry `routeSegment`; `RouteSegmentInferenceService`; follow-up JSON KEEP |
| 2026-09-10 | Onda H **ATENDIDO_PARCIAL** — próximo: cutover TU (plano-02) |
| 2026-09-10 | E2.S4 **CUTOVER_PARTIAL** — dial productFamilyAuthorityShadow (OFF) + mapper TU→product intent |
| 2026-09-10 | Onda C/H **ATENDIDO_PARCIAL** — próximo: canary `cutoverEnabled=true` product OU production/KPI |
| 2026-09-10 | E2.S4 **CUTOVER_PRODUCT_CANARY** — cutoverEnabled=true + grounding anti-RAG; agree 10/10 E2.S2 |
| 2026-09-10 | Onda C/H **ATENDIDO_PARCIAL** — próximo: production/KPI dials OU E2.S5 |
| 2026-09-10 | E2.S4 **PRODUCTION_KPI_SHADOW_READY** — mappers+wire OFF; terms normalizados no match production |
| 2026-09-10 | Onda C/H **ATENDIDO_PARCIAL** — próximo: canary production/KPI OU E2.S5 |
| 2026-09-10 | E2.S4 **CUTOVER_ALL_FAMILIES_CANARY** — product mapper-first; production/KPI agree-gated ON |
| 2026-09-10 | Onda C/H **ATENDIDO_PARCIAL** — próximo: E2.S5 intent_router/analysis OU mapper-first prod/KPI |
| 2026-09-10 | E2.S4 **MAPPER_FIRST_ALL_FAMILIES** — production/KPI mapper-first + cobertura |
| 2026-09-10 | E2.S5 **CUTOVER_GENERIC_SLICE** — no_tool/presentation/compare overlay |
| 2026-09-10 | E2.S6 **ATENDIDO_PARCIAL** — harness dependsOn; taskPlanner live BLOCKED |
| 2026-09-10 | E2.S7 **JUSTIFIED_KEEP** — major heuristics KEEP; DELETE BLOCKED |
| 2026-09-10 | Onda C **ATENDIDO_PARCIAL** — plano-02 executável fechado com resíduos documentados |
| 2026-09-10 | E2.S5 **CUTOVER_FULL_SLICE** — analysis `is_*` multi-consumer + dial data_interpretation |
| 2026-09-10 | E2.S6 **ATENDIDO** — taskPlannerEnabled=true (fast ainda disabled) |
| 2026-09-10 | E2.S7 **KEEP_APPROVED** — fast paths JUSTIFIED (TARGET); sem DELETE indevido |
| 2026-09-10 | Onda C / plano-02 **ATENDIDO 100%** — aceite offline + verify-final |
| 2026-09-10 | **LIVE** plano-02 cutover **PASS 4/4** (`e2-plano02-cutover-live.md`; Keycloak religado) |
| 2026-09-10 | E9.S13 **ATENDIDO_PARCIAL** — C5 L1–L4 PASS → `multi_turn=PASS_OFFLINE_AND_LIVE`; C4 structure FAIL; deleteAuthorized=false |
| 2026-09-11 | E9.S13 **C4 PASS** — scoped fan-out select + follow-up multi-scope; `compound=PASS_OFFLINE_AND_LIVE`; deleteAuthorized=false |
| 2026-09-11 | E9.S14 **ATENDIDO** — live remaining gates 6/6 PASS; word-boundary candidateDiscovery (`ov`≠provider); `deleteAuthorized=true` |
| 2026-09-11 | E9.S8 **REVALIDADO** — matriz alinhada S13/S14; aggregate `PASS_OFFLINE_AND_LIVE_PARTIAL`; `globalReleasePass=false` (recommendations + parity) |
| 2026-09-11 | Onda H **ATENDIDO_PARCIAL** — próximo: live recommendations/parity **ou** APPROVED → globalReleasePass + E9.S9 |
| 2026-09-11 | E9.S15 **ATENDIDO** — recommendations grounded + send/stream/simulate parity live 3/3 (`e9-s15-release-blockers-live`) |
| 2026-09-11 | E9.S8 **ATENDIDO** — `globalReleasePass=true`; aggregate `PASS_OFFLINE_AND_LIVE`; blockingCells=[] |
| 2026-09-11 | E9.S9 **ATENDIDO** — aceite final Onda H documentado |
| 2026-09-11 | Plano 09 / Onda H **ATENDIDO** — release gates plenos; débitos F5 browser / tokens metadata não-bloqueantes |
| 2026-09-11 | E3.S8 **ATENDIDO** — Postgres overlay `working/lastAction` + merge history-wins; sanitize bounded |
| 2026-09-11 | Onda B **ATENDIDO** — E1.S6 fechado (DELETE registry E9.S12.*) |
| 2026-09-11 | Onda D **ATENDIDO** — plano 03 S1–S8 completo |
| 2026-09-11 | Programa llm-json-decoupling **ondas A–H ATENDIDAS** |
| 2026-09-11 | E9.S16 **ATENDIDO** — F5/session reload API (GET messages + same-product follow-up) |
| 2026-09-11 | E9.S11 **tokens PASS** — extractor lê *TokensEstimated + aliases adminDebug |
| 2026-09-11 | Changelog `2026-09-llm-json-decoupling.md` + pasta **ARQUIVADO** (A–H) |
| 2026-09-11 | **POLICY** zero mapa lateral — JUSTIFIED_POLICY revogada para pathMarkers laterais |
| 2026-09-11 | Onda I / plano 10 **EM_ANDAMENTO** — E10.S1 inventário + contrato sem pathMarkers |
| 2026-09-11 | E10.S1–S5 **ATENDIDO** — zero keys laterais; `ApiRouteDomainInferenceService`; stamp import |
| 2026-09-11 | Onda I **ATENDIDO** — gate `test_e10_zero_lateral_path_maps` PASS |
| 2026-09-11 | E10 **live PASS** — `smoke_e10_zero_lateral_path_maps_live.py` (product + KPI sibling + negative) |

## Reabertura corretiva — Onda J

| Data | Evento |
|------|--------|
| 2026-09-11 | Auditoria pós A–I: `VERIFY_FINAL_FAILED`; encontrados substitutos semânticos JSON→Python/strategy/routeSegment/registry + stale candidate evidence |
| 2026-09-11 | Regras `.cursor` endurecidas: `COMPLETE_GATE`, semantic residual search, candidate freshness e unknown API real |
| 2026-09-11 | Plano 11 criado; próxima subetapa obrigatória = **E11.S0 rebaseline/inventário/freeze** |
| 2026-09-11 | **E11.S0 ATENDIDO** — BASE `8bc84fc6…`; inventário D11-01..10; freeze corpus; métricas em `e11-s0-debt-metrics.json`; próxima = **E11.S1** |
| 2026-09-11 | **E11.S1 ATENDIDO** — Phase3 `--check-semantic-debt` vermelho (274); RQ11-10; próxima = **E11.S2** |
| 2026-09-11 | **E11.S2 ATENDIDO** — apiRouteDomain sem path authority; `SEMANTIC_PATH_DOMAIN_MAP=0`; próxima = **E11.S3** |
