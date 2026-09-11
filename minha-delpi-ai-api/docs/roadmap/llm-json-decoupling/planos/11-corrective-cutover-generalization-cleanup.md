# Plano 11 — Correção arquitetural: cutover + generalização + cleanup sem residual

**Prioridade:** P0  
**Status execução:** Onda J · **ABERTO / VERIFY_FINAL_FAILED** · E11.S0–S8 **ATENDIDO** · próxima = **E11.S9**  
**BASE_GIT_SHA (E11.S0):** `8bc84fc6d1cea3edc8cd0c08dceee90f9303e777`  
**Auditoria-base:** S4 `evidence/e11-s4-structured-continuity.md`  
**Origem:** revisão arquitetural pós Ondas A–I em 2026-09-11  
**Objetivo perceptível:** concluir de fato o desacoplamento OpenAPI-first, removendo authorities paralelas e substitutos semânticos do legado, provando que uma API OpenAPI nunca vista funciona sem código por endpoint e sem deixar `PARTIAL`, `LEGACY_FALLBACK`, `INCONCLUSIVE`, TODO ou dívida material escondida como “concluída”.

> Este plano **reabre** o programa. Os PASS anteriores das Ondas A–I permanecem como evidência histórica do estado em que foram executados, mas **não constituem aceite do candidate final** após os drifts identificados abaixo.

---

## 0. Regras obrigatórias de execução

Antes de qualquer diff de runtime, ler na ordem:

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

### Sequência inviolável

Em toda workstream que substitui autoridade legada:

```text
CUTOVER
→ PROVA DE WIRING REAL
→ GENERALIZAÇÃO
→ POSITIVE + SIBLING + NEGATIVE
→ METAMORPHIC / UNKNOWN API quando material
→ CLEANUP
→ BUSCA RESIDUAL SEMÂNTICA
→ VERIFY
→ COMPLETE_GATE
```

Não pular a etapa de generalização para apagar o legado mais cedo.

### Sem “concluído com pendência”

Enquanto existir item material do escopo em qualquer estado abaixo, este plano permanece aberto:

```text
PARTIAL
ATENDIDO_PARCIAL
LEGACY_FALLBACK
SHADOW_ONLY
INCONCLUSIVE
PENDING
DEFERRED sem justificativa de fora de escopo
TODO
FIXME
HACK
TEMPORARY
feature flag sem exit criteria
compatibility branch sem exit criteria
```

---

# 1. EXECUTION_DRIFT confirmado

## D11-01 — `api_route_domains` foi removido parcialmente, mas sua autoridade reapareceu em Python

`app/domain/services/api_route_domain_inference_service.py` contém `_DOMAIN_RULES` com fragments de path conhecidos e declara que as regras foram portadas do antigo mapa JSON.

**Classificação:** `DISPLAY/ROUTING_LEGACY_SUBSTITUTE`  
**Impacto:** `NO_NEW_PATH_MAP_SUBSTITUTE=PASS` anterior não é válido para o candidate atual.

## D11-02 — `parameterStrategy` saiu dos JSONs, mas reapareceu como inferência por path/operationId

A evidência E9.S12.E registra `ParameterStrategyInferenceService` como authority após o DELETE do catálogo.

**Classificação:** `ARGUMENT_BINDING_LEGACY_SUBSTITUTE`  
**Target:** schema OpenAPI + `SchemaDrivenArgumentBinderService` + validator, sem endpoint→strategy.

## D11-03 — `routeSegment` saiu do registry, mas continuidade passou a depender de path-tail/operationId inventory

A implementação usa derivação técnica para reconstruir continuity keys.

**Classificação:** `MULTI_TURN_PATH_COUPLING`  
**Target:** estado conversacional estruturado, actionId/argument/result references e schema; nunca substring/path-tail.

## D11-04 — `route.operationIds` continua sendo catálogo técnico paralelo de rotas conhecidas

A troca `pathMarkers → operationIds exatos` reduziu ambiguidade, mas não eliminou a autoridade manual por endpoint.

**Classificação:** `ROUTING_TECHNICAL_CATALOG_RESIDUAL`.

## D11-05 — Turn semantic ownership permanece duplicado

