# Desacoplamento de JSONs + inteligência LLM/OpenAPI — Minha DELPI AI

**Status atual:** **REABERTO — Onda J em execução planejada**  
**Plano ativo:** [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)  
**Escopo:** `minha-delpi-ai-api` + consumers relacionados do chat/MFE  
**Objetivo:** remover acoplamentos técnicos/linguísticos que impedem generalização para novas APIs, domínios e formulações sem manutenção rota a rota.

> As Ondas A–I produziram avanços e evidências históricas, mas uma auditoria posterior encontrou drifts materiais. Portanto, seus `PASS` não constituem aceite do **candidate final atual**. O programa só volta a ser arquivado após a Onda J passar `COMPLETE_GATE` + `VERIFY_FINAL` no HEAD final.

## Princípio da iniciativa

```text
catálogo técnico duplicado
→ OpenAPI + Action Catalog

NLU/semântica endpoint-specific
→ semantic understanding + retrieval + structured planner

argument binding
→ semantic delta + OpenAPI schema + validator

multi-turn
→ structured conversation state

policy / business rule / safety
→ determinístico

copy / UX / prompt
→ conteúdo configurável

presentation
→ responseSchema + payload + semantic metadata

contextual prose/recommendations
→ grounded synthesis, preferencialmente reutilizando LLM do turno
```

Não aplicar `JSON → LLM` indiscriminadamente. E, principalmente, **não aplicar `JSON → Python hardcode` para fazer cleanup parecer concluído**.

## Invariante reforçada — zero catálogo técnico paralelo

```text
NENHUM MAPA LATERAL OU SUBSTITUTO SEMÂNTICO DEVE SER AUTHORITY.
```

Isto inclui, em JSON **ou código**:

- path→domain maps;
- path/operationId→parameter strategy;
- path/operationId→route segment;
- route semantic→lista manual de operationIds para routing;
- selector por API/endpoint;
- presenter obrigatório por endpoint;
- taxonomia proprietária obrigatória para provider externo funcionar.

`path`, `method` e `operationId` continuam válidos como metadata técnica do Action Catalog para executar/observar a action. A proibição é usá-los como heurística hardcoded de semântica no core genérico.

## Documentos canônicos desta iniciativa

| Documento | Finalidade |
|---|---|
| [`prompt-cursor-plano-mestre.md`](./prompt-cursor-plano-mestre.md) | Rebaseline/revisão do plano em Plan mode. |
| [`prompt-cursor-execucao-corretiva.md`](./prompt-cursor-execucao-corretiva.md) | **Prompt de execução** da Onda J, uma subetapa por vez, sem pular gates. |
| [`roadmap.md`](./roadmap.md) | Estado macro, decisões e Definition of Done global. |
| [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md) | **Plano ativo** de correção arquitetural e verify-final. |
| [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) | Histórico de execução/evidências; deve ser atualizado durante a Onda J. |
| [`ARCHIVED.md`](./ARCHIVED.md) | Histórico das Ondas A–I; não representa o aceite vigente. |

## Planos históricos

| Plano | Tema | Relação com a Onda J |
|---|---|---|
| [`01-routing-registry-openapi.md`](./planos/01-routing-registry-openapi.md) | routing registry/OpenAPI | revisar residual registry/operationIds |
| [`02-semantic-understanding-intents.md`](./planos/02-semantic-understanding-intents.md) | semantic understanding/intents | consolidar authority e limpar NLU endpoint-specific |
| [`03-follow-up-refinement-argument-binding.md`](./planos/03-follow-up-refinement-argument-binding.md) | follow-up/refinement/args | retirar path-derived continuity/strategy |
| [`04-capabilities-action-catalog.md`](./planos/04-capabilities-action-catalog.md) | capabilities | corrigir metadata de efeito/risco |
| [`05-composition-enrichment-planning.md`](./planos/05-composition-enrichment-planning.md) | composition/enrichment | validar generalização no candidate final |
| [`06-recommendations-composer-contextual.md`](./planos/06-recommendations-composer-contextual.md) | recommendations | concluir cutover contextual e exit de fallback |
| [`07-presentation-schema-first-residuals.md`](./planos/07-presentation-schema-first-residuals.md) | presentation | revalidar fallback universal |
| [`08-skills-content-residual-catalogs.md`](./planos/08-skills-content-residual-catalogs.md) | skills/help/content | revalidar residual técnico |
| [`09-evals-rollout-cleanup.md`](./planos/09-evals-rollout-cleanup.md) | evals/release | evidência histórica; candidate final precisa rerun fresco |
| [`10-zero-lateral-path-maps.md`](./planos/10-zero-lateral-path-maps.md) | zero mapa lateral | reaberto por substitutos semânticos encontrados |

