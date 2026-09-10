# Desacoplamento de JSONs + inteligência LLM — Minha DELPI AI

**Status:** Onda A–G ATENDIDAS · Onda H **ATENDIDO_PARCIAL** (E9.S12.A–E DELETE; E2.S4 product dial OFF) · via [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)  
**Escopo:** `minha-delpi-ai-api/app/content` + consumidores runtime relacionados  
**Objetivo:** remover acoplamentos técnicos e linguísticos que impedem o chat de generalizar para novas APIs, novos domínios e formulações de linguagem natural sem manutenção rota a rota.

> Este diretório é roadmap executável. **Não criar planos `.plan.md` paralelos** para o mesmo programa: atualizar estes markdowns quando houver drift. Antes de implementar qualquer subetapa, revalidar código, contratos, regras `.cursor` e documentação vigente.

## Princípio da iniciativa

Não aplicar a simplificação `JSON -> LLM` indiscriminadamente.

```text
catálogo técnico duplicado
-> OpenAPI + Action Catalog

NLU/semântica hardcoded
-> Turn Understanding + retrieval + planner LLM estruturado

policy / business rule / safety
-> determinístico

copy / UX / prompt
-> conteúdo configurável
```

O LLM interpreta intenção e contexto. O OpenAPI define contrato. O validator valida argumentos. RBAC/policy decide autorização. O executor usa somente actions persistidas e permitidas.

## Documentos

| Documento | Finalidade |
|---|---|
| [`prompt-cursor-plano-mestre.md`](./prompt-cursor-plano-mestre.md) | Prompt para o Cursor revalidar HEAD e **atualizar estes markdowns** antes de implementar. |
| [`roadmap.md`](./roadmap.md) | Roadmap macro, dependências, critérios globais, ordem das ondas e Definition of Done. |
| [`planos/01-routing-registry-openapi.md`](./planos/01-routing-registry-openapi.md) | Remover autoridade **residual** do registry/`api_route_domains` (cold path já OpenAPI-first). |
| [`planos/02-semantic-understanding-intents.md`](./planos/02-semantic-understanding-intents.md) | Substituir NLU manual por Turn Understanding estruturado (hoje shadow). |
| [`planos/03-follow-up-refinement-argument-binding.md`](./planos/03-follow-up-refinement-argument-binding.md) | Generalizar follow-up/refinement/args via contexto + schema. |
| [`planos/04-capabilities-action-catalog.md`](./planos/04-capabilities-action-catalog.md) | Mini-catálogo `action.*` → Action Catalog; **pathRules já removido (D1)**. |
| [`planos/05-composition-enrichment-planning.md`](./planos/05-composition-enrichment-planning.md) | Composition/enrichment planner-driven. |
| [`planos/06-recommendations-composer-contextual.md`](./planos/06-recommendations-composer-contextual.md) | Recommendations/composer contextuais — **ATENDIDO** (queries = LEGACY_FALLBACK). |
| [`planos/07-presentation-schema-first-residuals.md`](./planos/07-presentation-schema-first-residuals.md) | Residuais de apresentação path/entity. |
| [`planos/08-skills-content-residual-catalogs.md`](./planos/08-skills-content-residual-catalogs.md) | Skills/help residual — **ATENDIDO** (hints neutros + help actionId + EAR copy + audit). |
| [`planos/09-evals-rollout-cleanup.md`](./planos/09-evals-rollout-cleanup.md) | Baseline, shadow/canary, R1-R11, cleanup. |
| [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) | Estado das ondas A–H e próxima subetapa. |
| [`evidence/onda-a-inventory.md`](./evidence/onda-a-inventory.md) | Inventário Onda A (consumers + classificação). |
| [`evidence/e1-s4-registry-selection-shadow.md`](./evidence/e1-s4-registry-selection-shadow.md) | E1.S4 — SHADOW_ON + agree aggregation admin. |
| [`evidence/e1-s4-agree-aggregation.md`](./evidence/e1-s4-agree-aggregation.md) | E1.S4 — admin summary `agreeRate` (sem cutover). |
| [`evidence/e1-s5-parameter-strategy-shadow.md`](./evidence/e1-s5-parameter-strategy-shadow.md) | E1.S5 — **ATENDIDO** (cutover completo da fila do resolver). |
| [`evidence/e1-s6-cleanup-partial.md`](./evidence/e1-s6-cleanup-partial.md) | E1.S6A — binder permanente / switch removido. |
| [`evidence/e1-s6b-selection-cutover.md`](./evidence/e1-s6b-selection-cutover.md) | E1.S6B — **ATENDIDO** cutover seleção OpenAPI-first. |
| [`evidence/e2-s1-heuristic-intent-inventory.md`](./evidence/e2-s1-heuristic-intent-inventory.md) | E2.S1 — inventário árvores heurísticas (Onda C). |
| [`evidence/e2-s2-understanding-baseline.md`](./evidence/e2-s2-understanding-baseline.md) | E2.S2 — baseline authority vs shadow TU. |
| [`evidence/e2-s3-turn-understanding-contract.md`](./evidence/e2-s3-turn-understanding-contract.md) | E2.S3 — contrato canônico TU. |
| [`evidence/e2-s4-authority-shadow.md`](./evidence/e2-s4-authority-shadow.md) | E2.S4 — SHADOW_ON authority vs TU. |
| [`evidence/e3-s1-multi-turn-state-inventory.md`](./evidence/e3-s1-multi-turn-state-inventory.md) | E3.S1 — inventário grafo multi-turn (Onda D). |
| [`evidence/e3-s2-follow-up-baseline.md`](./evidence/e3-s2-follow-up-baseline.md) | E3.S2 — baseline follow-up/refinement. |
| [`evidence/e3-s3-turn-refinement-contract.md`](./evidence/e3-s3-turn-refinement-contract.md) | E3.S3 — contrato canônico Turn Refinement. |
| [`evidence/e3-s4-schema-driven-argument-binder.md`](./evidence/e3-s4-schema-driven-argument-binder.md) | E3.S4 — binder OpenAPI sobre TurnRefinement. |
| [`evidence/e3-s5-schema-driven-group-by.md`](./evidence/e3-s5-schema-driven-group-by.md) | E3.S5 — group-by por schema/actionId. |
| [`evidence/e3-s6-pagination-filter-fast-path.md`](./evidence/e3-s6-pagination-filter-fast-path.md) | E3.S6 — pagination/filter schema-bound. |
| [`evidence/e3-s7-follow-up-routing-cutover.md`](./evidence/e3-s7-follow-up-routing-cutover.md) | E3.S7 — cutover follow-up routing. |
| [`evidence/e3-s8-persist-reload-cleanup.md`](./evidence/e3-s8-persist-reload-cleanup.md) | E3.S8 — persist/reload (DELETE deferred). |
| [`evidence/e4-s1-capability-inventory.md`](./evidence/e4-s1-capability-inventory.md) | E4.S1 — inventário capabilities/registry. |
| [`evidence/e4-s2-capability-discovery-baseline.md`](./evidence/e4-s2-capability-discovery-baseline.md) | E4.S2 — baseline discovery. |
| [`evidence/e4-s3-ux-capability-contract.md`](./evidence/e4-s3-ux-capability-contract.md) | E4.S3 — contrato uxCapability. |
| [`evidence/e4-s4-dynamic-capability-view.md`](./evidence/e4-s4-dynamic-capability-view.md) | E4.S4 — help dinâmico Action Catalog. |
| [`evidence/e4-s5-remove-action-mini-catalog.md`](./evidence/e4-s5-remove-action-mini-catalog.md) | E4.S5 — remove action.* do registry. |
| [`evidence/e5-s1-composition-inventory.md`](./evidence/e5-s1-composition-inventory.md) | E5.S1 — inventário decisões de composição. |
| [`evidence/e5-s2-composition-baseline.md`](./evidence/e5-s2-composition-baseline.md) | E5.S2 — baseline composition/enrichment. |
| [`evidence/e5-s3-goal-coverage-contract.md`](./evidence/e5-s3-goal-coverage-contract.md) | E5.S3 — contrato Goal Coverage. |
| [`evidence/e5-s4-planner-driven-enrichment.md`](./evidence/e5-s4-planner-driven-enrichment.md) | E5.S4 — enrichment via coverage gaps. |
| [`evidence/e5-s5-department-composition-cutover.md`](./evidence/e5-s5-department-composition-cutover.md) | E5.S5 — department goals+retrieval. |
| [`evidence/e5-s6-entity-enrichment-cutover.md`](./evidence/e5-s6-entity-enrichment-cutover.md) | E5.S6 — entity enrichment goals. |
| [`evidence/e5-s7-composition-cleanup.md`](./evidence/e5-s7-composition-cleanup.md) | E5.S7 — DELETE maps mortos composition. |

