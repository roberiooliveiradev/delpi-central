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
| `ChatCanvasIntentService` | Pedido de enviar ou **atualizar** conteúdo na lousa (cópia, append, merge com API; não confunde com Canva.com) |
| `ChatCanvasContentService` | Monta markdown da lousa: última resposta útil, `canvasOpen` do histórico, merge com tools |
| `ChatAgentProfileService` | Perfil dinâmico do agente ativo (`name`, `description`, `systemPrompt`) para identidade e small talk |
| `ChatAssistantIdentityService` | «Quem é você?» — resposta direta dinâmica (sem RAG/LLM no default) |
| `ChatMetaDirectAnswerService` | Perguntas compostas meta («quem sou eu, o que consigo fazer, quem é você?») em seções |
| `ExternalActionColumnLabelService` | Rótulos PT-BR de colunas (`column_labels.json` + OpenAPI `title`) no presenter |
| `ChatToolContextService` | Execução de tools; aceita `previous_messages` para herdar análise |
| `ChatExternalActionOrchestrationService` | Planeja várias actions OpenAPI (ex.: dois códigos de produto) |
| `ChatCompositeDirectAnswerService` | Monta resposta direta única com sucesso/erro por consulta |
| `ChatOperationalPipelineService` | Fast path operacional (desligado em modo análise) |
| `ExternalActionSelectionService` | Roteamento OpenAPI (não dispara consulta em pedido analítico nem em **cópia simples** para lousa) |
| `ChatDepartmentKpiIntentService` | KPIs departamentais (`/commercial`, `/financial`, `/production`, `/hr`, `/quality`, `/system`) |
| `ChatOperationalParameterService` | Consultas operacionais sem parâmetro (código de produto, etc.) |
| `ChatOperationalRefinementService` | Follow-up operacional (estoque, KPI/suprimentos com filial) reutilizando contexto do histórico |
| `ChatRouteContextService` | Herança de segmento OpenAPI (`/stock`, `/purchases`, `/supplies/cpv`, KPIs departamentais) entre turnos |
| `ChatDateRangeIntentService` | Períodos em linguagem natural («mês passado», «rol do mês de março», últimos N dias, intervalo `DD/MM/YYYY`) → `start_date`/`end_date` em `DD-MM-YYYY` (KPIs, suprimentos, listagem de OV); ambiguidade de ano pede confirmação |
| `ChatPaginationConsolidationService` | Consolidação automática de rotas paginadas quando o usuário pede total/completo ou confirma continuação |
| `ChatPaginatedExternalActionService` | Orquestra múltiplas chamadas API por turno e merge de payloads paginados |
| `ChatStreamActivityService` | Log de atividade em streaming SSE (`event: activity`) — fases **Pensar**, **Planejar novos passos**, consultas API, RAG, falhas e ausência de dados; `entry_id` estável para atualizar a mesma linha no painel |
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
| Resposta | **`build_direct_answer`** montada dinamicamente via `ChatAgentProfileService` (`name`, `description`, `systemPrompt` publicados; override opcional em `metadata.identity.responses`) quando `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED=true` (default) — **sem RAG nem LLM** |
| Desligar atalho | `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED=false` — volta RAG + LLM + policy `chat-assistant-identity.md` |
| RAG (modo legado) | `build_rag_query`, `RAG_IDENTITY_QUESTION_MIN_SCORE`, filtro `is_identity_relevant_chunk` (rejeita `Normas_Tecnicas_*` mesmo com “DELPI” no trecho) |

Com o atalho ativo, perguntas como «quem te criou?» não montam prompt com perfil RBAC completo nem chamam o Ollama.

### Small talk (maio/2026)

Saudações curtas («olá», «obrigado», «tchau») → `ChatSmallTalkService.build_direct_answer` com respostas em `small_talk.json`: **sem RAG**, **sem** loop agentic, **sem** LLM. Reduz latência e evita RAG irrelevante em cumprimentos.

### Perguntas meta compostas (maio/2026)

Mensagens que misturam perfil do usuário, capacidades da plataforma e identidade do assistente (ex.: *«me diga quem sou eu e o que consigo fazer aqui, quem é você?»*) → `ChatMetaDirectAnswerService.build` monta resposta em seções (`## Seu perfil`, `## O que você pode fazer aqui`, `## Sobre o assistente`). Tem prioridade sobre atalhos isolados de capacidade ou identidade.