O pipeline possui LLM estruturado (`ChatTurnAnalysisService`), mas mantém em paralelo `ChatTurnUnderstanding` heurístico, `ChatIntentRouter`, mappers e regras KPI/produção/produto baseadas em termos/tokens.

**Classificação:** `SEMANTIC_AUTHORITY_DUPLICATION`.

## D11-06 — recomendações ainda usam catálogo estático como fallback e como parte do oracle de smoke

`recommendationQueries` ainda participa do resultado e do teste de grounding.

**Classificação:** `CONTEXTUAL_RECOMMENDATION_INCOMPLETE_CUTOVER`.

## D11-07 — metadata de capability sintetizada não respeita efeito real da action

`ChatCapabilityDiscoveryService` atribui `readWrite=read`, `parallelSafe=true`, `risk=low` de forma uniforme.

**Classificação:** `CAPABILITY_METADATA_CONTRACT_DRIFT`.

## D11-08 — boundary/DI residual

Existem serviços de domain/application compondo dependências concretas, acessando filesystem ou escrevendo artefatos fora do ownership ideal.

**Classificação:** `CLEAN_ARCHITECTURE_BOUNDARY_DRIFT`.

## D11-09 — smoke versionado com defaults de credenciais

O smoke E10 contém defaults de usuário/senha de desenvolvimento.

**Classificação:** `SECURITY_HYGIENE_DRIFT`.

## D11-10 — prova de unknown-provider da Onda I não é fresca

Plano 10 reaproveitou E9.S10, executado antes da alteração posterior do motor de domínio/routing.

**Classificação:** `STALE_CANDIDATE_EVIDENCE`.

---

# 2. Ledger de requisitos

| ID | Requisito | Estado inicial |
|---|---|---|
| RQ11-01 | Eliminar path→domain maps/substitutos do core genérico, em qualquer formato | ATENDIDO (E11.S2) |
| RQ11-02 | Eliminar endpoint→parameterStrategy e usar schema OpenAPI como authority | ATENDIDO (E11.S3; path/oid inference removida; helpers schema-driven) |
| RQ11-03 | Eliminar continuidade multi-turn derivada de path/operationId | ATENDIDO (E11.S4; facetas estruturadas) |
| RQ11-04 | Remover `operationIds`/registry técnico como authority de routing | ATENDIDO (E11.S5; arrays observer até S10 DELETE) |
| RQ11-05 | Consolidar ownership semântico e remover NLU endpoint/domain-specific redundante | ATENDIDO (E11.S6; vocabulary facet/kind KEEP; pathTokens DELETE) |
| RQ11-06 | Tornar recommendations contextuais; estático no máximo fallback temporário com exit criteria | ATENDIDO (E11.S7; static=LEGACY_FALLBACK+exit) |
| RQ11-07 | Derivar capability metadata de contract/sensitivity/policy real | ATENDIDO (E11.S7; method+sensitivity) |
| RQ11-08 | Corrigir boundaries/DI/filesystem conforme Clean Architecture | ATENDIDO_PARCIAL (E11.S8; residual FS→S10) |
| RQ11-09 | Remover credenciais hardcoded/defaults sensíveis de scripts/smokes | ATENDIDO (E11.S8; SEMANTIC_SMOKE=0) |
| RQ11-10 | Tornar Architecture Enforcement capaz de detectar substitutos semânticos JSON↔Python/TS | ATENDIDO (E11.S1; debt full-tree ainda vermelho até cleanup) |
| RQ11-11 | Provar unknown external API + metamorphic rename no candidate final | ABERTO |
| RQ11-12 | Provar compound, multi-turn, required/missing args, safety, send/stream/simulate e persist/reload no candidate final | ABERTO |
| RQ11-13 | Encerrar flags/shadows/fallbacks/TODOs materiais ou mantê-los explicitamente fora de escopo sem declarar o objetivo global concluído | ABERTO |
| RQ11-14 | Atualizar README/roadmap/ledger/changelog/docs canônicas somente com estados sustentados pelo HEAD final | ABERTO |

---

# 3. Arquitetura CURRENT → TARGET

## CURRENT pós-auditoria

