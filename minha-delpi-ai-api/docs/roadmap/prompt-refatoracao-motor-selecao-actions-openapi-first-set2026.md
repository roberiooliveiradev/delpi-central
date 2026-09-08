# Prompt mestre — Refatoração do motor de seleção universal de Actions OpenAPI-first

**Tipo:** prompt executivo / playbook de implementação  
**Status:** implementação entregue (núcleo OpenAPI-first + cutover; registry só policies/rollback)  
**Data:** setembro/2026  
**Escopo principal:** `minha-delpi-ai-api`  
**Objetivo:** tornar a seleção e execução de Actions realmente generalista para qualquer provider OpenAPI importado, inclusive APIs externas nunca vistas pelo Minha DELPI.

**Entrega alinhada (set/2026):**
- Default `CHAT_OPENAPI_PLANNER_MODE=on` (Settings); Compose sem flags de modo.
- Fail-closed sem fallback registry; `autoTierC` só em CI.
- Retrieval híbrido + planner com scoring de especificidade + decomposição compound + estado multi-turno por `actionId`/`executionContext`.
- Validator com type/enum/format; manifesto semântico inclui sensitivity.
- Facade `ExternalActionSelectionService.select_action` redireciona para OpenAPI-first quando `mode=on` (Fase 9).
- Path-token discovery / markers desligados no caminho `mode=on`.
- Planner LLM opcional (`CHAT_OPENAPI_PLANNER_LLM_ENABLED` / `planner.llmEnabled`, default off — fail-soft para determinístico).
- Aceite: logistics + ACME component_cost + structure-excel / last-purchase / budget-history / price-intelligence.
- Dívida residual: remoção física dos módulos legado (`ExternalActionRegistryDispatch*`, markerPools) quando `mode=off` deixar de ser necessário.

---

## 1. Por que este documento existe

O Minha DELPI AI já possui:

- providers OpenAPI persistidos;
- catálogo de actions importadas;
- vínculo provider ↔ agente;
- `allowed_action_ids`;
- embeddings/ranking semântico;
- executor HTTP genérico;
- políticas de leitura/escrita/admin/confirmação;
- apresentação schema-driven;
- gates contra novos hardcodes arquiteturais.

Porém, a seleção operacional ainda conserva arquitetura de transição baseada em registry, route segments, intents por domínio, markers de path/operationId e heurísticas específicas. Os testes de regressão atuais já demonstram o efeito: quando há actions semanticamente próximas, a seleção pode escolher uma operação genérica em vez da operação específica pedida pelo usuário.

Exemplos observados em CI:

```text
"baixar estrutura em excel do produto 90261757"
  esperado: structure-excel
  selecionado: structure

"exportar planilha BOM do 90261757"
  esperado: structure-excel
  selecionado: structure

"Análise de preço da matéria-prima 10080001"
  esperado: raw-material-price-intelligence
  selecionado: pricing

"Última compra e ICMS do produto 10080001"
  esperado: last-purchase
  selecionado: purchases

"Histórico de orçamento de compra do produto 10080001"
  esperado: purchase-budget-history
  selecionado: purchases
```

Esses exemplos são **evidências de uma limitação geral**, não uma lista de frases a serem tratadas individualmente.

A correção deve permitir que uma API de terceiro, nunca vista antes pelo projeto, funcione com o mesmo mecanismo de seleção sem exigir:

- novo `if` em Python;
- novo intent específico por endpoint;
- novo `pathMarker`;
- novo `operationIdMarker`;
- nova `parameterStrategy` específica da rota;
- novo selector dedicado;
- novo presenter obrigatório;
- código do provider dentro do monorepo;
- conhecimento prévio do path da API.

---

# 2. PROMPT PARA O CURSOR

> Copie a partir daqui como instrução de execução.

---

## PAPEL

Atue como **Arquiteto de Software Sênior + Pair Programmer** da Minha DELPI.

Você deve investigar, corrigir, implementar, testar e documentar a evolução do motor de seleção de Actions da `minha-delpi-ai-api`.

A entrega não é uma correção localizada dos testes que falham. A entrega é uma **refatoração arquitetural generalista OpenAPI-first** capaz de resolver corretamente operations semanticamente próximas de qualquer API importada.

---

## 2.1 LEITURA OBRIGATÓRIA ANTES DE ALTERAR CÓDIGO

Leia e respeite, nesta ordem:

1. `documentos/instrucoes_oficiais_gpt_arquiteto_delpi_central.md`
2. `.cursor/rules/development-standards-index.mdc`
3. `.cursor/rules/evidence-driven-execution.mdc`
4. `.cursor/rules/centralized-rules-first.mdc`
5. `.cursor/rules/clean-code-architecture-guardrails.mdc`
6. `.cursor/rules/root-cause-generalized-fix.mdc`
7. `.cursor/rules/chat-intelligence-base.mdc`
8. `.cursor/rules/openapi-first-universal-tool-routing.mdc`
9. `.cursor/rules/operational-api-routing.mdc`
10. `.cursor/rules/assistant-content-json.mdc`
11. `.cursor/rules/ai-intelligence-evaluation.mdc`
12. `.cursor/rules/ai-context-and-tool-budget.mdc`
13. `.cursor/rules/ai-external-tools-security.mdc`
14. `.cursor/rules/http-integration-resilience.mdc`
15. `.cursor/rules/observability-standards.mdc`
16. `.cursor/rules/contract-evolution-backward-compatibility.mdc`
17. `.cursor/rules/architecture-ci-enforcement.mdc`
18. `.cursor/rules/test-and-commit.mdc`

Leia também:

- `minha-delpi-ai-api/docs/api/04-actions-openapi.md`
- `minha-delpi-ai-api/docs/roadmap/docie-desacoplamento-selecao-rotas-openapi.md`
- `minha-delpi-ai-api/docs/architecture/chat-pre-llm-layers.md`
- `minha-delpi-ai-api/docs/architecture/README.md`
- `minha-delpi-ai-api/docs/flows/04-operacional-e-apresentacao.md`
- `minha-delpi-ai-api/docs/development/guia-desenvolvimento.md`

**Importante:** documentos antigos podem representar arquitetura de transição. Não trate uma descrição histórica como verdade superior ao código atual, ao OpenAPI persistido ou às regras canônicas vigentes.

---

# 3. PERGUNTA ARQUITETURAL QUE A IMPLEMENTAÇÃO DEVE RESPONDER

Antes de alterar código, responda com evidência:

> Se eu conectar hoje uma API OpenAPI de terceiro que o Minha DELPI nunca viu, importar o schema, gerar/indexar as actions, vinculá-la a um agente e habilitar suas permissions/policies, o que exatamente ainda impede o agente de utilizar suas operações com a mesma inteligência usada para a `api-delpi`?

Para cada impedimento encontrado, informe:

| Campo | Conteúdo obrigatório |
|---|---|
| causa | por que a API externa fica em desvantagem |
| arquivo | arquivo real |
| classe/método | implementação responsável |
| evidência | trecho/fluxo/teste que comprova |
| impacto | seleção, parâmetros, contexto, execução ou apresentação |
| solução generalista | solução sem conhecimento do endpoint |
| fase | etapa de implementação |
| teste | como provar generalização |

**Resposta proibida:** “adicionar a rota no registry”.

---

# 4. ESTADO ATUAL A SER INVESTIGADO

Não assuma que os nomes abaixo continuam idênticos. Confirme no código antes de decidir.

Investigue pelo menos:

```text
ExternalActionSelectionService
ExternalActionSelectionDispatchService
ExternalActionSelectionSupportService
ExternalActionRouteSelectionService
ExternalActionOperationalRouteSelectionService
ExternalActionGenericRouteSelectionService
ExternalActionRegistryDispatchPhaseService
OperationalRouteRegistryService
OperationalRouteMatcherService
OperationalApiParameterBuilderService
ExternalActionCandidateDiscoveryService
ExternalActionManifestTextService
semantic ranker / embeddings repository
ExecuteExternalActionUseCase
HttpExternalActionGateway
ChatToolContextService
```

Mapeie também:

- modelo persistido de provider;
- modelo persistido de action catalog;
- importação OpenAPI;
- construção dos embeddings;
- `find_candidate_actions`;
- `allowed_action_ids`;
- overrides por agente;
- sensitivity/policies;
- confirmação de write/admin/destructive;
- metadata de `toolCalls`;
- estado de continuação multi-turno;
- extração atual de parâmetros;
- apresentação pós-tool.

---

# 5. PROBLEMAS CONCRETOS JÁ CONHECIDOS

## 5.1 Candidate discovery ainda possui conhecimento de rota

Hoje `ExternalActionSelectionSupportService.list_allowed_candidates()` combina busca do repositório com descoberta adicional por markers resolvidos da mensagem.

Investigue a dependência de:

```text
ExternalActionCandidateDiscoveryService.resolve_path_markers(message)
```

E toda lógica equivalente a:

```text
marker in path
marker in operationId
```

O mecanismo universal não deve precisar traduzir linguagem do usuário para fragmentos técnicos de path antes do retrieval.

---

## 5.2 Há APIs auxiliares de busca por path/operation token

Investigue usos de métodos como:

```text
find_allowed_actions_by_path_token(...)
find_catalog_actions_by_path_token(...)
```

Esses métodos podem permanecer temporariamente para compatibilidade, mas não podem ser o caminho canônico de uma nova API externa.

