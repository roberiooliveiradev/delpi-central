# Desacoplamento de JSONs + inteligência LLM — Minha DELPI AI

**Status:** Onda A ATENDIDA · ondas B–H via [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)  
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
| [`planos/06-recommendations-composer-contextual.md`](./planos/06-recommendations-composer-contextual.md) | Recommendations/composer contextuais; D2 ≠ aceite (queries ainda authority). |
| [`planos/07-presentation-schema-first-residuals.md`](./planos/07-presentation-schema-first-residuals.md) | Residuais de apresentação path/entity. |
| [`planos/08-skills-content-residual-catalogs.md`](./planos/08-skills-content-residual-catalogs.md) | Hints técnicos em skills/help. |
| [`planos/09-evals-rollout-cleanup.md`](./planos/09-evals-rollout-cleanup.md) | Baseline, shadow/canary, R1-R11, cleanup. |
| [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) | Estado das ondas A–H e próxima subetapa. |
| [`evidence/onda-a-inventory.md`](./evidence/onda-a-inventory.md) | Inventário Onda A (consumers + classificação). |
| [`evidence/e1-s3-action-catalog.md`](./evidence/e1-s3-action-catalog.md) | Prova E1.S3 (Onda B) — **PASS**. |
| [`evidence/e1-s5-parameter-strategy-shadow.md`](./evidence/e1-s5-parameter-strategy-shadow.md) | Shadow E1.S5 — strategies none/semantic/sale_orders. |

## Drift HEAD (2026-09-10) — resumido

| Tema | Estado |
|------|--------|
| OpenAPI-first cold path | Já default — plano 01 = residual |
| `capabilities.pathRules` | Removido — plano 04 R04-02 ATENDIDO |
| `recommendationQueries` | Ainda authority estática — plano 06 aberto |
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
