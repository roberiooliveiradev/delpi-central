# Prompt para Cursor — rebaseline e planejamento mestre do desacoplamento LLM/OpenAPI

Este prompt é usado em **Plan mode** para revalidar arquitetura, requisitos e etapas. Para implementar a Onda corretiva ativa, use [`prompt-cursor-execucao-corretiva.md`](./prompt-cursor-execucao-corretiva.md).

> **Estado atual:** o programa foi reaberto após auditoria arquitetural pós Ondas A–I. O plano ativo é [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md). PASSs históricos não constituem aceite do candidate final.

---

## Prompt

Você está trabalhando no monorepo `delpi-central`, com foco em `minha-delpi-ai-api`.

Sua tarefa neste modo é **revalidar o estado atual e manter o roadmap executável correto**. Não implemente runtime neste prompt; a execução possui prompt separado.

## 1. Fontes obrigatórias

Leia na ordem:

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
12. `.cursor/rules/ai-external-tools-security.mdc`
13. `.cursor/rules/llm-stack-centralized.mdc`
14. `minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md`
15. `minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/README.md`
16. `minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/roadmap.md`
17. todos os planos 01–11 relevantes ao drift.

## 2. Situação que deve ser revalidada, não assumida

A auditoria anterior encontrou, entre outros:

- mapa path→domain recriado em Python após remoção do JSON;
- `parameterStrategy` removida do JSON e reintroduzida por path/operationId;
- continuidade multi-turn derivada de path-tail/operationId inventory;
- `route.operationIds` como catálogo técnico paralelo residual;
- ownership semântico duplicado entre heurísticas/mappers e LLM Turn Analysis;
- recommendation estática ainda participando de fallback/oracle;
- capability metadata uniformemente `read/low/parallelSafe`;
- boundary/DI residual;
- credential defaults em smoke;
- unknown-provider antigo reutilizado depois de mudanças materiais.

Esses itens são hipóteses confirmadas no audit-base do Plano 11, mas **releia o HEAD atual antes de planejar**. Se algum já mudou, registre o drift e atualize o plano.

## 3. Regra fundamental de arquitetura

O target é:

```text
USER MESSAGE + STRUCTURED CONTEXT
→ semantic understanding
→ goals/subtasks/entities/references
→ allowed Action Catalog
→ semantic retrieval
→ structured planner restricted to candidates
→ schema-driven argument binder
→ OpenAPI validator
→ RBAC/sensitivity/confirmation
→ generic executor
→ responseSchema + metadata
→ schema-driven presentation
→ grounded synthesis/recommendations
```

O core precisa funcionar para provider OpenAPI externo nunca visto sem source code por endpoint.

## 4. Não aceite migração de representação como solução

A classificação deve ser conceitual.

Exemplos:

```text
pathMarkers JSON
→ _DOMAIN_RULES em Python
= NÃO RESOLVIDO

parameterStrategy JSON
→ if path/operationId → strategy
= NÃO RESOLVIDO

routeSegment JSON
→ path-tail/operationId-tail
= NÃO RESOLVIDO

pathMarkers
→ route.operationIds manual por rota semântica
= catálogo técnico residual
```

Planeje sempre a eliminação da authority, não apenas do arquivo/chave.

## 5. Classificação obrigatória por residual

Classifique cada nó/branch/catálogo como:

```text
TECHNICAL_CONTRACT_DUPLICATION
SEMANTIC_ROUTING_HEURISTIC
SEMANTIC_AUTHORITY_DUPLICATION
MULTI_TURN_PATH_COUPLING
ARGUMENT_BINDING_LEGACY_SUBSTITUTE
SEMANTIC_PRESENTATION_METADATA
LLM_COMPOSITION_CANDIDATE
LLM_LOCALIZATION_CANDIDATE
DETERMINISTIC_POLICY
BUSINESS_RULE
FACTUAL_GUARDRAIL
UX_COPY
VOCABULARY_TRANSVERSAL
FAST_PATH_TRANSVERSAL
TEST_FIXTURE
GENERATED_SNAPSHOT
DEAD_CONTENT
UNKNOWN_REQUIRES_EVIDENCE
```

E destino:

```text
OPENAPI_DIRECT
ACTION_CATALOG_MATERIALIZED
SCHEMA_DIRECT
TURN_UNDERSTANDING
ACTION_RETRIEVAL_PLANNER
OPENAPI_ARGUMENT_BINDER
STRUCTURED_CONVERSATION_STATE
EXISTING_TURN_LLM_SYNTHESIS
DETERMINISTIC_SERVICE
KEEP_JSON
KEEP_GENERATED
DELETE_AFTER_GENERALIZATION
INVESTIGATE_FIRST
```

