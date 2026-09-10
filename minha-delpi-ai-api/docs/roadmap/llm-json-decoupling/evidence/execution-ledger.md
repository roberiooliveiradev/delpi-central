# Ledger de execução — llm-json-decoupling

**Fonte:** markdowns desta pasta (não `.cursor/plans`).  
**Atualizado:** 2026-09-10  
**Baseline freeze:** [`onda-a-baseline/manifest.json`](./onda-a-baseline/manifest.json) (`runId=0249db78-d6fd-45b3-84bf-d11abcd17a6a`)

## Ondas

| Onda | Planos | Status | Próxima subetapa | Notas |
|------|--------|--------|------------------|-------|
| A — baseline/contratos | inventário + freeze | **ATENDIDO** | — | Ver `onda-a-inventory.md` |
| B — routing universal | 01 | **EM_ANDAMENTO** | E1.S6 prep / expandir cutover strategies | E1.S5 CUTOVER_PARTIAL none/semantic/sale_orders |
| C — entendimento | 02 | **BLOQUEADO_POR_B** (soft) | E2 inventário+baseline TU | Pode shadow em paralelo após B começar |
| D — multi-turn/args | 03 | **BLOQUEADO_POR_B** | inventário follow-up | Depende de actionId estável |
| E — caps/composition | 04, 05 | **PARCIAL** | 04: `action.*`; 05: routeIds | pathRules já DONE |
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
