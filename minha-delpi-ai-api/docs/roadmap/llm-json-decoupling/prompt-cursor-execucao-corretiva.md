# Prompt para Cursor — execução corretiva sem pular etapas

Use este prompt quando a intenção for **executar** a Onda J do programa `llm-json-decoupling`.

> Fonte de execução: [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md). Não criar `.cursor/plans/*.plan.md` paralelo para esta iniciativa.

---

## Prompt

Você está trabalhando no monorepo `delpi-central`, com foco em `minha-delpi-ai-api`.

Sua missão é **executar integralmente** o plano:

`minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/planos/11-corrective-cutover-generalization-cleanup.md`

O programa foi reaberto após auditoria arquitetural. Não trate os PASS das Ondas A–I como aceite atual; eles são evidência histórica. O objetivo desta execução é entregar o candidate final correto, generalizável, limpo e comprovado.

## 1. Leia antes de qualquer alteração

Na ordem:

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
15. o Plano 11 completo.

Não inicie E11.S1 antes de concluir o rebaseline E11.S0.

## 2. Protocolo de execução obrigatório

Execute **uma subetapa por vez**, na ordem definida no Plano 11.

Para cada E11.S* siga exatamente:

```text
REVALIDATE HEAD
→ git status / preservar trabalho alheio
→ reler objetivo + RQ + dependencies
→ READY_TO_EXECUTE
→ baseline/precondition da própria etapa
→ menor diff no owner canônico
→ wiring real
→ unit/contract
→ positive
→ sibling
→ negative
→ generalization/metamorphic/unknown quando aplicável
→ adversarial diff review
→ semantic residual search
→ postconditions
→ COMPLETE_GATE
→ atualizar plano/evidência/status
→ somente então liberar a próxima subetapa
```

Não pule uma etapa porque “a próxima parece resolver junto”. Se uma etapa se tornar redundante, registre `EXECUTION_DRIFT`, prove a redundância e atualize o plano antes de avançar.

## 3. Regra central: não mover o legado de lugar

A auditoria encontrou casos onde um catálogo removido dos JSONs foi recriado em Python.

Isso é **falha**, não cleanup.

Considere equivalentes:

```text
pathMarkers JSON == tuple/list/dict de path fragments em Python/TS
path→domain JSON == _DOMAIN_RULES/prefix maps/contains chains
parameterStrategy JSON == if path/operationId → strategy
routeSegment JSON == path-tail/operationId-tail → continuity
registry de operationIds == catálogo técnico paralelo de endpoints
static recommendation profile == mesmo catálogo usado como oracle de “contextual”
```

Se encontrar equivalência desse tipo:

```text
EXECUTION_DRIFT
→ STOP-THE-LINE da workstream
→ corrigir arquitetura
→ reexecutar provas afetadas
```

Não renomeie a dívida para passar scanner.

## 4. Ordem inviolável por workstream

```text
CUTOVER
→ GENERALIZATION
→ CLEANUP
→ VERIFY
```

### CUTOVER

A nova authority precisa estar realmente consumida no runtime principal. Classe criada ou teste unitário isolado não basta.

### GENERALIZATION

Antes de apagar o legado, provar a classe do problema:

- positive;
- sibling;
- negative;
- unknown external API quando tools;
- metamorphic provider/path/operationId rename quando tools;
- LLM-off/fallback seguro quando aplicável.

### CLEANUP

Apagar todos os consumers/fallbacks/mirrors/flags/loaders/caches/tests/docs que ficaram obsoletos.

Depois executar busca residual **semântica**, não só `rg` pelo nome antigo.

### VERIFY

Provar o comportamento no código pós-cleanup. Se o cleanup alterou runtime, reexecute as dimensões afetadas.

## 5. Critério de fechamento de uma subetapa

É proibido marcar `ATENDIDO`, `COMPLETED`, `100%` ou equivalente se houver item material em:

```text
PARTIAL
ATENDIDO_PARCIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
DEFERRED
TODO
FIXME
HACK
TEMPORARY
flag sem exit criteria
fallback sem exit criteria
```

Exceção: requisito explicitamente `FORA_DO_ESCOPO_COM_JUSTIFICATIVA` ou `BLOCKED_WITH_EVIDENCE`. Mesmo assim, se ele impedir o objetivo global, `FINAL_RESULT` continua FAIL/INCONCLUSIVE.