## Drift HEAD (2026-09-10) — resumido

| Tema | Estado |
|------|--------|
| OpenAPI-first cold path | Já default — plano 01 = residual |
| `capabilities.pathRules` | Removido — plano 04 R04-02 ATENDIDO |
| `recommendationQueries` | LEGACY_FALLBACK (E6.S4) — dual-run `recommendationDualRun` |
| Turn Understanding | Bundle + shadow on — plano 02 |

## Fontes obrigatórias antes de executar

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc`
3. `.cursor/rules/evidence-driven-execution.mdc`
4. `.cursor/rules/plan-construction.mdc`
5. `.cursor/rules/plan-execution.mdc`
6. `.cursor/rules/openapi-first-universal-tool-routing.mdc`
7. `.cursor/rules/assistant-content-json.mdc`
8. `.cursor/rules/ai-intelligence-evaluation.mdc`
9. `minha-delpi-ai-api/docs/api/04-actions-openapi.md`
10. `minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md`
11. `minha-delpi-ai-api/docs/roadmap/openapi-first-universal-tool-routing.md`

## Invariantes

- Nenhum novo `if path/provider/operationId` no core genérico.
- Nenhum novo catálogo paralelo de endpoints em JSON.
- LLM nunca escolhe URL arbitrária nem action fora das candidates autorizadas.
- `required`, `type`, `enum`, `format`, body/query/path continuam validados deterministicamente.
- RBAC, sensitivity e confirmation permanecem fora da decisão livre do modelo.
- Regras factuais e de negócio não migram para LLM só para reduzir JSON.
- Fast paths pequenos podem permanecer quando comprovadamente seguros e úteis para latência.
- Nova API OpenAPI desconhecida deve funcionar sem alterações por endpoint no core.
- Mudanças de inteligência exigem baseline vs candidate + R1–R11 + live/surface validation.

## Regra de execução

Cada plano filho (`planos/0N-*.md`) é a **unidade de execução**. Se o código atual contradizer uma decisão, registrar `EXECUTION_DRIFT` **no próprio markdown**, atualizar CURRENT/etapas e só então prosseguir. Não manter segundo plano Cursor como fonte.
