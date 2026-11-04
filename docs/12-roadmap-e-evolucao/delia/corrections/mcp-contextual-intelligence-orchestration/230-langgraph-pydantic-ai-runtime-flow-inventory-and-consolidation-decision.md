# 230 — DÉLIA · Inventário executivo dos fluxos LangGraph × Pydantic AI × Orquestração Application

**TASK_ID:** DELIA-C3-FRAMEWORK-OVERLAP-RUNTIME-FLOW-INVENTORY-01  
**STATUS:** TEMPLATE_FOR_CURSOR — TO_INVENTORY (não preencher por inferência)  
**CREATED:** 2026-11-04  
**REFERENCE:** doc 229 (auditoria sistêmica), doc 226 (semantic once), doc 228 §§12–20, execution ledger  
**SCOPE:** INVENTÁRIO COMPLETO EM UMA ÚNICA ITERAÇÃO — ZERO ALTERAÇÃO PRODUTIVA  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**PRODUCT_CODE_CHANGES:** NOT_AUTHORIZED  
**DECISION AUTHORITY:** Coordenação DÉLIA, após evidência produzida neste documento.

> **Missão do Cursor:** preencher INTEGRALMENTE este documento, no mesmo arquivo, em uma única execução abrangente. Não produzir uma sequência de pequenos prompts ou inventários parciais. Ao final, commit/push da versão preenchida na main e relatório de evidências. Não implementar nenhuma simplificação, desinstalar frameworks, mudar prompts, contratos, migrações, deployments ou ownership.

## 0. Reancoragem obrigatória e protocolo

Começar com HEAD/status, origin/main e Project Instructions/.cursor. Ler na ordem canônica 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger. Ler ainda 226, 228 e 229; verificar ADR 58, decisões sobre LangGraph, Pydantic AI, runtime, admission e orquestração.

Não assumir que os nomes em doc 229 representam o runtime real no HEAD atual; revalidar no código. Resolver divergências por hierarquia de autoridade, sinalizando drift, jamais reconciliando silenciosamente.

**Preencher:**
- BASE_HEAD: TO_INVENTORY
- HEAD/ORIGIN_MAIN at review: TO_INVENTORY
- GIT_STATUS (tracked/untracked/concurrent work): TO_INVENTORY
- AUTHORITIES_READ (paths + seções/SHAs): TO_INVENTORY
- THEMATIC_SPECS/ADRs/DECISIONS: TO_INVENTORY
- PHASE/CP/RQ according to doc 16+ledger: TO_INVENTORY
- DOC229_FINDINGS_REVALIDATED: TO_INVENTORY
- EXISTING_EQUIVALENT: TO_INVENTORY
- REUSE_DECISION: TO_INVENTORY
- EXECUTION_DRIFT: TO_INVENTORY

**Evidência e classificação:** PROVEN = arquivo:função:linha + contrato/consumer + execução ou teste quando necessário; PARTIALLY_PROVEN = parte validada e lacuna identificada; TO_INVENTORY = não verificado; INCONCLUSIVE = insuficiente; NOT_USED = ausência demonstrada por busca residual + grafo de consumers (mera busca zero não prova ausência); TEST_NOT_RUN = execução não realizada. Não classificar README/documentação como prova de uso no runtime. A mera importação de framework não prova necessidade operacional.

## 1. Pergunta decisória central

**LangGraph e Pydantic AI exercem responsabilidades complementares na DÉLIA ou existe sequenciamento/planejamento/admission/retry/estado duplicado entre eles e o orquestrador Application?**

O objetivo NÃO é escolher um framework por preferência. O resultado deve determinar, por responsabilidade e por fluxo, se cada mecanismo é **KEEP / CONSOLIDATE / REMOVE_CANDIDATE / TO_INVENTORY**, com prova, risco de remoção, consumidores, substituto existente e teste de equivalência. Diferenciar:
1. biblioteca importada vs chamada ativa;
2. engine ativo vs engine configurado porém não usado;
3. execução sequencial vs dupla execução;
4. propósito semântico LLM vs transporte/validação tipada;
5. estado de workflow vs estado de sessão/turno vs evidência;
6. retomada durável vs retry em memória;
7. reflexão ou proposta do modelo vs autorização/decisão determinística.