## 6. Ordem de cada workstream

O plano só é executável se cada migração de authority respeitar:

```text
CUTOVER
→ wiring real
→ GENERALIZATION
→ positive + sibling + negative
→ unknown/metamorphic quando material
→ CLEANUP
→ semantic residual search
→ VERIFY
→ COMPLETE_GATE
```

Nunca planeje `DELETE` antes de existir prova de generalização suficiente.

## 7. Ledger e rastreabilidade

Cada requisito material deve possuir:

```text
RQ
→ evidência/current
→ decisão
→ subetapa
→ teste
→ generalization proof
→ cleanup proof
→ ready criteria
```

Estados permitidos:

```text
ATENDIDO_NO_PLANO
HERDADO_POR_SOLUCAO_TRANSVERSAL
FORA_DO_ESCOPO_COM_JUSTIFICATIVA
BLOQUEADO_COM_EVIDENCIA
```

Não desapareça com requisito por compressão de texto.

## 8. “Concluído” significa sem pendência material

Ao revisar status, trate como **não concluído** qualquer etapa que ainda possua no escopo:

```text
PARTIAL
ATENDIDO_PARCIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
DEFERRED sem justificativa
TODO
FIXME
HACK
TEMPORARY
flag/fallback sem exit criteria
```

Se o objetivo original exige remoção/substituição, não aceite `LEGACY_FALLBACK` como `ATENDIDO`.

## 9. Unknown external API e metamorphic

Unknown API precisa ser provider fictício realmente novo:

```text
OpenAPI
→ import/index
→ agent binding
→ allowed actions
→ retrieval
→ planner
→ validator
→ policy
→ executor
→ presentation
```

Não vale:

- mensagem sem sentido;
- rota conhecida com frase nova;
- fixture ensinada ao runtime.

Metamorphic deve renomear provider/path/operationId preservando semântica e schema.

## 10. Frescor de evidência

Candidate evidence pertence a `gitSha + config + dataset + model/provider + OpenAPI/Action Catalog hash`.

Se houver diff posterior que afete uma dimensão, aquela prova volta a `INCONCLUSIVE` até rerun.

Não planeje fechamento usando unknown/metamorphic de commit anterior à mudança que se pretende validar.

## 11. LLM: usar onde agrega semântica

Para cada uso de LLM, responder:

1. o dado já existe no OpenAPI/schema/Action Catalog?
2. é transformação determinística?
3. é semântica estável materializável/cacheável?
4. depende do contexto atual?
5. pode reutilizar a chamada LLM existente do turno?
6. qual fallback em timeout/falha?
7. qual budget de latência/tokens?
8. como output será validado/allowlisted?

Preferência:

```text
canonical source
> deterministic transform
> cached/materialized semantic result
> reuse existing turn LLM
> new dedicated LLM call
```

## 12. Segurança e Clean Architecture

Planeje preservando:

- planner restrito a candidates autorizadas;
- schema validation determinística;
- RBAC/sensitivity/confirmation fora da decisão livre do modelo;
- nenhuma URL arbitrária;
- sem secrets em prompt/log/script;
- domain sem infrastructure/filesystem IO indevido;
- composition root como lugar normal para adapters concretos;
- capability metadata coerente com method/sensitivity/policy.

## 13. Evals obrigatórios no candidate final

Cobrir conforme applicability:

- semantic siblings;
- multi-provider;
- no-tool;
- required present/missing;
- enum/type/body/query/path;
- compound long request;
- multi-turn/follow-up;
- unknown external OpenAPI real;
- metamorphic rename;
- unauthorized/write/destructive;
- prompt/tool-output injection;
- recommendations contextual;
- schema-driven presentation;
- send/stream/simulate/UI;
- persist/reload/F5;
- outcome/task success;
- P50/P95;
- tokens/model calls/tool count/cost.

## 14. Documento ativo

O plano corretivo ativo é:

`planos/11-corrective-cutover-generalization-cleanup.md`

Atualize esse arquivo se a revalidação encontrar drift. Não abra outro plano paralelo para o mesmo objetivo.

README/roadmap/ARCHIVED são status/documentação; não substituem o Plano 11 durante execução.

## 15. Saída deste Plan mode

Entregue:

```text
HEAD_REVALIDATED:
DRIFTS_CONFIRMED:
DRIFTS_RESOLVED_SINCE_AUDIT:
NEW_DRIFTS:
REQUIREMENT_LEDGER_STATUS:
PLAN_11_CHANGES:
READY_SUBSTEP:
BLOCKERS:
```

Pare no planejamento. Para implementação, usar `prompt-cursor-execucao-corretiva.md` e executar E11.S0→E11.S10 sem pular `COMPLETE_GATE`.
