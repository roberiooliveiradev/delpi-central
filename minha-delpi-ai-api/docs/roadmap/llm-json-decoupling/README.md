# Desacoplamento de JSONs + inteligência LLM — Minha DELPI AI

**Status:** planejamento ativo  
**Escopo:** `minha-delpi-ai-api/app/content` + consumidores runtime relacionados  
**Objetivo:** remover acoplamentos técnicos e linguísticos que impedem o chat de generalizar para novas APIs, novos domínios e formulações de linguagem natural sem manutenção rota a rota.

> Este diretório é roadmap executável, não fonte canônica de arquitetura. Antes de implementar qualquer subetapa, revalidar código, contratos, regras `.cursor` e documentação vigente.

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
| [`prompt-cursor-plano-mestre.md`](./prompt-cursor-plano-mestre.md) | Prompt pronto para o Cursor investigar o estado atual e construir/atualizar o plano completo antes de implementar. |
| [`roadmap.md`](./roadmap.md) | Roadmap macro, dependências, critérios globais, ordem das ondas e Definition of Done. |
| [`planos/01-routing-registry-openapi.md`](./planos/01-routing-registry-openapi.md) | Remover autoridade runtime de `operational_route_registry`/`api_route_domains` sobre seleção técnica. |
| [`planos/02-semantic-understanding-intents.md`](./planos/02-semantic-understanding-intents.md) | Substituir NLU manual de produto, produção, KPI e intents genéricas por entendimento estruturado. |
| [`planos/03-follow-up-refinement-argument-binding.md`](./planos/03-follow-up-refinement-argument-binding.md) | Generalizar follow-up, refinamento, group-by e binding de parâmetros via contexto + schema. |
| [`planos/04-capabilities-action-catalog.md`](./planos/04-capabilities-action-catalog.md) | Eliminar mini-catálogo manual de actions/capabilities e classificar semanticamente no Action Catalog. |
| [`planos/05-composition-enrichment-planning.md`](./planos/05-composition-enrichment-planning.md) | Tornar composição departamental e enriquecimentos entity-driven planner-driven. |
| [`planos/06-recommendations-composer-contextual.md`](./planos/06-recommendations-composer-contextual.md) | Recomendações e sugestões do composer baseadas no contexto e nas actions permitidas. |
| [`planos/07-presentation-schema-first-residuals.md`](./planos/07-presentation-schema-first-residuals.md) | Remover acoplamentos residuais de apresentação por path/entity quando schema/metadata bastam. |
| [`planos/08-skills-content-residual-catalogs.md`](./planos/08-skills-content-residual-catalogs.md) | Limpar hints técnicos em skills/help/content sem mover copy legítima para o LLM. |
| [`planos/09-evals-rollout-cleanup.md`](./planos/09-evals-rollout-cleanup.md) | Baseline, shadow/canary, R1-R11, unknown API, metamorphic tests, rollout e remoção final. |

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
- Mudanças de inteligência exigem baseline vs candidate + R1-R11 + live/surface validation.

## Regra de execução

Cada plano filho deve ser revalidado antes de executar. Se o código atual contradizer uma decisão deste roadmap, registrar `EXECUTION_DRIFT`, atualizar o plano com evidência e só então prosseguir.