## 2. Escopo integral — pesquisa de uso e consumers

Inspecionar obrigatoriamente:
- manifests/lockfiles e versões instaladas de langgraph, langchain, pydantic-ai, pydantic, opentelemetry e eventuais wrappers;
- bootstrap/DI/factory/config/env/feature flags que escolhem engines e providers;
- entrypoints de HTTP/NDJSON, eventos, jobs e quaisquer surfaces que acionem o engine;
- HandleInteractiveConversationTurn e call graph de OperationalCapabilityOrchestrator;
- app.infrastructure.orchestration.langgraph_engine e seus nós/arestas/compilações (confirmar nomes no HEAD);
- portas/adapters Pydantic AI, _propose e contratos de saída estruturada;
- interaction admission, turn_goal, decomposition, acquisition filter, owner/group/capability selection, arguments, discovery/candidate binding, owner invocation, assessment, evidence composition, grounding e presentation;
- SubObjectiveTracker, prior continuation, snapshots/checkpoints e timeouts/retries;
- tests e todos os consumers dos símbolos/arquivos, inclusive possíveis apps não conversacionais.

**Busca residual obrigatória:** símbolos, instanciações, métodos invoke/ainvoke/stream, StateGraph/CompiledGraph/checkpointer/store/nodes/edges, Agent/run/run_sync/Tool/Deps/ModelRetry, _propose, admission, sequence engine, flags de rollout. Se um framework tem imports mas nenhum consumer runtime, diferenciar dead code de estratégia prevista.

## 3. Inventário de fluxos concretos (PREENCHER TODOS)

Um flow começa em entrypoint real e termina em outcome/client/worker. Expandir ou reduzir nomes conforme código e indicar fluxo NÃO EXISTENTE quando demonstrado.

| FLOW_ID | Entrada real / gatilho | Seleção de runtime/flag | Sequencer efetivo | LangGraph etapas | Pydantic AI etapas | Orquestrador Application etapas | Estado/checkpoint | Consumers | Outcome | Evidência (path:lines) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F01 | Interaction HTTP JSON | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F02 | Interaction HTTP NDJSON | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F03 | Conversational admission/answer | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F04 | Live owner surface inquiry | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F05 | Single-owner READ | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F06 | Multi-evidence compare | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F07 | Discover→candidate→execute | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F08 | Continuity/refinement follow-up | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F09 | Failure/retry/timeout/cancel | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F10 | Scheduled/event/Watch/Work/background (if live) | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| F11+ | Outras entradas/engines/flags encontradas | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |

**Para cada fluxo ativo:** adicionar abaixo um call chain concreto com nomes de funções, ordem das chamadas, limites de transação, estado lido/escrito, LLM call sites, chamadas MCP/HTTP e ponte exata entre os frameworks. Provar se duas mensagens de log "interaction_admission" significam duas invocações ou apenas duas camadas logando o mesmo evento. Usar correlation IDs existentes, nunca atribuir duplicação por log sem call chain.

## 4. Matriz de responsabilidades / sobreposições

| Responsabilidade | LangGraph: realiza? como? | Pydantic AI: realiza? como? | Application: realiza? como? | Owner canônico | Mesmo input decidido >1x? | Dependência legítima? | Evidência | KEEP / CONSOLIDATE / REMOVE_CANDIDATE |
|---|---|---|---|---|---|---|---|---|
| Admission | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Intent + typed goal | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Decomposition / planning | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Subgoal classification | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Owner/group selection | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Capability selection | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Tool schema / arguments | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| MCP discover / candidate binding | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Execution orchestration | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Retry / error propagation / deadlines | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| State / checkpoints / resume / HITL | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Policy / AuthZ / write gates | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | Core/Domain/DÉLIA boundaries | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Evidence / provenance / grounding | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | DÉLIA Evidence + Domain truth | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Synthesis / output projection | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Streaming / NDJSON delivery | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Observability / telemetry | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |

**Conceitos a verificar:** LangGraph pode apenas sequenciar nós e Pydantic AI pode apenas chamar/validar LLM sem duplicação. Prove ou refute. Diferenciar dois wrappers no call stack de dois planners ativos. Auditar checkpoints e durabilidade real (store/config/runtime), não apenas APIs disponíveis na biblioteca.

## 5. Inventário de uso real por framework

### 5A. LangGraph

- Package/version/pins e onde instalado: TO_INVENTORY
- Files with imports (lista completa): TO_INVENTORY
- Runtime builders/factories/config selectors: TO_INVENTORY
- Nós e suas responsabilidades: TO_INVENTORY
- Arestas/condicionais/loops: TO_INVENTORY
- Entradas/saídas e consumer concreto: TO_INVENTORY
- StateGraph/CompiledGraph realmente chamados? TO_INVENTORY
- Checkpointer persistente? tecnologia, namespace, owner, restore path, consumidores: TO_INVENTORY
- Store/memory realmente usado? TO_INVENTORY
- Interrupt/resume/HITL? gate real: TO_INVENTORY
- Retry/durability/fan-out? TO_INVENTORY
- Admission duplicada? mesmo call, segunda chamada, ou log repetido: TO_INVENTORY
- Exclusividades que o Application atual não oferece: TO_INVENTORY
- Fluxos cuja retirada quebraria contrato/outcome: TO_INVENTORY
- Configuração presente mas sem call graph consumidor: TO_INVENTORY

### 5B. Pydantic AI

- Package/version/pins: TO_INVENTORY
- Files with imports (lista completa): TO_INVENTORY
- Onde são instanciados Agents/ports/Deps/Models: TO_INVENTORY
- Agentes efetivamente usados vs definidos: TO_INVENTORY
- Chamadas run/run_sync/stream e consumers: TO_INVENTORY
- Tool calls nativas Pydantic AI realmente usadas, ou apenas structured proposals: TO_INVENTORY
- Output validators/retries e interação com retries próprios: TO_INVENTORY
- Esquemas e validações reaproveitados: TO_INVENTORY
- Provider SDK/auth/credentials boundary: TO_INVENTORY
- Que estado guarda entre etapas (se houver): TO_INVENTORY
- O que é um wrapper fino sobre LLM vs agent com tool loop: TO_INVENTORY
- Uso efetivo de tracing/instrumentation: TO_INVENTORY
- Fluxos que dependem de features exclusivas: TO_INVENTORY

### 5C. Orquestrador Application

- Entrypoints: TO_INVENTORY
- Decomposição, select, arguments, candidate, owner read, composition: TO_INVENTORY
- Quem decide fluxo/transition e quem só invoca modelo: TO_INVENTORY
- Estado/retentativas/timeouts: TO_INVENTORY
- Sobreposições comprovadas com LangGraph/Pydantic AI: TO_INVENTORY
- Complexity candidates vs security-critical guards: TO_INVENTORY
- Owner/consumer e port boundaries: TO_INVENTORY

## 6. Call sites de LLM e medição

Preencher **uma linha por call site ativo** (não só por instruction ID); relacionar instruction purpose, path, trigger, retries, tokens/latência se disponíveis, fallback e repeated semantics.

| ID | Path:função:linhas | Flow | Framework executor | Instruction/model | Trigger | Output schema | Retry owner | Invocações observadas | Duplica informação anterior? | Tokens/latência reais | Evidência |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L001… | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | NOT_MEASURED | TO_INVENTORY |

Referência doc 229: ~20 instruções e ~26 _propose sites são contagens anteriores, **recontar no HEAD e diferenciar site estático, chamadas dinâmicas e retries**.

Para cada fluxo significativo: número de LLM calls até primeira READ, até evidência verificada e até terminal. Se não houver traces confiáveis, marcar NOT_MEASURED, não estimar tokens como medidos.

## 7. Estado, side effects, ownership e fluxo de falhas