## Drifts que motivaram a Onda J

A auditoria pós-implementação encontrou:

1. `ApiRouteDomainInferenceService._DOMAIN_RULES` portando path maps do JSON para Python;
2. `ParameterStrategyInferenceService` inferindo strategy por path/operationId após DELETE do catálogo;
3. continuidade/`routeSegment` derivada de path-tail/operationId inventory;
4. `route.operationIds` como catálogo técnico paralelo residual;
5. ownership semântico duplicado entre heurísticas/mappers e LLM Turn Analysis;
6. `recommendationQueries` ainda como fallback e parte de oracle de smoke;
7. capability metadata fixa `read/low/parallelSafe` para actions heterogêneas;
8. boundary/DI residual;
9. credential defaults em smoke;
10. unknown-provider histórico reutilizado depois de mudança material.

O detalhamento e os critérios de correção estão no Plano 11.

## Regras obrigatórias antes de executar

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc`
3. `.cursor/rules/evidence-driven-execution.mdc`
4. `.cursor/rules/plan-construction.mdc`
5. `.cursor/rules/plan-execution.mdc`
6. `.cursor/rules/test-and-commit.mdc`
7. `.cursor/rules/openapi-first-universal-tool-routing.mdc`
8. `.cursor/rules/operational-api-routing.mdc`
9. `.cursor/rules/assistant-content-json.mdc`
10. `.cursor/rules/ai-intelligence-evaluation.mdc`
11. `.cursor/rules/clean-architecture-chat-api.mdc`
12. `minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md`

## Ordem de execução da Onda J

```text
E11.S0  rebaseline/inventário
E11.S1  architecture enforcement semântico
E11.S2  apiRouteDomain sem path authority
E11.S3  argument binding schema-driven
E11.S4  multi-turn sem path/operationId continuity
E11.S5  registry/operationIds sem routing authority
E11.S6  semantic authority única + cleanup NLU manual
E11.S7  recommendations contextuais + capability metadata
E11.S8  Clean Architecture + segurança de scripts
E11.S9  candidate final + unknown/metamorphic + R1–R11
E11.S10 residual scan + docs + verify-final
```

Em workstream de substituição:

```text
CUTOVER
→ GENERALIZATION
→ CLEANUP
→ VERIFY
→ COMPLETE_GATE
```

## O que não conta como concluído

Se fizer parte do objetivo material, qualquer um destes estados mantém a iniciativa aberta:

```text
PARTIAL
ATENDIDO_PARCIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
DEFERRED
TODO/FIXME/HACK/TEMPORARY
flag/fallback sem exit criteria
```

Não é permitido escrever “100% concluído” deixando “próximo passo”, “depois remover”, “falta unknown”, “falta live”, “fallback ainda necessário” ou equivalente.

## Definition of Done global

A iniciativa só pode voltar a `CONCLUÍDA/ARCHIVED` quando, no mesmo candidate final:

```text
CUTOVER_RESULT = PASS
GENERALIZATION_RESULT = PASS
CLEANUP_RESULT = PASS
UNKNOWN_EXTERNAL_API = PASS
METAMORPHIC_PROVIDER_PATH_OPERATION_RENAME = PASS
ARGUMENT_SCHEMA_AUTHORITY = PASS
MULTI_TURN_STRUCTURED_STATE = PASS
SEMANTIC_AUTHORITY_SINGLE_OWNER = PASS
CONTEXTUAL_RECOMMENDATIONS = PASS
CAPABILITY_SECURITY_METADATA = PASS
CLEAN_ARCHITECTURE = PASS
SECURITY_HYGIENE = PASS
SEND_STREAM_SIMULATE_UI = PASS
PERSIST_RELOAD_F5 = PASS
R1_R11_REQUIRED_DIMENSIONS = PASS
RESIDUAL_SCAN = PASS
DOCS_MATCH_FINAL_HEAD = PASS
COMPLETE_GATE = PASS
VERIFY_FINAL = PASS
```

Se qualquer item obrigatório estiver `FAIL`, `INCONCLUSIVE`, `PARTIAL` ou depender de evidência anterior ao último diff material, o status permanece **REABERTO / VERIFY_FINAL_FAILED**.
