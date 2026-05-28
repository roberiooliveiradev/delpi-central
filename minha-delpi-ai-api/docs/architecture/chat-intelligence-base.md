# Arquitetura — Inteligência no chat base

**Status:** vigente (maio/2026)  
**Público:** desenvolvimento `minha-delpi-ai-api`, plugin `minha-delpi-chat`, gestão de agentes

---

## Princípio

O **chat** é onde a inteligência transversal evolui. **Agentes** são instâncias de chat com mais habilidades, contextos e actions — não um motor paralelo.

| Conceito | Papel |
|----------|--------|
| **Chat (sessão)** | Pipeline de mensagens, histórico, tools, RAG, LLM |
| **Agente** | `system_prompt`, skills, actions permitidas, especialização de conhecimento |
| **Projeto** | Prompt de projeto, agente padrão, agrupamento de sessões |
| **Simulação / admin** | Mesmo pipeline, com rascunho ou sandbox |

Melhorias de inteligência (comparação, insights, fast path operacional, resposta direta, contexto de ferramentas no histórico) devem ser implementadas na **camada base** e **herdadas** automaticamente por agentes, projetos e demais consumidores.

---

## Pipeline base

```text
Mensagem do usuário
  → Segurança (input)
  → ChatWorkspaceContextService (projeto + agente + capabilities)
  → ChatIntelligencePipelineService
        · decisão operacional / análise
        · contexto de conversa (incl. previews de tools no histórico)
  → ChatToolContextService (seleção e execução de tools/actions)
        · finalize: modo análise, supressão de direct answer
  → RAG (escopo agente/projeto/anexos)
  → ChatPromptBuilderService + prompt_policies
  → LLM (stream ou send)
```

**Camadas antes do LLM (modelo completo, short-circuit, implementação por fases):** [`chat-pre-llm-layers.md`](./chat-pre-llm-layers.md).

### Serviços centrais

| Serviço | Função |
|---------|--------|
| `ChatIntelligencePipelineService` | Orquestra decisões pré/pós-tools compartilhadas |
| `ChatConversationContextService` | Texto de histórico + dados de `toolCalls` em metadata |
| `ChatAnalysisIntentService` | Detecção de comparação / insights |
| `ChatCanvasIntentService` | Pedido de enviar conteúdo à lousa (não confunde com Canva.com) |
| `ChatCanvasContentService` | Monta markdown da última resposta assistant + confirmação |
| `ChatToolContextService` | Execução de tools; aceita `previous_messages` para herdar análise |
| `ChatExternalActionOrchestrationService` | Planeja várias actions OpenAPI (ex.: dois códigos de produto) |
| `ChatCompositeDirectAnswerService` | Monta resposta direta única com sucesso/erro por consulta |
| `ChatOperationalPipelineService` | Fast path operacional (desligado em modo análise) |
| `ExternalActionSelectionService` | Roteamento OpenAPI (não dispara consulta em pedido analítico nem em pedido de lousa) |
| `ChatDepartmentKpiIntentService` | KPIs departamentais (`/commercial`, `/financial`, `/production`, `/hr`, `/quality`, `/system`) |
| `ChatOperationalParameterService` | Consultas operacionais sem parâmetro (código de produto, etc.) |
| `ChatOperationalRefinementService` | Follow-up de estoque (filial/armazém) reutilizando código do histórico |
| `ChatCapabilitiesService` | Perguntas «consegue…?» / capacidades sem chamar API à toa |
| `ChatMessageNormalizationService` | Typos comuns (ebita→ebitda, kaisen→kaizen, coonsegue→consegue, …) |
| `ChatStructureComparisonOrchestrationService` | Comparação de estruturas com fetch multi-produto |
| `PromptPolicyService` | Policies globais (`operational-agent.md`, `chat-analysis-insights.md`, …) |