---

## 5.3 Continuação multi-turno ainda pode depender de fragmento de path

Investigue fluxos como:

```text
resolve_previous_external_action_id(... path_fragment=...)
```

O estado multi-turno deve preferir `actionId`, `providerKey`, `operationId`, argumentos resolvidos, entity/data shape e metadata estruturada, não reconstruir intenção procurando substring no path executado.

---

## 5.4 O facade ainda expõe métodos por domínio

`ExternalActionSelectionService` ainda possui wrappers como seleção de produto, metadata, refinamentos etc.

Nem todo wrapper precisa ser removido imediatamente, mas confirme quais representam:

```text
orquestração legítima
vs
ensino de endpoint/domínio ao core
```

Reduza progressivamente a segunda categoria.

---

## 5.5 O registry ainda é uma fonte técnica concorrente

`operational_route_registry.json` contém/continha conceitos como:

```text
pathMarkers
operationIdMarkers
routeSegment
parameterStrategy
priority por rota
matchers específicos
```

OpenAPI + Action Catalog já possuem a informação técnica da operation.

O registry deve ser tratado como:

```text
LEGACY / COMPATIBILITY / MIGRATION
```

Não como requisito para novas APIs.

---

## 5.6 Documentação canônica contém drift

`docs/api/04-actions-openapi.md` ainda ensina, na seção de rotas operacionais DOCIE, a adicionar uma entrada ao `operational_route_registry.json` para cada nova rota GET.

O documento `docs/roadmap/docie-desacoplamento-selecao-rotas-openapi.md` declara “100% desacoplamento”, mas descreve arquitetura cujo motor ainda depende de dezenas/centenas de entradas declarativas derivadas por rota.

Durante esta implementação:

1. não apague o histórico;
2. marque claramente o que é legado/transição;
3. atualize a arquitetura canônica para o fluxo OpenAPI-first universal;
4. remova instruções que ensinem novos contributors a aumentar o registry.

---

# 6. ARQUITETURA ALVO OBRIGATÓRIA

O fluxo canônico deve convergir para:

```text
Mensagem do usuário
        ↓
preparação + contexto estruturado
        ↓
decomposição em subtarefas quando necessário
        ↓
actions permitidas ao agente
        ↓
retrieval híbrido top-K sobre Action Catalog
        ↓
planner estruturado escolhe action + propõe argumentos
        ↓
validador determinístico contra OpenAPI
        ↓
policy / sensitivity / confirmation
        ↓
executor HTTP genérico
        ↓
interpretação + apresentação schema-driven
        ↓
síntese da resposta
```

Ou, resumido:

```text
OpenAPI
→ Action Catalog
→ semantic document/index
→ allowed actions
→ hybrid retrieval
→ structured planner
→ OpenAPI validation
→ policy
→ generic executor
→ schema-driven presentation
```

---

# 7. RESPONSABILIDADE DE CADA CAMADA

## 7.1 OpenAPI importado

É a fonte técnica para:

- `operationId`;
- HTTP method;
- path;
- path params;
- query params;
- headers declarados;
- request body;
- required/optional;
- type;
- enum;
- format;
- response schema;
- security scheme;
- deprecation;
- summary/description/tags/examples quando disponíveis.

Não duplicar isso em JSON de assistant content.

---

## 7.2 Action Catalog

É a representação normalizada da operation importada.

Deve fornecer dados suficientes para seleção e execução sem consultar código do provider.

Confirme se o modelo atual precisa ser enriquecido. Qualquer migração deve respeitar compatibilidade e `contract-evolution-backward-compatibility.mdc`.

---

## 7.3 Documento semântico da Action

A indexação de cada action deve montar um documento semântico rico a partir do OpenAPI.

No mínimo considerar:

```text
provider name
operationId
method
path
summary
description
tags
parameter names
parameter descriptions
parameter types/enums
request body field names/descriptions
response schema field names/descriptions
examples úteis
sensitivity quando aplicável
```

O path pode contribuir como metadata técnica, mas não deve dominar o ranking sobre linguagem natural clara.

Exemplo conceitual:

```text
Action: get_product_structure_excel
Summary: Export product structure as Excel
Description: Generate/download a spreadsheet containing the product BOM/structure
Tags: products, structure, export
Parameters: code — product identifier
Response: binary Excel file
```

Isso deve diferenciar naturalmente a action de:

```text
get_product_structure
Summary: Get product structure
Response: hierarchical JSON
```

Sem:

```python
if "excel" in message:
    choose("structure-excel")
```

---

# 8. RETRIEVAL HÍBRIDO

Implemente ou consolide um único mecanismo de candidate retrieval.

Deve trabalhar somente sobre actions:

```text
importadas
+ enabled
+ vinculadas ao agente
+ permitidas pelo binding/override
```

A estratégia deve combinar, conforme stack existente:

```text
semantic/vector score
+ lexical score
+ metadata filtering
```

Pode usar BM25/trigram/FTS se já houver suporte adequado no stack, mas não introduza infraestrutura nova sem provar necessidade.

O retrieval deve retornar `top-K` com score/metadata observáveis.

### Requisitos

- não carregar todas as actions no prompt;
- não escolher provider por prefixo;
- não dar preferência implícita à `api-delpi`;
- não usar ordem de `allowed_action_ids` como substituto de inteligência semântica;
- usar ordem apenas como desempate determinístico final se realmente necessário e documentado;
- ações semanticamente parecidas devem chegar juntas ao planner;
- incluir score gap e evidência lexical/semântica na telemetria quando disponível.

---

# 9. PLANNER ESTRUTURADO

Após retrieval, não execute simplesmente o primeiro candidato.

Crie/reuse um planner estruturado que receba:

```text
mensagem/subtarefa
contexto relevante
candidatos top-K
descrição/schema mínimo necessário de cada candidato
estado multi-turno aplicável
```

E produza estrutura semelhante a:

```json
{
  "actionId": "provider.action",
  "operationId": "operation_id",
  "arguments": {},
  "confidence": 0.91,
  "reason": "user requested an Excel export of the product structure"
}
```

### Restrições

- planner escolhe somente entre candidates recebidos;
- nunca cria URL;
- nunca cria path;
- nunca cria operationId inexistente;
- nunca escolhe action fora de `allowed_action_ids`;
- nunca altera sensitivity/policy;
- nunca recebe secrets desnecessários;
- tool output não pode reescrever system/developer policy.

O `reason` é explicação curta operacional, não chain-of-thought.

---

# 10. VALIDAÇÃO DETERMINÍSTICA DOS ARGUMENTOS

Depois do planner, validar argumentos contra o OpenAPI real.

Criar/reusar responsabilidade equivalente a:

```text
OpenApiActionArgumentValidator
```

Retornos sugeridos:

```text
VALID
MISSING_REQUIRED_ARGUMENTS
INVALID_ARGUMENTS
AMBIGUOUS_ARGUMENTS
```

Validar no mínimo:

- required params;
- path params;
- query params;
- body;
- primitive types;
- arrays/objects;
- enums;
- formats suportados;
- propriedades desconhecidas quando schema restringir;
- coerência entre path template e parâmetros.

### Regra crítica

Se falta argumento obrigatório que não pode ser resolvido do contexto com segurança:

```text
PERGUNTAR AO USUÁRIO
```

Não inventar.

---

# 11. EXTRAÇÃO DE PARÂMETROS OPENAPI-FIRST

Migrar progressivamente a montagem de parâmetros de strategies específicas para schema-driven binding.

O código deve conseguir resolver genericamente:

```text
/products/{code}
?limit=20
?date=2026-09-08
body.customerId
body.items[]
```

Com base no schema da operation e na linguagem/contexto.

Strategies legadas podem continuar como compatibilidade temporária quando houver semântica empresarial que o OpenAPI padrão não expressa, mas:

1. devem ser documentadas como override/compatibility;
2. não podem ser requisito para provider externo;
3. não devem duplicar required/type/enum/path/query/body já descritos no OpenAPI;
4. devem possuir critério de remoção.

Extensões opcionais `x-delpi-ai` podem enriquecer o comportamento, porém **OpenAPI padrão deve funcionar sozinho**.

---

# 12. REQUEST DECOMPOSITION — FRASES LONGAS E MÚLTIPLOS PEDIDOS

O motor deve suportar mensagens como:

```text
"Veja a última compra do 10080001, compare com o preço atual,
mostre o histórico de orçamento e depois me diga se houve aumento."
```

Não reduzir isso a um único intent.

Implementar/reusar decomposição estruturada:

```text
request
→ subtasks
→ dependências entre subtasks
→ retrieval por subtask
→ plans
→ DAG simples de tools
→ execução paralela quando independente
→ síntese final
```

Exemplo:

```text
T1 last purchase ──┐
T2 current price ──┼→ compare
T3 budget history ─┘
```

### Regras

- não executar duplicatas equivalentes;
- preservar ordem semântica quando houver dependência;
- permitir paralelo para leituras independentes;
- writes/destructive continuam sujeitos a policy/confirmação;
- não ultrapassar budgets definidos em `ai-context-and-tool-budget.mdc`.

---

# 13. ESTADO MULTI-TURNO

Substituir dependências frágeis de substring/path por estado estruturado.

Manter, quando relevante:

```text
selectedProvider
selectedAction
operationId
resolvedEntities
resolvedArguments
lastToolResults
pagination
sort/grouping
metric
hierarchyDepth
timeRange
referenceDate
```

Exemplo:

```text
Usuário: "mostre a estrutura do 90261757"
Assistente: executa estrutura
Usuário: "agora exporte em excel"
```

O segundo turno deve entender que:

```text
entity = produto 90261757
domínio atual = estrutura
novo objetivo = exportar representação
```

E comparar candidates de export sem procurar `"/structure"` no último path.

---

# 14. DATAS E TEMPO

Há regressão conhecida em fixture que esperava data fixa histórica e hoje recebe a data atual.

Não corrija trocando uma data fixa por outra.

Introduza/reuse abstração de clock quando lógica depende de “hoje”, “ontem”, “último dia”, data de referência etc.

Testes devem poder injetar/fixar:

```text
current_date
current_datetime
timezone
```

Use timezone de negócio configurada, não `datetime.now()` espalhado.

Testes de linguagem temporal devem ser determinísticos.

---

# 15. SEGURANÇA E POLICY

Preservar integralmente:

- Keycloak/OIDC;
- JWT validado;
- RBAC;
- provider binding;
- `allowed_action_ids`;
- allowRead/allowWrite/allowAdmin;
- sensitivity;
- confirmação de write/admin/destructive;
- regras SSRF/egress;
- redaction de secrets;
- limites de response/schema/payload;
- redirects seguros;
- timeouts;
- política de retry/idempotência.

O novo planner **não** é um bypass de autorização.

Fluxo obrigatório:

```text
candidate allowed
→ planner
→ argument validation
→ policy recheck
→ confirmation se aplicável
→ executor
```

---

# 16. EXECUÇÃO HTTP

Preservar `ExecuteExternalActionUseCase` / gateway equivalente como caminho genérico.

Não criar:

```text
ApiDelpiProductClient
ThirdPartyXSpecialExecutor
if provider == "api-delpi"
```

no motor universal apenas para executar operations específicas.

A URL final deve ser construída somente a partir de:

```text
provider baseUrl aprovado
+ imported action path
+ validated arguments
```

Nunca a partir de URL livre gerada pelo LLM.

---

# 17. APRESENTAÇÃO

Não reintroduza apresentação por path.

A apresentação deve continuar seguindo:

```text
response schema
+ entity/dataShape
+ delivered metadata
+ presentation hints genéricos/opcionais
```

A correção recente de hierarchy é referência de princípio:

```text
hierarchy semantic signal
→ tree
```

Não:

```text
if "/parents" in path
if "/structure" in path
```

Uma API externa que declare/produza shape hierárquico deve ter comportamento equivalente.

---

# 18. MODELOS / PORTS RECOMENDADOS

Não crie abstrações duplicadas se equivalentes já existirem. Primeiro inventarie.

Se necessário, convergir para conceitos equivalentes a:

```text
ActionDescriptor
ActionCandidate
ActionPlan
ActionArgumentValidationResult
ToolExecutionPolicy
```

Ports equivalentes:

```text
ActionCatalogPort
ActionSemanticSearchPort
ActionPlannerPort
OpenApiValidatorPort
ExternalActionExecutorPort
```

### Clean Architecture

**domain**

- modelos/decisões puras;
- score/normalização sem acesso DB/HTTP.

**application**

- retrieval orchestration;
- planning orchestration;
- validation orchestration;
- policy/execution coordination.

**infrastructure/adapters**

- Postgres/pgvector;
- LLM planner adapter;
- HTTP client;
- provider/OpenAPI fetch.

Não importar Flask/SQLAlchemy/requests diretamente no domínio.

---

# 19. OBSERVABILIDADE OBRIGATÓRIA

Para cada decisão de action, gerar metadata suficiente para responder:

> Por que esta action foi escolhida em vez das demais candidates?

Sem registrar chain-of-thought.

Registrar, quando aplicável:

```text
requestId
conversationId
turnId
agentId
selectionMode
subtaskId
providerKey
candidateCount
candidateActionIds
retrievalSemanticScore
retrievalLexicalScore
selectedActionId
operationId
plannerConfidence
validationStatus
policyDecision
confirmationRequired
fallbackUsed
executionDurationMs
statusCode
toolCount
```

Nunca registrar:

```text
JWT
API key
senha
Authorization completo
cookie
system prompt completo
chain-of-thought
payload sensível integral
```

---

# 20. EVALS — PROIBIDO VALIDAR SÓ OS CASOS QUE MOTIVARAM A REFATORAÇÃO

Antes da primeira mudança, registrar baseline.

Depois comparar o mesmo corpus.

O corpus deve incluir no mínimo:

### A. Actions semanticamente próximas