```text
User message
→ query improvement
→ heuristics/router/TU mappers
→ optional LLM Turn Analysis
→ Action Catalog / retrieval / planner
→ alguns bridges/registries/operationIds/path-derived domains/strategies
→ validation/policy/execution
→ schema presentation + profiles/fallbacks
→ static/contextual mixed recommendations
```

Problema: o caminho novo existe, mas authorities antigas ou equivalentes ainda participam de decisões e vários “DELETEs” apenas mudaram de representação.

## TARGET

```text
USER MESSAGE + STRUCTURED CONVERSATION STATE
        |
        v
SEMANTIC TURN UNDERSTANDING / ANALYSIS
        |
        v
goals + entities + references + presentation intent
        |
        v
ALLOWED ACTION CATALOG
        |
        v
semantic retrieval per goal
        |
        v
STRUCTURED PLANNER restricted to candidates
        |
        v
argument delta
        |
        v
OPENAPI SCHEMA BINDER + VALIDATOR
        |
        v
RBAC + sensitivity + confirmation
        |
        v
GENERIC EXECUTOR
        |
        v
responseSchema + payload + semantic metadata
        |
        v
SCHEMA-DRIVEN PRESENTATION
        |
        v
existing grounded LLM synthesis
        |
        +--> contextual recommendations/follow-ups
```

### Invariantes do TARGET

- nenhuma nova API exige editar core por path/provider/operationId;
- `x-delpi.*` é enrichment opcional, nunca requisito universal;
- path/method/operationId continuam disponíveis como contrato técnico de execução, mas não viram regra semântica hardcoded;
- RBAC/safety/validation continuam determinísticos;
- LLM não escolhe action fora de candidates autorizadas;
- MFE não redecide semântica de domínio;
- persisted display/context state não exige rerun de LLM para F5/reload.

---

# 4. Métricas de dívida obrigatórias

Capturar no E11.S0 e novamente no E11.S10:

```text
PATH_COUPLED_RUNTIME_RULES
OPERATION_ID_COUPLED_RUNTIME_RULES
ENDPOINT_STRATEGY_RULES
MANUAL_INTENT_RULES
LEGACY_BRANCHES
LEGACY_FALLBACKS
SHADOWS_WITHOUT_EXIT
TECHNICAL_CATALOG_ENTRIES
HARDCODED_SMOKE_CREDENTIAL_DEFAULTS
DOMAIN_SERVICES_WITH_INFRA_IO
APPLICATION_SERVICES_COMPOSING_INFRA_DIRECTLY
TODO_FIXME_HACK_MATERIAL_COUNT
```

Objetivo final para itens de acoplamento técnico removíveis: **0**, salvo exceção explicitamente classificada como contrato técnico legítimo e não authority semântica.

---

# 5. Etapas de execução

## E11.S0 — Rebaseline, inventário final e reabertura formal

**TIPO:** INVESTIGATION / VERIFY  
**Cobre:** RQ11-10, RQ11-13, RQ11-14

### Fazer

1. registrar `BASE_GIT_SHA` atual;
2. executar `git status` e preservar trabalho alheio;
3. reler todos os consumers dos símbolos citados em D11-01..10;
4. medir as métricas de dívida §4;
5. congelar dataset/corpus de candidate desta Onda;
6. identificar quais evidências anteriores continuam válidas apenas como baseline histórico;
7. atualizar este plano se algum símbolo/ownership mudou.

### Não fazer

- nenhum diff de comportamento antes de concluir o inventário;
- não reaproveitar `PASS` histórico como candidate final;
- não alterar fixtures para adaptar expectativa ao código atual.

### Pronto quando

- CURRENT confirmado no HEAD;
- ledger RQ11 atualizado;
- dataset/version/hash definidos;
- cada drift possui producer/consumer/fallback/test/doc mapeados;
- `READY_TO_EXECUTE` de E11.S1 comprovado.

### Estado E11.S0 (2026-09-11)

- **COMPLETE_GATE:** ATENDIDO
- Evidência: `evidence/e11-s0-rebaseline.md` + `evidence/e11-s0-debt-metrics.json`
- Corpus freeze: `routing_cases.json@v1` sha256 `7ff37332…039d`; `r1_r11_corpus_v1` sha256 `371f0cfa…c26b8`
- RQ11 ledger permanece ABERTO (S0 só reabre/inventaria; não fecha requisitos de cutover)
- `READY_TO_EXECUTE` E11.S1: **sim**