Use cases (`SendChatMessageUseCase`, `StreamChatMessageUseCase`, `AdminAgentSimulateUseCase`) **não** devem acumular regras de inteligência — apenas passam histórico e flags ao pipeline.

A preparação compartilhada do turno (tools, RAG, flags `skipRag` / `fastPath`) está em **`ChatTurnPreparationService`** (`app/application/services/chat_turn/chat_turn_preparation_service.py`), usada por send e stream.

### Identidade do assistente (maio/2026)

Perguntas como «quem é você», «quem te criou», «o que você é» (não confundir com «quem sou eu» / perfil do usuário):

| Etapa | Comportamento |
|-------|----------------|
| Classificação | `ChatAssistantIdentityService.is_assistant_identity_question` / `classify` (categorias: `who`, `origin`, `role`, `what`, `limits`, `usage`) |
| Resposta | **`build_direct_answer`** (texto em `identity.json`) quando `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED=true` (default) — **sem RAG nem LLM** (latência baixa em CPU) |
| Desligar atalho | `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED=false` — volta RAG + LLM + policy `chat-assistant-identity.md` |
| RAG (modo legado) | `build_rag_query`, `RAG_IDENTITY_QUESTION_MIN_SCORE`, filtro `is_identity_relevant_chunk` (rejeita `Normas_Tecnicas_*` mesmo com “DELPI” no trecho) |

Com o atalho ativo, perguntas como «quem te criou?» não montam prompt com perfil RBAC completo nem chamam o Ollama.

**Skill `company-knowledge`:** necessária para incluir documentos globais no escopo RAG. Agentes sem skill explícita herdam o default quando `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL=true`.

**Validação rápida:**

```bash
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python scripts/smoke_identity_rag.py <user_id> <session_id> "quem te criou?"
```

Testes: `test_chat_turn_preparation_identity_rag.py`, `test_chat_assistant_identity_rag_filter.py`, `test_chat_assistant_identity_stream_and_send.py`, `test_chat_admin_debug_service.py`.

---

## O que o agente adiciona (e só isso)

1. **Prompt** — personalidade e instruções (`system_prompt`).
2. **Skills** — policies extras (`metadata.skills`).
3. **Actions** — subset de rotas OpenAPI (`allowedActionIds` / providers).
4. **RAG** — filtros de especialização (tags, categorias, namespaces).
5. **Limites** — `max_tool_calls`, confirmação de escrita, capabilities.

O agente **não substitui** detecção de intenção, pipeline operacional ou modo análise comparativa.

**Base global de conhecimento:** agentes sem skill explícita `company-knowledge` herdam `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL` (documentos como `O_ARQUITETO_DO_CODIGO.md`).

---

## Roteamento automático (api-delpi)

O `ExternalActionSelectionService` resolve a action **antes** do LLM quando o fast path operacional está ativo. Ordem resumida:

1. Pedidos de **comparação/insights** → sem action (modo análise).
2. **OV / LMP / Transforma Mais / metadados Protheus** (tabelas/colunas).
3. **Suprimentos** (CPV, OTD, giro, valor total de estoque) — sem código de produto.
4. **Produto por código** (estoque, estrutura, pais, descrição, …) por intent.
5. **Busca por grupo ou descrição** → `GET /products/search` (prioridade sobre analyser quando há «grupo X»).
6. **KPI departamental** via `ChatDepartmentKpiIntentService`.
7. Fallback semântico (se ranker configurado) — **bloqueado** quando a intenção é produto (estoque/estrutura/etc.) **sem código** (`ChatOperationalParameterService`).

### Parâmetro obrigatório (estoque sem código) — maio/2026

Perguntas como «estoque do produto» (sem código) **não** disparam API nem loop agentic:

| Etapa | Comportamento |
|-------|----------------|
| `ChatOperationalParameterService` | Detecta intent STOCK/STRUCTURE/PARENTS/DESCRIPTION sem código |
| `ChatTurnPreparationService` | `direct_answer` canônico (`operational_parameters.json`), `skip_rag`, **sem** `build_tool_context` |
| `ExternalActionSelectionService` | Retorna `None` (evita fallback semântico → ROL comercial) |
| `ChatAgenticToolLoopService` | Não executa se `should_skip_agentic_loop` |

Com código (`10080099`), o fluxo normal seleciona `GET /products/{code}/stock`.

### Loop agentic e router LLM — defaults conservadores

| Variável | Default | Motivo |
|----------|---------|--------|
| `CHAT_AGENTIC_LOOP_ENABLED` | `false` | Evita 2ª/3ª inferência e disparo de actions irrelevantes (ex. KPIs ROL) |
| `CHAT_TOOL_ROUTER_ENABLED` | `false` | Roteamento determinístico (`ExternalActionSelectionService`) já cobre o caso |
| `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` | `12` | Quando agentic ligado, catálogo vem de `find_candidate_actions`, não `allowedActionIds[:10]` |

Habilitar agentic/router só em sandbox ou com agente com **poucas** actions bem descritas.

### Multi-action e histórico (maio/2026)

`ChatAnalysisIntentService.extract_product_codes_for_action_planning` planeja consultas paralelas **somente** com códigos da mensagem atual. Se o usuário já informou um código («estoque do produto 10080099»), códigos citados só no histórico **não** disparam N chamadas. Follow-ups («estoque desse produto») continuam resolvendo **um** código via contexto.

`CHAT_OPERATIONAL_SLIM_USER_CONTEXT` (default `true`): em modo operacional, o prompt LLM não inclui o bloco completo de perfil RBAC (reduz tokens), exceto perguntas sobre o **usuário** («quem sou eu»).

### Refinamento operacional (follow-up de estoque) — maio/2026

Após uma consulta de estoque bem-sucedida, mensagens como «filtre filial 02» ou «somente armazém 99»:

| Etapa | Comportamento |
|-------|----------------|
| `ChatOperationalRefinementService` | Detecta refinamento; recupera código do produto do histórico; extrai filial/armazém |
| `ExternalActionSelectionService` | Reexecuta `get_product_stock` com `branch`/`warehouse` nos parâmetros |
| `ChatIntelligencePipelineService` | Liga `operational_optimize` e `skip_rag` mesmo sem código na mensagem atual |

Evita RAG irrelevante (ex. anexo SQL) e mantém o contexto da conversa em vez de tratar o follow-up como pergunta nova.

### Regras críticas (produtos)

| Situação | Rota correta | Erro comum |
|----------|--------------|------------|
| «Busque 3 produtos do **grupo 1008**» | `GET /products/search` + `group_code=1008`, `page_size=3` | Tratar `1008` como `{code}` no `/analyser` |
| «Resumo do produto 10080047» | `GET /products/{code}/summary` | Cair no `/analyser` |
| «Faturamento do produto …» | `GET /products/{code}/sales/billing` | Usar `/sales` genérico |
| «Valor total de estoque da empresa» | `GET /supplies/stock-value` | `GET /products/{code}/stock` |
| «Compare as estruturas» | Orquestração multi-fetch | Uma única action ou só histórico |

O dígito após «grupo» **não** é código de produto (`ChatProductQueryIntentService._is_group_code_numeric_token`).

### Perguntas de capacidade

«Consegue buscar por grupo?», «coonsegue…» → `ChatCapabilitiesService.is_capability_inquiry`: resposta direta com método/rota, **sem** `execute_external_action`.

### Paridade ChatGPT/Gemini (roteamento e velocidade) — maio/2026

Pesquisa e plano de produto (28/mai/2026): decisão de rota **antes** do LLM, catálogo pequeno se usar loop agentic, respostas diretas sem inferência quando possível.