```text
structure vs structure-excel
pricing vs price intelligence
purchases vs last purchase
purchases vs budget history
list vs detail
search vs get-by-id
summary vs export
```

### B. API externa fictícia

Crie fixture de provider que não use nomes/path da DELPI.

Exemplo conceitual:

```text
providerKey: acme-supply
operations:
  get_component
  get_component_cost
  get_component_cost_history
  export_component_cost_history
  get_component_dependencies
```

Perguntas devem selecionar corretamente por `summary/description/schema`, não por conhecimento prévio.

### C. Parâmetros

- path param;
- query required;
- query optional;
- enum;
- request body;
- array;
- missing required;
- argumento ambíguo.

### D. Multi-provider

Mesma semântica e/ou paths parecidos em providers diferentes.

Não usar prefix bias.

### E. Multi-turn

```text
"mostre o custo do componente A"
"agora o histórico"
"exporte"
```

### F. Compound requests

2, 3 e 5 subtasks.

### G. Negativos

- action não permitida;
- write sem confirmação;
- action inexistente;
- prompt injection em tool output;
- missing required param;
- score insuficiente/ambíguo.

---

# 21. MÉTRICAS DE QUALIDADE

Registrar baseline e resultado final de, no mínimo:

```text
action_top_k_recall
action_selection_accuracy
argument_extraction_accuracy
required_argument_accuracy
false_tool_call_rate
unnecessary_follow_up_rate
multi_request_completion_rate
tool_execution_success_rate
fallback_rate
planner_abstention_rate
latency p50/p95
tokens/context budget
```

A implementação não está concluída se melhorar apenas os casos DELPI e piorar o provider externo fictício.

---

# 22. BUDGET DE CONTEXTO E TOOLS

Não enviar ao planner:

```text
OpenAPI completo de todos providers
catálogo inteiro de actions
histórico completo da conversa
payload integral de todas as tools
```

Aplicar:

```text
allowed actions
→ retrieval top-K
→ somente schema/metadata das candidates
→ contexto multi-turno relevante
→ resultados necessários para a subtarefa
```

Definir limites configuráveis, com default conservador, para:

```text
retrieval top-K
planner candidates
parallel tool calls
history turns
RAG chunks
result bytes usados na síntese
```

Qualquer mudança desses limites deve ser avaliada por evals.

---

# 23. ESTRATÉGIA DE MIGRAÇÃO

Não faça big-bang.

Implementar por fases com paridade observável.

## Fase 0 — baseline e inventário

- mapear pipeline real;
- rodar suites atuais;
- registrar falhas atuais;
- medir seleção atual;
- classificar componentes como `CANONICAL`, `COMPATIBILITY`, `LEGACY`, `REMOVE`.

**Gate:** documento/evidência do pipeline e baseline reproduzível.

---

## Fase 1 — Action Semantic Document

- consolidar construção semântica de action;
- incluir summary/description/tags/params/body/response;
- reindexar fixtures necessárias;
- manter compatibilidade com registros atuais.

**Gate:** tests demonstrando diferenciação entre operations semelhantes sem path-specific rules.

---

## Fase 2 — Hybrid Candidate Retriever

- substituir path-marker discovery como caminho principal;
- filtrar governance antes do ranking;
- retornar top-K observável;
- manter fallback legado temporário atrás de flag/compatibility mode se necessário.

**Gate:** top-K recall do corpus ≥ baseline e API externa fictícia passando.

---

## Fase 3 — Structured Action Planner

- planner escolhe apenas top-K autorizado;
- saída estruturada validável;
- confidence/reason operacional;
- abstém quando ambíguo.

**Gate:** action selection accuracy melhora sem regressão significativa de false tool calls.

---

## Fase 4 — OpenAPI Argument Validator + Binder

- extrair/propor args;
- validar schema;
- missing required → pergunta;
- remover dependência de strategies técnicas redundantes.

**Gate:** suite path/query/body/enum/required/ambiguous passando.

---

## Fase 5 — Multi-turn structured state

- action/context por metadata estruturada;
- reduzir busca por path em histórico;
- manter continuidade de entities/args/timeRange/pagination.

**Gate:** follow-up corpus passando sem path fragment dependency.

---

## Fase 6 — Compound Request Planner

- decomposição;
- DAG;
- paralelismo seguro;
- síntese.

**Gate:** multi-request completion rate definido e aprovado.

---

## Fase 7 — Shadow mode

Rodar, quando possível:

```text
legacy selector
vs
new selector
```

Sem duplicar execução externa.

Comparar apenas decisão:

```text
legacyActionId
newActionId
scores
plannerConfidence
expected quando houver fixture
```

**Gate:** divergências classificadas; nenhuma regressão crítica sem explicação.

---

## Fase 8 — Canary