---

## E11.S1 — Architecture Enforcement contra substitutos semânticos

**TIPO:** CUTOVER DE GATE  
**Cobre:** RQ11-10

### Objetivo

Fazer o CI detectar o conceito proibido, não apenas nomes específicos de chaves JSON.

### Fazer

Estender os gates existentes, sem criar um segundo sistema, para detectar pelo menos:

- path/domain maps em Python/TS (`_DOMAIN_RULES`, prefix maps e equivalentes);
- endpoint→parameter strategy;
- path/operationId→route segment;
- runtime registry que ensina action por lista manual de operationIds;
- credencial default em smoke/test script;
- reintrodução de `pathMarkers/pathToken/pathContains/pathRules` em content;
- known-endpoint branch adicionado para corrigir fixture.

O gate deve permitir uso técnico legítimo de `path`/`operationId` para execução/observabilidade sem confundir com semântica hardcoded.

### Teste mínimo

- positive: código atual proibido é detectado;
- sibling: outra representação equivalente também falha;
- negative: leitura genérica de `action.path` para montar HTTP não falha;
- negative: fixture/test pode mencionar path esperado sem ser runtime authority.

### Pronto quando

O gate fica vermelho no baseline pelos drifts reais e não por falso positivo estrutural.

**Atenção:** não “corrigir” o gate para ficar verde antes do cleanup. O vermelho é a prova de que o enforcement enxerga a dívida.

### Estado E11.S1 (2026-09-11)

- **COMPLETE_GATE:** ATENDIDO
- Evidência: `evidence/e11-s1-semantic-debt-gate.{md,json}`
- RQ11-10: **ATENDIDO** (detecção); dívida permanece até cleanup
- Gate baseline: **VERMELHO** (274 findings; sem exceção ampla)
- `READY_TO_EXECUTE` E11.S2: **sim**

---

## E11.S2 — `apiRouteDomain`: remover authority path-based

**TIPO:** CUTOVER → GENERALIZATION → CLEANUP  
**Cobre:** RQ11-01, RQ11-11

### CUTOVER

1. mapear todos os consumers de `apiRouteDomain` e classificar cada uso: routing, presentation, telemetry, policy, UX;
2. eliminar usos onde o domínio não é necessário;
3. onde semântica for útil, obter de metadata semântica do OpenAPI/Action Catalog (`tags`, summary/description/schema) ou materialização genérica; `x-delpi` pode enriquecer, nunca ser obrigatório;
4. unknown provider sem classificação específica deve funcionar com `generic`/tag semantic fallback, sem capability outage.

### GENERALIZAÇÃO

Provar:

- action DELPI conhecida;
- sibling de outro domínio;
- provider OpenAPI externo sem `x-delpi`;
- rename metamórfico de provider/path/operationId preservando metadata semântica;
- negative: path parecido não força domínio errado.

### CLEANUP

Remover:

- `ApiRouteDomainInferenceService._DOMAIN_RULES`;
- path-prefix/contains equivalents usados como semantic authority;
- docs que legitimem path inference como arquitetura final;
- tests que congelem paridade com antigo path map em vez de semântica.

### Complete gate

`PATH_COUPLED_RUNTIME_RULES` associado a domain = 0 e unknown/metamorphic PASS no código pós-cleanup.

### Estado E11.S2 (2026-09-11)

- **COMPLETE_GATE:** ATENDIDO
- Evidência: `evidence/e11-s2-api-route-domain-semantic.md`
- `SEMANTIC_PATH_DOMAIN_MAP` full-tree = 0
- RQ11-01 ATENDIDO; unknown/metamorphic unit PASS (live/R11 ficam em E11.S9)
- `READY_TO_EXECUTE` E11.S3: **sim**

---

## E11.S3 — Argument binding: schema authority, sem `ParameterStrategyInferenceService`

**TIPO:** CUTOVER → GENERALIZATION → CLEANUP  
**Cobre:** RQ11-02, RQ11-11, RQ11-12

### CUTOVER

