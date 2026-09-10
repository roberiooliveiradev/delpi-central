# Ledger de execução — llm-json-decoupling

**Fonte:** markdowns desta pasta (não `.cursor/plans`).  
**Atualizado:** 2026-09-10  
**Baseline freeze:** [`onda-a-baseline/manifest.json`](./onda-a-baseline/manifest.json) (`runId=0249db78-d6fd-45b3-84bf-d11abcd17a6a`)

## Ondas

| Onda | Planos | Status | Próxima subetapa | Notas |
|------|--------|--------|------------------|-------|
| A — baseline/contratos | inventário + freeze | **ATENDIDO** | — | Ver `onda-a-inventory.md` |
| B — routing universal | 01 | **ATENDIDO_PARCIAL** | Onda H: DELETE fields registry | Cutover seleção + binder OK; JSON markers deferred |
| C — entendimento | 02 | **ATENDIDO_PARCIAL** | E2.S4 cutover (após agree) → S5–S7 | S1–S3 OK; S4 shadow-only; DELETE heuristics deferred |
| D — multi-turn/args | 03 | **ATENDIDO_PARCIAL** | Onda H: DELETE terms | S1–S7 OK; S8 reload OK; DELETE deferred |
| E — caps/composition | 04, 05 | **ATENDIDO** | — | plano 04+05 S1–S7 OK |
| F — UX inteligente | 06 | **ATENDIDO** | — | E6.S1–S6 OK; queries = LEGACY_FALLBACK |
| G — presentation/skills | 07, 08 | **ATENDIDO** | — | Planos 07+08 S1–S* OK |
| H — cutover/cleanup | 09 | **ATENDIDO_PARCIAL** | promover dims PASS_OFFLINE→PASS / DELETE | S1–S11; efficiency live OK; DELETE ainda bloqueado |

## Protocolo por subetapa

```text
abrir planos/0N-*.md
→ revalidar HEAD vs EXECUTION_DRIFT
→ READY_TO_EXECUTE?
→ implementar menor escopo
→ testes positive/sibling/negative
→ atualizar STATUS neste ledger + no plano
→ só então avançar dependente
```

## Proibições

- Não criar `.plan.md` paralelo para este programa.
- Não DELETE de registry/intents/queries sem evidência candidate ≥ baseline + unknown API + metamorphic.
- Não reintroduzir `pathRules` / `capabilityGroup` por endpoint.
- Drift material → `EXECUTION_DRIFT` no markdown do plano afetado + STOP-THE-LINE no subgrafo.

## Registro de progresso

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
| 2026-09-10 | E3.S7 **ATENDIDO** — cutover follow-up_type→routeSegment (terms observer) |
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