Ativar novo selector progressivamente por configuração/flag, não por provider hardcoded.

Exemplo conceitual:

```text
selectionMode = legacy | shadow | universal
```

Não criar `if provider == api-delpi` para canary.

**Gate:** métricas e erros dentro dos limites definidos.

---

## Fase 9 — remover duplicação técnica

Após paridade comprovada:

- deixar `operational_route_registry.json` apenas para compatibilidade realmente necessária;
- remover novas dependências de `pathMarkers`/`operationIdMarkers`;
- remover selectors per-endpoint/per-provider sem responsabilidade legítima;
- remover parameter strategies que apenas repetem OpenAPI;
- atualizar documentação.

**Gate:** provider externo nunca visto funciona sem entrada no registry.

---

# 24. REGISTRY — POLÍTICA DE REMOÇÃO

Não apagar o registry imediatamente se ainda houver consumidores reais.

Mas aplique esta regra:

```text
NOVA API / NOVA OPERATION
→ NÃO adicionar entrada ao registry para ensinar path/operação/parâmetro
```

Toda entrada existente deve ser classificável como:

```text
BUSINESS_OVERRIDE
COMPATIBILITY
LEGACY_PENDING_REMOVAL
```

Se a entrada apenas repete OpenAPI:

```text
TECHNICAL_DUPLICATION
→ migrar
→ testar
→ remover
```

O gate `LEGACY_REGISTRY_GROWTH` da Fase 3 deve continuar ativo.

---

# 25. DOCUMENTAÇÃO A ATUALIZAR NA MESMA ENTREGA

Atualize no mínimo:

```text
docs/api/04-actions-openapi.md
docs/roadmap/docie-desacoplamento-selecao-rotas-openapi.md
docs/architecture/chat-pre-llm-layers.md
docs/flows/04-operacional-e-apresentacao.md
docs/development/guia-desenvolvimento.md
```

### `04-actions-openapi.md`

Remover a instrução canônica de que toda nova GET precisa de entrada no registry.

Novo fluxo documentado:

```text
Provider OpenAPI
→ importar/indexar
→ vincular ao agente
→ permissions/policies
→ usar
```

Registry deve aparecer apenas como compatibilidade legada.

### DOCIE antigo

Não apagar histórico de fases anteriores.

Alterar status para refletir que o “100%” era referente ao desacoplamento de hardcode Python daquela etapa, não à arquitetura OpenAPI-first universal atual.

Adicionar link para este prompt/playbook e marcar evolução arquitetural posterior.

---

# 26. CI / GATES

Preservar e ampliar, quando necessário:

```text
Architecture Enforcement
Cursor Rules Governance
DOCIE lint
presentation path-if gate
unit/integration/eval suites
```

O CI deve impedir novos padrões como:

```python
if "/products/" in path:
if "factory-status" in path:
if action_id.startswith("api_delpi."):
```

E novas entradas no registry destinadas apenas a ensinar uma operation recém-importada.

Adicionar gate/fixture para provider OpenAPI externo fictício.

---

# 27. DÍVIDAS CONHECIDAS QUE NÃO DEVEM SER MASCARADAS

Durante a execução você pode encontrar falhas preexistentes.

Já foram observadas:

1. casos de seleção de actions específicas perdendo para genéricas;
2. fixture temporal dependente da data atual;
3. snapshot de apresentação com `sectionAvailabilityLineCount` desatualizado;
4. `plugins/minha-delpi-chat/package.json` e `package-lock.json` fora de sincronismo para React/ReactDOM.

Para cada uma:

```text
CAUSADA_PELA_MUDANCA
PREEXISTENTE_RELACIONADA
PREEXISTENTE_NAO_RELACIONADA
```

Não altere gate para esconder falha.

Não atualize snapshot apenas para ficar verde sem provar que o novo valor é correto.

Não misture correção de lockfile MFE com arquitetura de action selection sem necessidade; trate em mudança separada se não bloquear o objetivo.

---

# 28. TESTES DE ACEITE OBRIGATÓRIOS

A entrega final deve provar todos os cenários abaixo.

## 28.1 API externa desconhecida

Dado:

```text
OpenAPI válido de provider fictício
nenhum código do provider no monorepo
nenhuma entrada de registry
nenhum intent específico
nenhum presenter específico
```

Quando:

```text
importar
indexar
vincular ao agente
habilitar leitura
fazer pergunta em linguagem natural
```

Então:

```text
retrieval encontra candidates
planner escolhe operation correta
argumentos são resolvidos/solicitados
validator aprova
policy aprova
executor genérico recebe action válida
resposta é interpretada/apresentada
```

---

## 28.2 Operations muito parecidas

Provider com:

```text
get_component_cost
get_component_cost_history
export_component_cost_history
```