- rastrear todos os consumers de `ParameterStrategyInferenceService`;
- ligar `TurnRefinement`/planner argument delta ao `SchemaDrivenArgumentBinderService` e `ValidateActionArgumentsService`;
- nomes/location/required/type/enum/format vêm do OpenAPI action schema;
- required ausente → clarify específico;
- nenhuma strategy decide argumentos porque o path “parece produto/filial/data”.

### GENERALIZAÇÃO

Casos mínimos:

- path param string;
- query integer;
- enum;
- body object;
- required missing;
- parameter com nome nunca visto no monorepo;
- provider/path/operationId renomeados com schema preservado.

### CLEANUP

- remover `ParameterStrategyInferenceService` se nenhum contrato legítimo restar;
- remover enum/catalog de strategies que tenha ficado sem consumer;
- remover shadows/flags/tests de paridade do endpoint→strategy antigo;
- busca residual por nomes de strategies e branches equivalentes.

### Complete gate

`ENDPOINT_STRATEGY_RULES = 0`; R3 PASS no candidate pós-cleanup.

### Estado E11.S3 (2026-09-11)

- **COMPLETE_GATE:** ATENDIDO (path/oid→strategy = 0; `SEMANTIC_ENDPOINT_PARAMETER_STRATEGY=0`)
- Evidência: `evidence/e11-s3-schema-argument-binding.md`
- RQ11-02 ATENDIDO; R3 live fica em E11.S9
- Residual: recipes `parameterStrategies` / legacy helpers ainda podem enriquecer params **quando o schema declara** os campos — não via path map
- `READY_TO_EXECUTE` E11.S4: **sim**

---

## E11.S4 — Multi-turn/refinement sem path-tail/operationId-tail

**TIPO:** CUTOVER → GENERALIZATION → CLEANUP  
**Cobre:** RQ11-03, RQ11-12

### CUTOVER

Follow-up deve usar estado estruturado já persistido/transportado, como:

```text
selectedAction/actionId
resolvedEntities
resolvedArguments
resultReferences
pagination/timeRange
pendingRequirements
lastResult excerpt/identity
```

Não reconstruir intent/continuity key pelo endereço técnico da action.

### GENERALIZAÇÃO

Testar:

- “e os fornecedores?”;
- “só filial 01”;
- “e no mês passado?”;
- “agora o produto X” sobrescrevendo contexto anterior;
- pagination/filter;
- provider/path/operationId renomeado mantendo action semantics/state;
- persist/reload/F5 antes do follow-up.

### CLEANUP

Remover:

- `RouteSegmentInferenceService` baseado em path/operationId;
- leitura runtime de `api-delpi/...openapi_operation_id_inventory.json` para continuidade;
- path-tail/operationId-tail maps;
- follow-up branches que só existem para routes conhecidas.

### Complete gate

R6 PASS e `PATH/OPERATION_ID_COUPLED_RUNTIME_RULES` de continuidade = 0.

### Estado E11.S4 (2026-09-11)

- **COMPLETE_GATE:** ATENDIDO (`SEMANTIC_PATH_ROUTE_SEGMENT=0`; inventory FS removido)
- Evidência: `evidence/e11-s4-structured-continuity.md`
- RQ11-03 ATENDIDO; R6 live em E11.S9
- `READY_TO_EXECUTE` E11.S5: **sim**

---

## E11.S5 — Registry/operationIds: retirar autoridade técnica paralela

**TIPO:** CUTOVER → GENERALIZATION → CLEANUP  
**Cobre:** RQ11-04, RQ11-11

### CUTOVER

- provar que seleção principal usa `allowed Action Catalog → retrieval → planner` sem narrowing obrigatório por registry routeId/operationIds;
- consumers que precisam de routeId apenas para UX/telemetry devem receber semantic metadata já materializada, não lista de endpoints;
- confirmar se `operational_route_registry` ainda tem responsabilidade legítima não técnica; reduzir ao mínimo ou remover.

### GENERALIZAÇÃO

- action conhecida;
- action irmã;
- unknown external API sem entrada no registry;
- metamorphic rename;
- multi-provider com funções parecidas.

### CLEANUP

Remover quando sem consumer legítimo:

- `route.operationIds` runtime authority;
- `select_registry_route_id` narrowing técnico;
- manual route generators/CI mirrors que só congelam OpenAPI em outro formato;
- compatibility marker branches sem exit criteria;
- dead shadows/flags após cutover.

Não remover metadata técnica `operationId` do Action Catalog; remover apenas o catálogo paralelo que a usa como regra semântica.

### Complete gate

Nova API não exige registry edit para routing authority; `SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG` runtime authority = 0.

- **COMPLETE_GATE:** ATENDIDO (`operationIdsRuntimeAuthority=false`; cutover permanente em `select_registry_route_id`)
- Evidência: [`../evidence/e11-s5-registry-operation-ids-cutover.md`](../evidence/e11-s5-registry-operation-ids-cutover.md)
- `READY_TO_EXECUTE` E11.S6: **sim**

---

## E11.S6 — Consolidar semantic understanding e retirar NLU endpoint/domain-specific

**TIPO:** CUTOVER → GENERALIZATION → CLEANUP  
**Cobre:** RQ11-05, RQ11-12

### Inventário antes do cutover

Mapear ownership e precedência reais de:

- `ChatIntentRouterService`;
- `ChatTurnUnderstandingService`;
- `ChatTurnAnalysisService`;
- `ChatTaskPlannerService`;
- `TurnUnderstanding*Kpi/Product/Production*MapperService`;
- `department_kpi_rules.json`;
- product/production intent bundles;
- fast paths legítimos.

### Decisão alvo

Uma única authority semântica principal deve produzir entendimento estruturado para casos não triviais. Heurísticas podem permanecer somente quando:

- são transversais;
- têm alta precisão comprovada;
- não mapeiam frase→endpoint/pathToken/operationId/domain route;
- possuem negative cases e não bloqueiam o LLM quando ambíguas.

### GENERALIZAÇÃO

- frases curtas/longas;
- typo/sinônimo/informal;
- dois KPIs semanticamente próximos;
- domínio nunca visto no código;
- pedido composto com dependências;
- no-tool;
- unknown provider.

### CLEANUP

Eliminar tabelas `_TOKEN_RULES`, keyword/exclude trees e path/catalog tokens usados para ensinar endpoints, quando o novo owner cobrir os casos.

Vocabulário corporativo transversal pode permanecer se não escolher endpoint diretamente.

### Complete gate

`MANUAL_INTENT_RULES` endpoint/domain-specific (pathTokens / pathMarkers de routing) = 0; vocabulary facet/kind transversal documentado como KEEP; compound live R1/R2/R9 → E11.S9.

- **COMPLETE_GATE:** ATENDIDO (`SEMANTIC_CONTENT_LATERAL_PATH_KEY=0`; production pathTokens DELETE; KPI virtual sem markers)
- Evidência: [`../evidence/e11-s6-semantic-authority-cutover.md`](../evidence/e11-s6-semantic-authority-cutover.md)
- `READY_TO_EXECUTE` E11.S7: **sim**

---

## E11.S7 — Recommendations contextuais + capability metadata correta

**TIPO:** CUTOVER → GENERALIZATION → CLEANUP  
**Cobre:** RQ11-06, RQ11-07

### Recommendations

- usar user goals + facts/dataAnswer + limitations + result refs + context + allowed actions + already executed;
- preferir reutilizar síntese LLM já existente no turno;
- validar actionId contra candidates/allowed actions;
- recommendation nunca autoexecuta write;
- fallback determinístico mínimo é aceitável durante rollout, com observabilidade e exit criteria.

**Proibido:** usar `recommendationQueries` estático como oracle principal para provar que a geração é contextual.

### Capability metadata

Derivar de contract/policy real:

```text
method + sensitivity + policy
→ readWrite
→ risk
→ parallelSafe
→ requiresConfirmation
```

Não marcar tudo como read/low/parallel-safe.

### GENERALIZAÇÃO

- read action;
- write action;
- destructive/admin;
- unknown external action;
- recommendation depois de resultado parcial;
- evitar ação já executada;
- LLM-off fallback seguro.

### CLEANUP

Remover static recommendation profiles quando métricas e candidate final permitirem; senão manter como `BLOCKED_WITH_EVIDENCE`, e o plano permanece não concluído se o objetivo original exigir sua remoção.