### Lousa / canvas — cópia, append e merge operacional (maio/2026)

| Tipo de pedido | Exemplo | Comportamento |
|----------------|---------|---------------|
| **Cópia simples** | «coloque na lousa» | Copia a **última resposta útil** do assistente (ignora confirmações «Coloquei … na lousa») |
| **Append de chat** | «acrescente isso na lousa» | Merge do markdown já na lousa (`metadata.canvasOpen` do histórico) + última resposta útil |
| **Append operacional** | «acrescente na lousa a descrição do produto 10080049» | Executa action OpenAPI → merge na lousa existente; **não** bloqueia tools |

Detalhes:

- `ChatCanvasIntentService.is_canvas_operational_update_request` libera `ExternalActionSelectionService` e `ChatExternalActionOrchestrationService` (só cópia simples bloqueia actions).
- `ChatCanvasContentService.build_update_from_tools` usa `textPresentation.markdown` (ou tabela) das tool calls bem-sucedidas.
- Exige `capabilities.canvas !== false` no agente; evento SSE `canvas_open` e `metadata.canvasOpen` na mensagem assistant.

Testes: `test_chat_canvas_intent_service.py`, `test_chat_canvas_content_service.py`, `test_chat_canvas_stream_and_send.py`.

### Rótulos de colunas em português (maio/2026)

Tabelas operacionais usam `ExternalActionColumnLabelService`: prioridade OpenAPI `title` → `column_labels.json` → humanize do nome técnico. Evita headers crus (`order_number`, `X3_CAMPO`) na UI quando há tradução cadastrada.

### Listagem de OV vs vendas de produto (maio/2026)

| Situação | Rota correta | Erro comum |
|----------|--------------|------------|
| «listar ov de 01/04/2026 a 30/04/2026» | `GET /sales` (`list_sale_orders`) com `date_start` / `date_end` | Tratar datas como códigos de produto (`01042026`) e chamar `/products/{code}/sales` |
| Resumo de vendas de um produto | `GET /products/{code}/sales` | Confundir com listagem de OVs |

`ChatAnalysisIntentService.extract_all_product_codes` ignora tokens de data `DD/MM/YYYY`. Apresentação de OVs usa tabela (`preferredFormat: table`); coluna `order_number` rotulada como **OV**.

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
5. **Drill-down por descrição** — «Mais informações sobre {descrição}» após árvore/tabela de estrutura: `ChatProductDescriptionResolutionService` resolve o código no histórico (`presentation`/`treePresentation`); se não achar, roteia para `GET /products/search`. Tokens de especificação técnica (`6,30X0,80`, `1,00-2,60`) **não** viram código de produto.
6. **Busca por grupo ou descrição** → `GET /products/search` (prioridade sobre analyser quando há «grupo X»).
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
| `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` | `12` | Loop agentic: catálogo via `ChatAgenticCatalogService` + `find_candidate_actions`, ranqueado por intent |

Habilitar agentic/router só em sandbox ou com agente com **poucas** actions bem descritas.

**Catálogo agentic (11.3.1):** com `CHAT_AGENTIC_LOOP_ENABLED=true`, `ChatAgenticCatalogService` monta no máximo `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` (default 12) a partir de `find_candidate_actions`, reordenando por intent (`/stock`, `/structure`, …). O planner LLM **só** pode escolher actions desse catálogo; metadados em `toolCalls[].metadata.agentic` / `intelligence.agentic` (`catalogSize`, `catalogMaxActions`).

### Multi-action e histórico (maio/2026)

`ChatAnalysisIntentService.extract_product_codes_for_action_planning` planeja consultas paralelas **somente** com códigos da mensagem atual. Se o usuário já informou um código («estoque do produto 10080099»), códigos citados só no histórico **não** disparam N chamadas. Follow-ups («estoque desse produto») continuam resolvendo **um** código via contexto.

`CHAT_OPERATIONAL_SLIM_USER_CONTEXT` (default `true`): em modo operacional, o prompt LLM não inclui o bloco completo de perfil RBAC (reduz tokens), exceto perguntas sobre o **usuário** («quem sou eu»).

### Refinamento operacional (follow-up de estoque) — maio/2026

Após uma consulta de estoque bem-sucedida, mensagens como «filtre filial 02» ou «somente armazém 99»:

| Etapa | Comportamento |
|-------|----------------|
| `ChatOperationalRefinementService` | Detecta refinamento; recupera código/rota do histórico; extrai filial/armazém |
| `ChatRouteContextService` | Mapeia segmentos de path e lote recente de tools para `resolve_product_route_segment` |
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

### Streaming — log de atividade e carregamento (maio/2026)

Turnos em `POST .../messages/stream` expõem progresso antes do texto final:

| Camada | Comportamento |
|--------|----------------|
| **API** | Após `status` «Conectado…», o prepare roda em thread com `app_context` Flask; eventos `activity` são emitidos durante carga de sessão, tools e RAG (não só no fim). |
| **SSE** | Comentário `: connected` + keepalive após `status`/`activity` (`X-Accel-Buffering: no`). |
| **Plugin** | `ChatThinkingDots` (três pontos pulsando); log **uma linha por fase** que substitui a anterior (`compactActivityLogForDisplay`); `flushSync` no `onActivity`. |
| **Resposta** | Texto revelado aos poucos (`useStreamingTextReveal`); durante o prepare não substitui o painel de etapas. |

Serviços: `ChatTurnPreparationService` (`on_stream_activity`), `stream_chat_message_use_case` (fila + thread), `ChatStreamingActivityPanel`, `streamingActivityLog.ts`.

### Apresentação rica sem duplicar markdown (maio/2026)

Quando `toolCalls[].metadata.presentation` (ou `tablePresentation`) traz **tabela**, **gráfico** ou **KPI**:

| Camada | Regra |
|--------|--------|
| **API** | `ChatToolContextService._compact_direct_answer_for_rich_presentation` encurta ou anula `directAnswer` tabular; mantém só título ou texto curto não tabular. Estrutura `/structure` com markdown completo continua usando `_suppress_redundant_structure_presentations` (só card, sem tabela duplicada). |
| **Plugin** | `shouldSuppressMarkdownForPresentation` oculta `ChatMarkdown` se o corpo repete tabela/gráfico; `ChatRichPresentation` é a fonte visual (toggle gráfico/tabela). |

Pedido explícito «em texto» / «só texto» (`_FORMAT_TEXT_HINTS`) não compacta o `directAnswer`.

### Consolidação paginada (total / completo / continuar) — maio/2026

Quando a API retorna resposta parcial (`page`, `total`, `total_pages`), o chat pode buscar **várias páginas** e consolidar numa única resposta — em **qualquer formato** (tabela, árvore, gráfico ou texto).

| Gatilho | Exemplos | Comportamento |
|---------|----------|---------------|
| **Total/completo** | «traga tudo», «listagem completa», «tabela completa», «registros completos» | Após a 1ª página, busca páginas restantes até `CHAT_PAGINATION_MAX_PAGES_PER_TURN` |
| **Follow-up após parcial** | «árvore completa», «tabela completa», «completo» (mesma conversa) | Reutiliza a última action paginada do histórico; refaz consulta + consolida |
| **Continuação** | «sim, continue», «continuar», «sim» (com estado pendente) | Retoma de `metadata.toolCalls[].paginationConsolidation` |
| **Limite por turno** | — | Ao atingir o limite, pergunta se deve continuar; confirmação do usuário dispara novo lote |

| Etapa | Serviço / campo |
|-------|-----------------|
| Detecção de intenção | `ChatPaginationConsolidationService.looks_like_full_fetch_request` / `looks_like_continue_fetch_request` |
| Plano de páginas | `build_fetch_plan`, `build_continue_plan`, `collect_last_paginated_reference` |
| Execução | `ChatPaginatedExternalActionService` (`maybe_consolidate`, `fetch_full_from_history`, `fetch_continue_plan`) |
| Integração | `ChatToolContextService` — atalho **antes** da seleção normal de tools |
| Estado persistido | `toolCalls[].metadata.paginationConsolidation` (`fetchedPages`, `mergedCount`, `apiTotal`, `completed`, `consolidatedPayload`) |
| Formato | `_resolve_consolidation_format` — pedido explícito («em tabela») ou herança do `preferredFormat` do turno anterior |

Variáveis:

| Variável | Default |
|----------|---------|
| `CHAT_PAGINATION_AUTO_FETCH_ENABLED` | `true` |
| `CHAT_PAGINATION_MAX_PAGES_PER_TURN` | `5` (máx. 8) |

Testes: `test_chat_pagination_consolidation_service.py`, `test_chat_paginated_external_action_service.py`, cenários em `test_chat_tool_context_service_direct_response.py`.

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