Para todos os mecanismos que parecem sequenciar:
- Estado inicial/mutações/consumers/cleanup e isolamento entre turnos; checkpoint vs in-memory.
- Retries por camada (Pydantic AI, Application, LangGraph, transport); limite cumulativo, idempotência e cancelamento.
- Token/candidate state e discover→execute; distinguir mecânica de provider e decisão semântica.
- AuthN Keycloak, AuthZ Core live, Domain authority, Policy/Decision; nenhum framework é autoridade.
- Trusted sources vs model/metadata untrusted; nenhuma alteração de grounding sem Evidence.
- Fallback free form, owner-path-unbound, non-grounded e client projection.
- Duplicação de estado e risco de divergência.
- Persistência/publish de estado se houver: não inventar.

Produzir 3 traces **anotados** (ou prova TEST_NOT_RUN e replay de logs anteriores):
A) pergunta simples "O que é SIPOC?"; B) single READ 90260147; C) comparação 90260147 × 90260148. Um quarto trace D) candidate-bound discovery/execute se disponível. Não executar writes. Informar HASH de código/model/config de cada trace. Não confundir bind mount com deploy imutável.

## 8. Prova de duplicação e critérios de descarte

Para cada suspeita DUPLICATE:
1. Mostrar dois paths/owners e a mesma responsabilidade semântica/operacional.
2. Provar que ambos são executados no MESMO tipo de request, ou que um é caminho alternativo legítimo.
3. Demonstrar que outputs, contracts e consumers se sobrepõem.
4. Identificar quem é a autoridade legítima segundo docs canônicos.
5. Demonstrar dependências e impactos se consolidar.
6. Definir teste de equivalência operacional e segurança (sem executá-lo se exigir mudança).
7. Concluir DUPLICATE_PROVEN / COMPLEMENTARY_PROVEN / PARTIAL / INCONCLUSIVE.

**Remoção nunca aprovada apenas por não aparecer em um trace.** Usar matriz de consumidores, configurações de produção/homologação, flags e usos futuros documentados sem tratar PLANNED como PROVEN.

## 9. Matriz final de decisão (PREENCHIMENTO OBRIGATÓRIO)

| Mecanismo / fluxo | Necessidade legítima demonstrada? | Equivalente existente? | Consumers reais | Dependência exclusiva? | Risco de retirada | Decisão proposta | Evidência | Teste de equivalência |
|---|---|---|---|---|---|---|---|---|
| LangGraph runtime engine | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Pydantic AI model/agent adapter | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Application orchestrator | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Admission (todos os caminhos) | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Retry/deadline mechanisms | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| State/checkpoint/continuity | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |
| Decompose/classify/select | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY | TO_INVENTORY |

**Recomendação final obrigatória:**
- LangGraph: KEEP | CONSOLIDATE | REMOVE_CANDIDATE | INCONCLUSIVE — motivo + proof links.
- Pydantic AI: KEEP | CONSOLIDATE | REMOVE_CANDIDATE | INCONCLUSIVE — motivo + proof links.
- Application orchestrator: KEEP | CONSOLIDATE | REMOVE_CANDIDATE | INCONCLUSIVE — motivo + proof links.
- Quantas responsabilidades duplicadas PROVEN? TO_INVENTORY
- Quais funções exclusivas devem permanecer? TO_INVENTORY
- Qual é o menor caminho de simplificação sem criar arquitetura nova? TO_INVENTORY
- Há decisão canônica congelada que exige ADR? TO_INVENTORY
- Risco principal / fallback: TO_INVENTORY
- Ordem de alterações sugerida (máx. 3 passos bounded, sem implementar): TO_INVENTORY

## 10. Qualidade / prevenção contra nova rodada

**Cursor deve preencher tudo em uma única iteração.** Não encerrar com "preciso inventariar X depois" para code paths acessíveis no mesmo repo. Se algum dado não puder ser obtido, informar o bloqueio real, comando/consulta executado e efeito sobre a decisão. Não fabricar traces, tokens ou ambiente.