- **COMPLETE_GATE:** ATENDIDO (capability contract-derived; static recs = LEGACY_FALLBACK com exit criteria)
- Evidência: [`../evidence/e11-s7-recommendations-capability-metadata.md`](../evidence/e11-s7-recommendations-capability-metadata.md)
- `READY_TO_EXECUTE` E11.S8: **sim**

---

## E11.S8 — Clean Architecture + segurança de scripts

**TIPO:** CLEANUP / ARCHITECTURE  
**Cobre:** RQ11-08, RQ11-09

### Fazer

- mover filesystem/generation/persistence para infrastructure/tooling quando estiver em domain;
- composition root injeta repository/gateway/LLM; application/domain não escolhem adapter concreto como caminho normal;
- manter ports pequenos e testáveis;
- remover defaults versionados de usuário/senha/token em smoke scripts;
- script deve exigir env ou mecanismo dev seguro já canônico;
- procurar secrets/credentials equivalentes nos arquivos alterados pela iniciativa.

### Testes

- architecture enforcement;
- unit tests com dependency injection/fakes;
- smoke falha claramente quando credential env requerida está ausente;
- nenhuma credencial aparece em output/evidence.

- **COMPLETE_GATE:** ATENDIDO (credenciais; `SEMANTIC_*` full-tree=0; CA residual→S10)
- Evidência: [`../evidence/e11-s8-clean-arch-smoke-credentials.md`](../evidence/e11-s8-clean-arch-smoke-credentials.md)
- `READY_TO_EXECUTE` E11.S9: **sim**

---

## E11.S9 — Candidate final: generalização e R1–R11 frescos

**TIPO:** VERIFY / RELEASE BLOCKER  
**Cobre:** RQ11-11, RQ11-12, RQ11-13

### Pré-condição

Todas as mudanças de runtime de E11.S1–S8 concluídas. Registrar `FINAL_CANDIDATE_GIT_SHA`.

### Obrigatório

Executar no mesmo candidate final:

1. unit/contract relevantes;
2. positive conhecido;
3. sibling;
4. negative/no-tool;
5. unknown external OpenAPI **real**;
6. metamorphic provider/path/operationId rename;
7. required present/missing + enum/type/body/query/path;
8. semantic siblings + multi-provider;
9. compound long request;
10. multi-turn/follow-up;
11. partial failure;
12. unauthorized action;
13. write/destructive confirmation;
14. prompt/tool-output injection;
15. recommendations grounded/contextual;
16. schema-driven presentation;
17. send/stream/simulate/UI parity;
18. persist/reload/F5;
19. latency P50/P95;
20. LLM calls/tokens/tool count/cost.

### Unknown API não é negative nonsense

O provider fictício deve ser importado/indexado/bound ao agent sem alteração de core por endpoint. O caso `xyzzy/quux` pode continuar como negative, mas não conta como unknown API.

### Frescor

Qualquer diff material depois desta bateria invalida as dimensões afetadas e obriga rerun antes do fechamento.

### Pronto quando

Todas as `requiredDimensions` aplicáveis estão PASS. WARN/INCONCLUSIVE bloqueia release quando a dimensão é required.

---

## E11.S10 — Cleanup final, residual scan, docs e verify-final

**TIPO:** CLEANUP / VERIFY_FINAL  
**Cobre:** todos os RQ11

### Busca residual final

Executar buscas por conceito, não apenas por nomes:

```text
pathMarkers / pathContains / pathToken / pathRules
_DOMAIN_RULES / prefix maps / contains(path)
operationId lists used for semantic selection
parameterStrategy / strategy names / endpoint→binder branches
routeSegment / path-tail / operationId-tail
recommendationQueries / profile fallback authority
_TOKEN_RULES / keyword+exclude endpoint routing
legacy/shadow/fallback flags
TODO / FIXME / HACK / TEMPORARY
default user/password/token in smokes
filesystem IO inside domain
infra composition inside application/domain
```

Cada hit deve receber uma classificação:

```text
REMOVE_NOW
CONTRACT_LEGITIMATE
TRANSVERSAL_POLICY_KEEP
TEST_ONLY
DOC_HISTORY_ONLY
BLOCKED_WITH_EVIDENCE
```