## 6. E11.S0 é obrigatório

Antes de implementar:

- capture `BASE_GIT_SHA`;
- inspecione `git status`;
- revalide todos os símbolos citados no Plano 11;
- localize producers/consumers/fallbacks/tests/docs;
- meça as métricas de dívida do plano;
- congele dataset/config de avaliação;
- identifique quais evidências antigas são somente baseline histórico;
- atualize o Plano 11 se houver drift de código.

Não use um PASS antigo como candidate desta execução.

## 7. Architecture Enforcement deve falhar antes de ficar verde

Na E11.S1, primeiro prove que o gate detecta os drifts reais existentes.

Exemplos que o gate precisa enxergar:

- `_DOMAIN_RULES` path-based;
- endpoint→parameter strategy;
- path/operationId→route segment;
- registry técnico de operationIds;
- credential default em smoke.

Também prove negativos legítimos:

- `action.path` usado genericamente para executar HTTP;
- `operationId` armazenado como metadata técnica;
- fixture de teste mencionando path esperado.

Não escreva um scanner que simplesmente bloqueie as palavras `path` e `operationId`.

## 8. OpenAPI-first universal

O target é:

```text
OpenAPI
→ Action Catalog
→ allowed actions
→ semantic retrieval
→ structured planner restricted to candidates
→ schema-driven argument binder
→ deterministic validator
→ RBAC/sensitivity/confirmation
→ generic executor
→ schema-driven presentation
```

Não criar no core:

- selector por API;
- intent por endpoint;
- path/domain map;
- parameter strategy por endpoint;
- route segment por endpoint;
- presenter obrigatório por endpoint;
- metadata proprietária obrigatória para API externa.

`x-delpi.*` pode enriquecer providers DELPI, mas OpenAPI padrão precisa funcionar sem isso.

## 9. Argument binding

Remova a necessidade de `ParameterStrategyInferenceService` quando o schema já contém o contrato.

O fluxo correto é:

```text
semantic argument delta
→ SchemaDrivenArgumentBinderService
→ OpenAPI declared params/body
→ type/enum/format/required coercion/validation
→ execute or specific clarify
```

Não inferir `product_code`, `date_branch`, `sale_orders` etc. porque o path contém determinada string.

## 10. Multi-turn

Continuity deve usar structured state, por exemplo:

```text
selectedAction/actionId
resolvedEntities
resolvedArguments
resultReferences
pagination
timeRange
pendingRequirements
```

Não usar path-tail, operationId-tail ou arquivo de inventory de outra aplicação como runtime authority.

Teste persist/reload/F5 antes de follow-up.

## 11. Semantic understanding

Mapeie a precedência real entre:

- `ChatIntentRouterService`;
- `ChatTurnUnderstandingService`;
- `ChatTurnAnalysisService`;
- `ChatTaskPlannerService`;
- mappers product/production/KPI;
- fast paths.

O resultado precisa ter owner principal claro.

Heurísticas só podem permanecer se forem transversais, de alta precisão e não escolherem endpoint/pathToken/operationId/domain route.

Não preserve `_TOKEN_RULES` ou keyword/exclude trees endpoint-specific apenas porque cobrem casos conhecidos.

## 12. Recommendations e capability metadata

Recommendations devem usar:

```text
user goals
+ facts/dataAnswer
+ limitations
+ result refs
+ conversation context
+ allowed actions
+ already executed
```

Não use `recommendationQueries` estático como principal oracle de qualidade contextual.

Capability metadata deve refletir método/sensibilidade/policy real. Não atribua universalmente:

```text
readWrite=read
risk=low
parallelSafe=true
```

para writes/admin/destructive.

## 13. Clean Architecture e segurança

- domain não faz filesystem/infrastructure IO como responsabilidade normal;
- application/domain não compõem adapter concreto quando composition root pode injetar;
- use ports/DI simples;
- nenhum smoke/script contém usuário/senha/token default versionado;
- não logar secrets.

## 14. Candidate final é um estado exato

Depois do último diff material, registre `FINAL_CANDIDATE_GIT_SHA`.

Somente então execute a bateria final aplicável:

```text
unit/contract
positive
sibling
negative/no-tool
unknown external OpenAPI real
metamorphic provider/path/operationId rename
required present/missing
enum/type/body/query/path
semantic siblings
multi-provider
compound long request
multi-turn/follow-up
partial failure
unauthorized action
write/destructive confirmation
prompt/tool-output injection
recommendations contextual
schema presentation
send/stream/simulate/UI
persist/reload/F5
P50/P95
LLM calls/tokens/tool count/cost
```

### Importante

Uma mensagem sem sentido como `xyzzy quux` é negative/no-tool. Ela **não prova unknown external API**.

Unknown external API deve ser provider fictício realmente importado/indexado/vinculado sem adicionar código por endpoint.

Se houver qualquer diff que afete uma dimensão depois do teste, aquela prova fica `INCONCLUSIVE` até rerun no novo HEAD.

## 15. Não interrompa a execução prematuramente

Se uma subetapa concluir normalmente, prossiga para a próxima dependente sem pedir ao usuário autorização intermediária, **desde que o pedido atual já tenha autorizado executar o plano** e não exista bloqueio externo real.

Pare somente quando houver:

- secret/credential/dado externo indispensável que não pode ser inferido;
- risco de destruir dados/produção sem autorização;
- conflito de working tree que possa sobrescrever trabalho alheio;
- decisão de produto realmente não determinada pelo plano;
- falha externa que torne impossível produzir a evidência obrigatória.

Nesses casos, registre `BLOCKED_WITH_EVIDENCE`. Não marque o plano concluído.

## 16. Commit/push

Obedeça `test-and-commit.mdc` e o pedido do usuário da sessão.

Não use commit como prova de que uma etapa está correta. Primeiro passe `COMPLETE_GATE`.

## 17. Atualização documental durante a execução

Depois de cada E11.S* concluída:

- atualize o Plano 11;
- registre evidência reproduzível;
- atualize ledger quando apropriado;
- não antecipe `PASS` do roadmap global.

README/roadmap/changelog só voltam a `CONCLUÍDO/ARCHIVED` em E11.S10 depois do candidate final e residual scan.

## 18. Saída obrigatória por subetapa

Sempre reporte:

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
REQUIREMENTS_COVERED:
FILES_CHANGED:
CANONICAL_OWNER:
IMPLEMENTATION_RESULT:
TESTS:
POSITIVE:
SIBLING:
NEGATIVE:
GENERALIZATION:
RESIDUAL_SEARCH:
DRIFTS_FOUND:
POSTCONDITIONS_PROVED:
COMPLETE_GATE:
NEXT_STEP_UNLOCKED:
COMMIT_REALIZADO: sim|nao
PUSH_REALIZADO: sim|nao
```

## 19. Saída final obrigatória

Ao final da Onda J, produza a matriz requisito→implementação→teste→generalização→cleanup→evidência e declare separadamente:

```text
FINAL_CANDIDATE_GIT_SHA:
CUTOVER_RESULT:
GENERALIZATION_RESULT:
CLEANUP_RESULT:
UNKNOWN_EXTERNAL_API:
METAMORPHIC_RENAME:
ARGUMENT_SCHEMA_AUTHORITY:
MULTI_TURN_STRUCTURED_STATE:
SEMANTIC_AUTHORITY_SINGLE_OWNER:
CONTEXTUAL_RECOMMENDATIONS:
CAPABILITY_SECURITY_METADATA:
CLEAN_ARCHITECTURE:
SECURITY_HYGIENE:
SEND_STREAM_SIMULATE_UI:
PERSIST_RELOAD_F5:
R1_R11_REQUIRED_DIMENSIONS:
RESIDUAL_SCAN:
DOCS_MATCH_FINAL_HEAD:
COMPLETE_GATE:
VERIFY_FINAL:
FINAL_RESULT:
```

`FINAL_RESULT=PASS` somente se todos os itens obrigatórios forem PASS no candidate final.

Não deixe “próximo passo”, “depois remover”, “fallback ainda mantido”, “falta smoke”, “falta unknown API” ou “seria bom limpar” e ao mesmo tempo declare conclusão. Se existe trabalho material ainda necessário para o objetivo, continue executando ou mantenha o plano explicitamente aberto/bloqueado.