Perguntas:

```text
"qual o custo atual do componente X?"
"mostre o histórico do custo do componente X"
"baixe esse histórico em planilha"
```

Cada uma deve selecionar a operation semanticamente correta sem path rule.

---

## 28.3 Missing required

Se operation exige `componentId` e o usuário pergunta apenas:

```text
"mostre o histórico de custo"
```

Resultado esperado:

```text
não executar
→ solicitar componentId/contexto necessário
```

---

## 28.4 Write

Operation `POST` autorizada mas com confirmação obrigatória:

```text
planner seleciona
validator valida
policy exige confirmação
HTTP ainda NÃO executa
```

---

## 28.5 Provider não autorizado

Mesmo com alto semantic score:

```text
action fora de allowed_action_ids
→ nunca chega ao planner ou nunca pode ser selecionada
```

---

## 28.6 Compound

Mensagem com três pedidos independentes:

```text
→ três subtasks
→ candidates próprios
→ execução paralela se read-only e independente
→ resposta única sintetizada
```

---

## 28.7 Multi-turn

```text
Turno 1: detalhe
Turno 2: histórico
Turno 3: exportar
```

Preservar entidade e contexto sem path substring.

---

# 29. CRITÉRIO FINAL DE ACEITE ARQUITETURAL

A implementação somente pode ser declarada concluída quando esta frase for verdadeira:

> Uma API OpenAPI de terceiro que o Minha DELPI nunca viu pode ser importada, indexada, vinculada a um agente e utilizada em linguagem natural — inclusive para distinguir operations semelhantes e resolver argumentos — sem adicionar código específico do provider, path markers, operation markers, intent por endpoint, parameter strategy técnica obrigatória, registry por rota ou presenter obrigatório.

Fluxo final esperado:

```text
OpenAPI desconhecido
→ import
→ Action Catalog
→ semantic index
→ agent binding
→ allowed actions
→ request decomposition
→ hybrid retrieval
→ structured planner
→ OpenAPI argument validation
→ policy/confirmation
→ generic HTTP execution
→ schema-driven interpretation/presentation
→ answer
```

---

# 30. PROIBIÇÕES ABSOLUTAS

Não aceite como solução:

```text
adicionar palavras "excel", "ICMS", "última compra" em if Python específico
adicionar pathMarker novo para cada teste
adicionar operationIdMarker novo para cada operation
criar selector por provider
criar selector por endpoint
ordenar api-delpi antes de api externa
usar actionId prefix como score
mover hardcode de Python para JSON técnico
ensinar parameters duplicando o OpenAPI
executar URL inventada pelo LLM
pular allowed_action_ids
pular policy/confirmation
inventar required argument
mandar catálogo inteiro ao LLM
marcar teste como xfail para concluir fase
reduzir gate para ocultar regressão
```

---

# 31. FORMATO DE EXECUÇÃO E RELATÓRIO DO CURSOR

Antes de implementar, entregue uma seção curta:

```text
DIAGNÓSTICO CONFIRMADO
ARQUITETURA ATUAL
ACOPLAMENTOS REMANESCENTES
ARQUITETURA ALVO
PLANO POR FASE
TESTES/GATES
RISCOS/ROLLBACK
```

Depois execute fase a fase.

Ao final de cada fase, reporte:

```text
FASE
arquivos alterados
arquitetura introduzida/removida
testes executados
resultado antes/depois
dívida remanescente
rollback
```

Na conclusão, responda explicitamente:

```text
API_EXTERNA_SEM_REGISTRY: SIM|NÃO
SELECAO_OPERACOES_SEMELHANTES: SIM|NÃO
PARAMETROS_OPENAPI_FIRST: SIM|NÃO
MULTI_TURNO_ESTRUTURADO: SIM|NÃO
COMPOUND_REQUESTS: SIM|NÃO
POLICY_PRESERVADA: SIM|NÃO
LEGACY_REGISTRY_NOVAS_ROTAS: ZERO|NÃO_ZERO
ARCHITECTURE_ENFORCEMENT: PASS|FAIL
EVALS: PASS|FAIL
```

Se algum item for `NÃO`/`FAIL`, não declare a refatoração concluída.

---

# 32. PRINCÍPIO FINAL

A inteligência do Minha DELPI AI não deve vir de conhecer previamente cada endpoint da DELPI.

Ela deve vir de:

```text
contrato OpenAPI rico
+ catálogo bem indexado
+ retrieval de qualidade
+ planner restrito e estruturado
+ validação determinística
+ contexto multi-turno
+ políticas seguras
+ evals de generalização
```

Quando uma nova API precisar de código central para “ensinar” cada route ao chat, a arquitetura ainda não atingiu o objetivo.

---

> Fim do prompt executivo.