`BLOCKED_WITH_EVIDENCE` material impede `FINAL_RESULT=PASS` se conflita com o objetivo desta iniciativa.

### Documentação

Atualizar somente após o residual scan e candidate final:

- `README.md`;
- `roadmap.md`;
- este plano;
- `evidence/execution-ledger.md`;
- changelog relacionado;
- docs arquiteturais canônicas impactadas;
- Help quando user-facing.

Só arquivar novamente após `VERIFY_FINAL=PASS`.

---

# 6. Matriz obrigatória de fechamento

Preencher no final:

| Requisito | Implementação final | Generalização | Cleanup residual | Evidência FINAL_CANDIDATE_GIT_SHA | Status |
|---|---|---|---|---|---|
| RQ11-01 | | | | | |
| RQ11-02 | | | | | |
| RQ11-03 | | | | | |
| RQ11-04 | e11-s5 | cutover+facet | test_e11_s5_* | ATENDIDO | arrays observer |
| RQ11-05 | e11-s6 | TU+mappers authority | test_e11_s6_* | ATENDIDO | live R1/R2/R9→S9 |
| RQ11-06 | e11-s7 | dual-run exit | test_e6_s4_* | ATENDIDO | profiles até exit |
| RQ11-07 | e11-s7 | method+sensitivity | test_e11_s7_* | ATENDIDO | |
| RQ11-08 | | | | | |
| RQ11-09 | | | | | |
| RQ11-10 | | | | | |
| RQ11-11 | | | | | |
| RQ11-12 | | | | | |
| RQ11-13 | | | | | |
| RQ11-14 | | | | | |

Nenhuma célula material pode ser omitida.

---

# 7. Definition of Done da Onda J

```text
CUTOVER_RESULT = PASS
GENERALIZATION_RESULT = PASS
CLEANUP_RESULT = PASS
UNKNOWN_EXTERNAL_API = PASS_ON_FINAL_CANDIDATE
METAMORPHIC_RENAME = PASS_ON_FINAL_CANDIDATE
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
FINAL_RESULT = PASS
```

Se qualquer linha acima estiver `PARTIAL`, `WARN` obrigatório, `INCONCLUSIVE`, `LEGACY_FALLBACK` incompatível com o objetivo ou `FAIL`:

```text
FINAL_RESULT = VERIFY_FINAL_FAILED
```

---

# 8. Saída obrigatória do Cursor ao terminar cada subetapa

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

Não escrever “feito”, “100%”, “concluído” ou “PASS” sem preencher os campos materiais acima.

---

# 9. Revisão adversarial final

Antes de `FINAL_RESULT=PASS`, responder com evidência:

1. Algum antigo mapa JSON foi apenas movido para Python/TS?
2. Existe qualquer path→domain semantic authority no core?
3. Existe endpoint→parameter strategy?
4. Follow-up ainda depende de path/operationId?
5. Registry/operationIds ainda ensina routing de actions conhecidas?
6. Uma nova API exige editar core?
7. O teste unknown realmente importou provider nunca visto?
8. O rename metamórfico foi executado **depois do último diff material**?
9. Existe mais de um owner semântico concorrente para intent/task planning?
10. Há keyword/token table endpoint-specific no runtime?
11. Recommendations continuam sendo essencialmente lista estática por profile?
12. O oracle de recommendation mede contexto ou apenas igualdade com catálogo legado?
13. Capability metadata reflete writes/admin/destructive corretamente?
14. Algum domain service faz filesystem/infrastructure IO indevido?
15. Algum application/domain service compõe adapter concreto sem necessidade?
16. Algum smoke contém credential default?
17. Há flag/shadow/fallback sem exit criteria?
18. Há TODO/FIXME/HACK material no escopo?
19. Toda evidência de release pertence ao `FINAL_CANDIDATE_GIT_SHA`?
20. README/roadmap/ledger descrevem o estado real e não um PASS histórico?
21. O runtime final ficou **mais simples e mais geral**, ou apenas redistribuiu o mesmo conhecimento?

Qualquer resposta material sem prova mantém o plano aberto.
