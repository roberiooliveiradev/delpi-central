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
| E — caps/composition | 04, 05 | **EM_ANDAMENTO** | E5.S4 planner-driven enrichment | plano 04 ATENDIDO; 05 S1–S3 OK |
| F — UX inteligente | 06 | **PRONTO_APÓS_E** | E6.S1 | recommendationQueries ainda authority |
| G — presentation/skills | 07, 08 | **PRONTO_APÓS_F** | inventário residual | Display path→label já limpo |
| H — cutover/cleanup | 09 | **CONTÍNUO** | E9.S1 corpus ampliado | Não remover legado sem gates |

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
| 2026-09-10 | Onda E **EM_ANDAMENTO** — próxima E5.S4 |