| Recurso | Caminho |
|---------|---------|
| Roadmap Onda 11 (feito / falta / critérios) | [`../roadmap/inteligencia-chat-onda-11-paridade-assistentes.md`](../roadmap/inteligencia-chat-onda-11-paridade-assistentes.md) |

### Documentos e testes

| Recurso | Caminho |
|---------|---------|
| Mapa intenção → rota (RAG) | [`../knowledge/api-delpi-rotas-agente.md`](../knowledge/api-delpi-rotas-agente.md) |
| Auditoria rota a rota + status | [`../roadmap/api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md) |
| Casos de regressão | `tests/fixtures/chat_intelligence_regression_cases.py` |
| Limite upload conhecimento | `KNOWLEDGE_DOCUMENT_MAX_CHARS` (default 2M) |

```bash
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_intelligence_regression.py \
  tests/unit/domain/services/test_chat_department_kpi_intent_service.py \
  tests/unit/application/services/test_external_action_selection_service.py \
  tests/unit/domain/services/test_chat_product_query_intent_service.py \
  -q
```

---

## Diagnóstico admin (`adminDebug`)

**Toda** resposta do assistente (send/stream/resend) monta e **persiste** `metadata.adminDebug` via `ChatAdminDebugService.build_for_turn(...)` — para qualquer usuário, permitindo estudo do modelo no banco.

**Exposição ao cliente** (resposta HTTP, SSE, painel no chat) só quando `SendChatMessageRequest.admin_debug=True`, definido pelas rotas com `_can_use_admin_debug()` (permissão `minha-delpi.chat.admin` ou superadmin). O `GET /sessions/:id/messages` remove `adminDebug` do JSON para quem não é admin.

Payload típico (campos principais):

| Seção | Conteúdo |
|-------|----------|
| `workspace` | `agentKey`, `agent`, `project`, `skills`, `specialization`, actions habilitadas |
| `pipeline` | `operationalOptimize`, `analysisMode`, `fastPath`, **`skipRag`**, `historySummary` |
| `tooling` | `toolCalls`, `selectedExternalAction`, texto de contexto de tools |
| `rag` | `sources`, `ragContextText` |
| `llm` | Mensagens enviadas ao modelo (truncadas) |
| `recordedAt` | ISO UTC do turno |

Para perguntas de identidade, espere `pipeline.skipRag: false`. `rag.sources` pode vir vazio no JSON exposto (fontes globais ocultas) — use `rag.ragContextText` e `rag.sourcesNote`. Se só houver normas técnicas na base, o filtro esvazia o contexto e a resposta vem do fallback canônico (sem LLM).

Mensagens antigas não ganham diagnóstico retroativo.

---

## Checklist para novas features de inteligência

- [ ] Implementação em serviço/domain compartilhado (não só no JSON do agente).
- [ ] `ChatToolContextService` ou pipeline atualizado se afetar tools/histórico.
- [ ] Policy em `prompt_policies/` se mudar comportamento do LLM para todos.
- [ ] Testes unitários + caso em `chat_intelligence_regression_cases.py` quando aplicável.
- [ ] Sem duplicar lógica entre stream e send.
- [ ] Simulação admin recebe `previous_messages` quando depender de histórico.
- [ ] Rotas de mensagem passam `admin_debug=_can_use_admin_debug()` para **expor** diagnóstico (persistência é automática).

---

## Referências

- Auditoria api-delpi (maio/2026): [`../roadmap/api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md)
- Roadmap onda 1 (pipeline): [`../roadmap/inteligencia-chat-onda-1.md`](../roadmap/inteligencia-chat-onda-1.md)
- Agentes (HTTP): [`../api/03-agentes.md`](../api/03-agentes.md)
- Modelo conceitual: [`../api/12-modelo-conceitual.md`](../api/12-modelo-conceitual.md)
- Regra Cursor: [`.cursor/rules/chat-intelligence-base.mdc`](../../../.cursor/rules/chat-intelligence-base.mdc)