O documento preenchido deve conter:
- links exatos GitHub SHA/permalinks path#Lx-Ly para todos os findings centrais;
- lista de todos os fluxos e consumers; as entradas irrelevantes justificadas;
- evidência de execução quando duplicação for afirmada;
- contraprovas e casos negativos;
- nenhuma tabela central contendo TO_INVENTORY sem motivo concreto;
- recomendações com um único owner por responsabilidade, sem alterar autoridade;
- nenhuma proposta de novo framework;
- nenhuma nova engine, registry, store ou abstraction por conveniência;
- apreciação de risco sobre RC-A obligations, RC-B selection, RC-C discovery e REF05;
- separação DÉLIA de Minha DELPI Chat, que é apenas referência.

Os arquivos do inventário podem ser lidos e pesquisados livremente; apenas este documento e, se autorizado por protocolo, uma linha factual no ledger devem ser alterados. Evitar tocar arquivos já staged por outro trabalho: fazer staging explícito somente de paths deste task, inspecionar git diff --cached antes de commit, preservar concorrência e nunca usar git add -A. Corrigir o problema do commit 9bf8d1f5cc (arquivos plugin-ui/tv-dashboard no index) **procedimentalmente**, não reescrever histórico.

## 11. Gate de saída e relatório

**AC-01** reanchor conforme hierarquia; **AC-02** mapa completo de entradas/consumers; **AC-03** fluxos F01–F10 preenchidos e variações; **AC-04** mapa real LangGraph/Pydantic/Application; **AC-05** execução vs import provada; **AC-06** pontos duplicados PROVEN ou INCONCLUSIVE bem delimitados; **AC-07** call sites LLM e retries; **AC-08** estado/checkpoint/continuity; **AC-09** AuthZ/Evidence trust gates preservados; **AC-10** matrix final KEEP/CONSOLIDATE/REMOVE_CANDIDATE; **AC-11** 3 traces ou lacunas comprovadas; **AC-12** nenhuma implementação produtiva; **AC-13** documento/ledger e commit/push rastreáveis; **AC-14** ações futuras ≤3 bounded com testes de equivalência; **AC-15** nenhuma mudança de fase.

Relatório final:

~~~text
DÉLIA FRAMEWORK FLOW INVENTORY REPORT
TASK_ID:
BASE_HEAD:
FINAL_HEAD:
ORIGIN_MAIN:
PUSH_VERIFIED:
AUTHORITY_REANCHOR:
CP_RQ:
DOC_PATH:
FLOW_COUNT:
LANGGRAPH_ACTIVE_FLOWS:
PYDANTIC_AI_ACTIVE_FLOWS:
APPLICATION_ACTIVE_FLOWS:
LANGGRAPH_EXCLUSIVE_FUNCTIONS:
PYDANTIC_AI_EXCLUSIVE_FUNCTIONS:
DUPLICATIONS_PROVEN:
COMPLEMENTARITIES_PROVEN:
SUSPECTED_BUT_UNPROVEN:
LLM_ACTIVE_CALL_SITES:
RETRY_LAYER_COUNT:
CHECKPOINT_DURABILITY_EVIDENCE:
RUNTIME_TRACES:
TOKEN_USAGE:
STATE_OWNERS:
AUTHZ_AND_EVIDENCE_GATES:
EXISTING_EQUIVALENT:
REUSE_DECISION:
LANGGRAPH_RECOMMENDATION:
PYDANTIC_AI_RECOMMENDATION:
APPLICATION_RECOMMENDATION:
MINIMAL_CONSOLIDATION_PATH:
TEST_OF_EQUIVALENCE_REQUIRED:
ARCHITECTURE_DECISION_REQUIRED:
EXECUTION_DRIFT:
INCONCLUSIVE_ITEMS_WITH_REASON:
FILES_CHANGED:
PRODUCT_CODE_CHANGED: NO
PRODUCTION_DEPLOY: NOT_AUTHORIZED
NEXT_BOUND_STEP:
~~~

**PARADA:** Não avançar para implementação. Submeter este documento preenchido à coordenação. Só assim decidir se manter, consolidar ou remover um dos frameworks. Não recomendar substituição com base em preferência tecnológica.
