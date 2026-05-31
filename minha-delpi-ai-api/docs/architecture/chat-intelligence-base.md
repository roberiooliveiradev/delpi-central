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
| `ChatIntentRouterService` | Roteamento de intenção (Playbook 02): `classify`, `resolve_executed`; intents `self_help`, `web_search`, `sql_task`, `mixed_task`, `presentation_task`; `metadata.intentRouting` + `adminDebug.intentRoute`; ver [`intent-routing.md`](./intent-routing.md) |
| `ChatIntentRouterMetricsService` | `intentRouterMetrics` e espelho `intentRouting` na mensagem do assistente |
| `ChatActivePendingService` | Pendências ativas (`metadata.activePending`); resolução como `clarification`; filial/sim; snapshot de roteamento no feedback `routing_*` |
| `ChatOnboardingService` | Playbook 10 — cards/tour no catálogo, modo treinamento («me ensine a usar»), estágio `onboarding_training` |
| `ChatOnboardingMilestoneService` | Marcos leves de adoção — `milestoneCelebrations` e `onboardingMilestonesAchieved` no metadata do assistente |
| `ChatAttachmentResponseService` | Enriquece upload/listagem com `readingStatus` e `preview` consistente (Playbook 07) |
| `ChatAttachmentImageOcrService` | OCR opcional em imagens (`CHAT_ATTACHMENT_IMAGE_OCR_ENABLED`) |
| `ChatDocumentVisionService` | Skill `document-vision-delpi` — OCR PDF/imagem (native + Tesseract); anexos da sessão (`documentVision` no tool context) e `drawing-analysis-delpi` |
| `ChatDocumentVisionBomService` | Heurística BOM (`bomRows`, estágio `bom_heuristic`) em texto OCR — Onda 13.3.2 |
| `ChatDocumentVisionTitleBlockService` | Carimbo `titleBlock` (bbox heurístico + `fields.code/rev`) — Onda 13 |
| `ChatDocumentVisionTablesService` | Tabelas `tables[]` (markdown/TSV heurístico, estágio `table_heuristic`) — Onda 13 |
| Backends visão | `native`, `tesseract`, `docling`, `paddleocr` (profile vision), `ollama_vlm` (Ollama `/api/chat` + imagens) |
| Persistência anexo | `attachment.metadata.documentVision` após indexação (`IndexChatAttachmentUseCase`) e turno `attachment_document` |
| `ChatAgentMiniDashboardService` | Mini dashboard + recomendações em `GET /chat/agents/{id}/stats` (gráficos Fase 4) |
| `ChatConversationContextService` | Texto de histórico + dados de `toolCalls` em metadata |
| `ChatAnalysisIntentService` | Detecção de comparação / insights; `is_data_interpretation_request` e `is_data_reference_without_tool_data` para follow-ups sobre dados já consultados |
| `ChatDataInterpretationAnswerService` | Resposta direta nos follow-ups (#74–78): monta markdown a partir de `humanizedSummary` das tool calls recentes, sem nova API/SQL |
| `ChatTechnicalDescriptionIntentService` | «Como descrever terminal/cabo?», campos da descrição técnica → RAG `Normas_Tecnicas_DELPI.md` (global), sem API de catálogo |
| `ChatCanvasIntentService` | Pedido de enviar ou **atualizar** conteúdo na lousa (cópia, append, merge com API; não confunde com Canva.com) |
| `ChatCanvasContentService` | Monta markdown da lousa: última resposta útil, `canvasOpen` do histórico, merge com tools |
| `ChatAgentProfileService` | Perfil dinâmico do agente ativo (`name`, `description`, `systemPrompt`) para identidade e small talk |
| `ChatAssistantIdentityService` | «Quem é você?» — resposta direta dinâmica (sem RAG/LLM no default) |
| `ChatMetaDirectAnswerService` | Perguntas compostas meta («quem sou eu, o que consigo fazer, quem é você?») em seções |
| `ExternalActionColumnLabelService` | Rótulos PT-BR de colunas (`column_labels.json` + OpenAPI `title`) no presenter |
| `ChatToolContextService` | Execução de tools; aceita `previous_messages` para herdar análise |
| `ChatExternalActionOrchestrationService` | Planeja várias actions OpenAPI (ex.: dois códigos de produto) |
| `ChatCompositeDirectAnswerService` | Monta resposta direta única com sucesso/erro por consulta |
| `ChatOperationalPipelineService` | Fast path operacional (desligado em modo análise e em Normas/descrição técnica) |
| `ChatSqlOperationalIntentService` | Perguntas SQL de produção/programação do dia (não catálogo) |
| `ChatSqlProductionQueryService` | Template SC2010 + execução `/data/sql` ou resposta direta com SQL |
| `ChatSqlQueryRefinementService` | Follow-up multi-turn: add/remove colunas, filtro de filial e exibir SQL anterior |
| `ExternalActionSelectionService` | Roteamento OpenAPI (não dispara consulta em pedido analítico, Normas ou **cópia simples** para lousa) |
| `ChatDepartmentKpiIntentService` | KPIs departamentais (`/commercial`, `/financial`, `/production`, `/hr`, `/quality`, `/system`) |
| `ChatOperationalParameterService` | Consultas operacionais sem parâmetro (código de produto, etc.) |
| `ChatOperationalRefinementService` | Follow-up operacional (estoque, KPI/suprimentos com filial) reutilizando contexto do histórico |
| `ChatRouteContextService` | Herança de segmento OpenAPI (`/stock`, `/purchases`, `/supplies/cpv`, KPIs departamentais) entre turnos |
| `ChatDateRangeIntentService` | Períodos em linguagem natural («mês passado», «rol do mês de março», últimos N dias, intervalo `DD/MM/YYYY`) → `start_date`/`end_date` em `DD-MM-YYYY` (KPIs, suprimentos, listagem de OV); ambiguidade de ano pede confirmação |
| `ChatPaginationConsolidationService` | Consolidação automática de rotas paginadas quando o usuário pede total/completo ou confirma continuação |
| `ChatPaginatedExternalActionService` | Orquestra múltiplas chamadas API por turno e merge de payloads paginados |
| `ChatStreamActivityService` | Log de atividade em streaming SSE (`event: activity`) — fases **Pensar**, **Planejar novos passos**, consultas API, RAG, falhas e ausência de dados; `entry_id` estável para atualizar a mesma linha no painel |
| `ChatCapabilitiesService` | Perguntas «consegue…?» / capacidades sem chamar API à toa |
| `AssistantCapabilitiesRegistry` | Catálogo `features_catalog.json`, busca, disponibilidade e «o que mudou?» (autoajuda Fase 2) |
| `ChatAssistantCatalogService` | Payload do painel de ajuda (`GET /chat/assistant/catalog`, Fase 4–5: agente, `userContext`, filtro por permissão de tools) |
| `AssistantCapabilitiesCatalogGenerator` | Sincroniza `features_catalog.json` com actions/skills — KPIs, produto, match por path mais específico (`pathRulesVersion` 2026.06.02) |
| `ChatTextTaskIntentService` | Tarefas textuais puras (correção, e-mail, resumo) — estágio `text_task`, sem tools/RAG |
| Correção de texto | [`text-correction.md`](./text-correction.md) — `ChatTextCorrectionIntentService`, validador, chips |
| `ChatEmailIntentService` | Subintenções de e-mail (`email_create`, `email_formalize`, …) — estágio `email_writing` |
| `ChatEmailQualityValidator` | Checklist pós-geração (frases artificiais, assinatura, prazos, assunto fraco) → `emailQuality` |
| `ChatEmailAnswerGuardService` | Sanitização soft (assinatura inventada, frases artificiais) antes de persistir |
| `ChatEmailPromptSupplementService` | Contexto no prompt (destinatário, tom, DELPI/IA, preferências) |
| `ChatEmailPreferenceService` | Preferências de e-mail na sessão (`emailWriting` persistido, `emailPreferences` no metadata/chips) |
| `ChatEmailTurnService` | Orquestra suplemento de prompt, guard e metadata de follow-up |
| `ChatEmailOperationalComposerService` | E-mail a partir de consulta autorizada (turno misto / follow-up) + `emailDataSource` |
| `ChatEmailFollowUpService` | Chips `emailFollowUpSuggestions` + `textTask` após rascunho de e-mail |
| `ChatHelpErrorFollowUpService` | Chips de autoajuda após erro operacional (`helpErrorFollowUpSuggestions`, Fase 5) |
| `ChatWebSearchSaveSourcesService` | Persiste fontes da última pesquisa web como `project_source` (chip «Salvar fontes») |
| `ChatHelpAdoptionService` | Log estruturado de adoção do painel `?` (`POST /chat/assistant/help-events`) |
| `ChatGuidedFlowService` | Fluxos guiados e cards interativos (`guidedFlow`, `guidedFlowCards`) — interatividade Fase 5 |
| `ExternalActionResultPresenter` | `humanizedSummary` explícito para listas vazias; `chartPresentation` com tipos ampliados |
| `ChatChartTypeSelectionService` | Escolhe `chartType` (bar, line, horizontal_bar, donut, grouped_bar, …) a partir dos dados e da pergunta |
| `ChatMessageNormalizationService` | Typos comuns (ebita→ebitda, kaisen→kaizen, coonsegue→consegue, …) |
| `ChatStructureComparisonOrchestrationService` | Comparação de estruturas com fetch multi-produto |
| `PromptPolicyService` | Policies globais (`operational-agent.md`, `administrative-writing.md`, `email-writing.md`, `chat-analysis-insights.md`, …) |
| `ChatWorkingMemoryService` | Snapshot pré/pós-turno: entidades, follow-up, referências resolvidas |
| `ChatSessionMemoryService` | Fase 4: overlay em `ai_chat_session_memory` (reload da sessão) |
| `ChatBehaviorInstructionService` | Instruções de comportamento da sessão injetadas no contexto operacional |
| `ChatContextAssertivenessService` | Score 0–100 e flags (`follow_up_entity_reused`, `humanized_none_fields`, …) |
| `ChatContextMetadataService` | Grava `contextSnapshot`, `contextAssertiveness` e espelha em `adminDebug` |

Use cases (`SendChatMessageUseCase`, `StreamChatMessageUseCase`, `AdminAgentSimulateUseCase`) **não** devem acumular regras de inteligência — apenas passam histórico e flags ao pipeline.

Documentação dedicada: [`email-writing.md`](./email-writing.md) (escrita de e-mails corporativos).

### Memória e assertividade (Fases 4–5)

1. **Pré-turno** — `ChatTurnPreparationService` monta `workspaceContext.workingMemory` a partir do histórico e do overlay persistido (`ChatSessionMemoryService`).
2. **Pós-turno** — `ChatContextMetadataService` atualiza snapshot e calcula assertividade; `contextSnapshot` é sincronizado em `ai_chat_session_memory`.
3. **Admin** — `ChatAdminDebugService.resolve_client_admin_debug` mescla memória/assertividade após o attach (resposta HTTP/SSE).
4. **Regressão** — `CONTEXT_ASSERTIVENESS_CASES` em `tests/fixtures/chat_intelligence_regression_cases.py`; smokes `scripts/smoke_context_assertiveness_multiturn.py` e `scripts/smoke_follow_up_chips.py` (ver [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md)).

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

### Perfil do usuário («quem sou eu»)

| Etapa | Comportamento |
|-------|----------------|
| Fonte | `GET {CORE_API_BASE_URL}/me` + `me/access-profile` via `ChatUserContextService` |
| Resposta direta | `build_direct_answer` — exibe nome/e-mail ao titular (não aplica `_strip_pii`; LGPD só no bloco injetado no LLM em `build_user_context`) |
| Consentimento | `GET {CORE_API_BASE_URL}/me/consents` (mesmo prefixo que `/me`; **não** duplicar `/core-api` no path quando a base já é `http://core-api:8000`) |

Se o consentimento `ai_context` não estiver concedido e `LGPD_REQUIRE_AI_CONSENT=true`, o prompt LLM não recebe PII — mas a resposta direta na UI continua mostrando nome/e-mail quando `/me` os retorna.

### Small talk (maio/2026)

Saudações, despedidas, agradecimentos, confirmações e interações sociais curtas → `ChatSmallTalkService.build_direct_answer` com padrões em `small_talk.json` (fonte única via `ChatSmallTalkPatternService`): **sem RAG**, **sem** loop agentic, **sem** LLM. Catálogo inspirado em expressões conversacionais PT-BR ([cumprimentos/despedidas](https://philipebrazuca.com/pt-br/cumprimentos-e-despedidas-em-portugues/), intents de [atendimento BR](https://huggingface.co/datasets/RichardSakaguchiMS/brazilian-customer-service-conversations)). Categorias: `greeting`, `wellbeing`, `thanks`, `apology`, `praise`, `farewell`, `ack`, `laughter`.

Typos de saudação (`bo dia`, `bao dia`) são normalizados em `ChatMessageNormalizationService` antes do match.

### Perguntas utilitárias — hora, data, ano (maio/2026)

Perguntas curtas como «que horas são?», «que dia é hoje?», «qual o ano?» → `ChatUtilityDirectAnswerService` com padrões em `utility_answers.json`:

| Etapa | Comportamento |
|-------|----------------|
| Classificação | `classify(message)` por categoria (`current_time`, `current_date`, `current_datetime`, `current_weekday`, `current_year`) |
| Resposta | Template PT-BR com hora/data reais (`CHAT_UTILITY_TIMEZONE`, default `America/Sao_Paulo`) quando `CHAT_UTILITY_DIRECT_ENABLED=true` |
| Pipeline | **Sem RAG**, **sem** loop agentic, **sem** LLM; estágio `utility_direct` |
| Typos | `ChatMessageNormalizationService` corrige antes do match — ex.: `que hors são?` → `que horas sao`, `q horas` → `que horas`, `q dia` → `que dia e hoje` |
| Exclusões | Mensagens com contexto operacional (`producao`, `ordem`, `estoque`, …) não entram no atalho |

Checklist manual: **U1–U9** em [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md).

Testes: `test_chat_utility_direct_answer_service.py`, `test_chat_utility_stream.py`, `test_chat_message_normalization_service.py`.

### Rótulos PT-BR das rotas api-delpi (maio/2026)

Actions OpenAPI do provider **api-delpi** exibem rótulos humanizados via `ChatActionLabelService` + `labels/api_paths.json` (~84 rotas alinhadas ao código em `api-delpi/app/main.py`):

- Inclui: `/commercial/proposals`, `/production/oee/series`, `/production/otd/series`, `/production/eficiencia-fabril/*`, `/system/tables/{tablename}/schema|indexes|relations`
- Removidas rotas fantasma (`/commercial/billing`, `/chat/*`, subrotas inexistentes de produto)

`capabilities.json` (`pathRules`, `commonExamples`) reflete o mesmo catálogo. Regenerar OpenAPI opcional: `scripts/sync_api_delpi_openapi.py`.

Testes: `test_chat_action_label_service.py`, `test_content_service.py`.

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

### Pesquisa web — planejamento (maio/2026)

| Camada | Comportamento |
|--------|----------------|
| `ChatWebSearchPlanningService` | Modo `quick` (≤3 queries) ou `deep` (até 6); variantes «manual oficial», `site:marca` (WEG, Siemens, …) |
| `ChatWebSearchIntentService.resolve` | Expõe `plannedQueries`, `searchMode`, `preferOfficial` nos argumentos da tool |
| `WebSearchHttpGateway` | Executa queries planejadas antes do retry EN; grava `searchMode` no payload |
| MFE | `ChatWebSearchResearchPanel` exibe modo e preferência por fontes oficiais |

Smoke: `scripts/smoke_web_search_planning.py`. Requer `CHAT_WEB_SEARCH_ENABLED=true` e provider configurado para E2E real.

### Pesquisa web — avaliação de fontes (maio/2026)

| Camada | Comportamento |
|--------|----------------|
| `ChatWebSearchSourceEvaluationService` | Classifica URL (`manufacturer`, `government`, `forum`, …), pontua e reordena `results` |
| `WebSearchTool` | Chama `enrich_payload` após busca bem-sucedida |
| `ChatWebSearchDirectAnswerService` | Injeta avisos de confiabilidade no markdown quando aplicável |
| `ChatWebSearchResearchActivityService` | Propaga `confidence`, `warnings`, `excludedSources` e metadados por site |
| MFE | Painel de pesquisa com tag «oficial», rótulo de confiança e observações |

Testes: `test_chat_web_search_source_evaluation_service.py`, `test_chat_web_search_research_activity_service.py` (propagação).

### Pesquisa web — integração anexo / ERP (maio/2026)

| Camada | Comportamento |
|--------|----------------|
| `ChatWebSearchIntegrationService` | Detecta híbrido anexo+web ou produto+web; queries extras; libera companion operacional |
| `ChatWebSearchIntentService` | `integrationMode` nos argumentos; não bloqueia actions quando há produto interno |
| `WebSearchTool` / síntese / resposta direta | Metadata e notas «não substituir dado interno» |
| MFE | Painel indica modo (`produto + web`, `anexo + web`, etc.) |

Testes: `test_chat_web_search_integration_service.py`.

### Pesquisa web — UX pós-pesquisa (maio/2026)

| Camada | Comportamento |
|--------|----------------|
| `ChatWebSearchFollowUpService` | `webSearchFollowUpSuggestions` no metadata (playbook `webSearchFollowUpChips`) |
| MFE | Cards de fontes web, badges «oficial», chips «Após pesquisa web» |

Testes: `test_chat_web_search_follow_up_service.py`.

### Pesquisa web — cruzamento ERP (maio/2026)

| Camada | Comportamento |
|--------|----------------|
| `ChatWebSearchErpCrossReferenceService` | Após ERP + `web_search` no mesmo turno, anexa bloco comparativo e `erpCrossReference` no payload |
| `ChatToolContextService` | Propaga `webSources` mesmo quando a resposta direta veio do ERP |

Testes: `test_chat_web_search_erp_cross_reference_service.py`.

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

**Base global de conhecimento:** agentes sem skill explícita `company-knowledge` herdam `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL` (documentos em [`../knowledge/domains/global/`](../knowledge/domains/global/): `normas-tecnicas-delpi.md`, `gpt-instructions.md`, `O_ARQUITETO_DO_CODIGO.md`).

### Descrição técnica de matérias-primas — Normas DELPI (maio/2026)

Perguntas de **como escrever/descadastrar** descrições técnicas (não confundir com «qual a descrição do produto 10080047»):

| Etapa | Comportamento |
|-------|----------------|
| `ChatTechnicalDescriptionIntentService` | Detecta orientação normativa («como descrever terminal», «campos da descrição», «normas técnicas cabo») |
| `ChatTurnPreparationService` | `build_rag_query` enriquecido com grupo técnico (ex.: terminal → **1008**) |
| `ExternalActionSelectionService` | Retorna `None` — **sem** busca REST de catálogo |
| `ChatOperationalPipelineService` | Fast path operacional **desligado** |
| `ChatOperationalParameterService` | **Pula loop agentic** (resposta documental via RAG + 1 LLM) |
| Policy | `technical-description-normas.md` — ir à seção do `Normas_Tecnicas_DELPI.md`, explicar estrutura/campos/exemplos |

Fonte RAG: `docs/knowledge/domains/global/normas-tecnicas-delpi.md` (`scope: global`). Skill `company-knowledge` necessária (default herdado).

Testes: `test_chat_technical_description_intent_service.py`, `test_select_action_skips_catalog_for_technical_description_guidance`.

Checklist manual: **N1–N4** em [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md).

### SQL operacional — produção do dia (maio/2026)

Perguntas como «quais produtos serão produzidos hoje?» exigem **SQL analítico** (SC2010), não catálogo REST:

| Serviço | Função |
|---------|--------|
| `ChatSqlOperationalIntentService` | Marca intenção SQL de produção |
| `ChatSqlProductionQueryService` | Template SQL; fast path com `POST /data/sql` ou resposta direta com query (G3) |
| `ChatToolContextService` | Executa SQL sem RAG quando aplicável |

Bloqueios: não usar `/products/search`; action fixa em `/data/sql` (não KPI departamental «production»).

Checklist: **G1–G3** em [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md); smoke `scripts/smoke_gpt_instructions_improvements.py`.

### Download de fontes e anexos (maio/2026)

| Endpoint | Escopo |
|----------|--------|
| `GET /chat/attachments/{id}/download` | Anexos da conversa |
| `GET /chat/sources/{id}/download` | Fontes de agente, projeto, notas de texto |

UI: botões no painel de conhecimento do agente, fontes do projeto e chips de anexo na mensagem (plugin `minha-delpi-chat`).

Doc HTTP: [`../api/05-projetos-fontes-anexos-artefatos.md`](../api/05-projetos-fontes-anexos-artefatos.md).

### Bundle exportável do agente (maio/2026)

Pasta [`../knowledge/domains/agents/minha-delpi-chat/`](../knowledge/domains/agents/minha-delpi-chat/) — reimportação em lote com nomes normalizados + `manifest.json`.

Script: `scripts/export_agent_knowledge_bundle.py --agent-key minha-delpi-chat`. Normalização: `AgentKnowledgeFilenameService`.

Changelog consolidado: [`../changelog/2026-05-inteligencia-chat-entregas.md`](../changelog/2026-05-inteligencia-chat-entregas.md).

---

## Roteamento automático (api-delpi)

O `ExternalActionSelectionService` resolve a action **antes** do LLM quando o fast path operacional está ativo. Ordem resumida:

1. Pedidos de **comparação/insights** → sem action (modo análise).
2. **Descrição técnica / Normas** («como descrever terminal») → sem action; RAG global `Normas_Tecnicas_DELPI.md`.
3. **SQL produção do dia** («produzidos hoje», programação SC2010) → `POST /data/sql` via fast path; não `/products/search`.
4. **OV / LMP / Transforma Mais / metadados Protheus** (tabelas/colunas).
5. **Suprimentos** (CPV, OTD, giro, valor total de estoque) — sem código de produto.
6. **Produto por código** (estoque, estrutura, pais, descrição cadastral, …) por intent.
7. **Drill-down por descrição** — «Mais informações sobre {descrição}» após árvore/tabela de estrutura: `ChatProductDescriptionResolutionService` resolve o código no histórico (`presentation`/`treePresentation`); se não achar, roteia para `GET /products/search`. Tokens de especificação técnica (`6,30X0,80`, `1,00-2,60`) **não** viram código de produto.
8. **Busca por grupo ou descrição** → `GET /products/search` (prioridade sobre analyser quando há «grupo X»).
9. **KPI departamental** via `ChatDepartmentKpiIntentService`.
10. Fallback semântico (se ranker configurado) — **bloqueado** quando a intenção é produto (estoque/estrutura/etc.) **sem código** (`ChatOperationalParameterService`).

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

**Perfis dev/prod (admin):** [`../knowledge/chat-intelligence-settings-profiles.md`](../knowledge/chat-intelligence-settings-profiles.md).

| Variável | Default | Motivo |
|----------|---------|--------|
| `CHAT_AGENTIC_LOOP_ENABLED` | `false` | Evita 2ª/3ª inferência e disparo de actions irrelevantes (ex. KPIs ROL) |
| `CHAT_TOOL_ROUTER_ENABLED` | `false` | Roteamento determinístico (`ExternalActionSelectionService`) já cobre o caso |
| `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` | `12` | Loop agentic: catálogo via `ChatAgenticCatalogService` + `find_candidate_actions`, ranqueado por intent |

Habilitar agentic/router só em sandbox ou com agente com **poucas** actions bem descritas.

**Catálogo agentic (11.3.1):** com `CHAT_AGENTIC_LOOP_ENABLED=true`, `ChatAgenticCatalogService` monta no máximo `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` (default 12) a partir de `find_candidate_actions`, reordenando por intent (`/stock`, `/structure`, …). O planner LLM **só** pode escolher actions desse catálogo; metadados em `toolCalls[].metadata.agentic` / `intelligence.agentic` (`catalogSize`, `catalogMaxActions`).

**Schemas enxutos (11.3.2):** cada action do catálogo é serializada por `ChatAgenticActionSchemaService` (método, path, descrição curta, parâmetros com `example` e `exampleArguments`) antes do prompt do planner — evita mandar o OpenAPI completo e orienta argumentos (`code`, `branch`, datas, paginação). Limite: `CHAT_AGENTIC_SCHEMA_MAX_PARAMETERS` (default 10).

**Native tool calling piloto (11.3.3):** `ChatNativeToolCallingService` só ativa quando (1) `CHAT_NATIVE_TOOL_CALLING_ENABLED=true`, (2) admin `nativeToolCallingEnabled=true` e (3) agente com `metadata.intelligence.nativeToolCallingEnabled=true`. Rotas api-delpi permanecem heurísticas.

**Timings no admin (11.3.4):** `metadata.intelligence.timings` (`ragMs`, `toolsMs`, `llmMs`, `totalMs`) é copiado para `adminDebug.intelligence` e exibido no painel «Diagnóstico (admin)» do plugin.

### Multi-action e histórico (maio/2026)

`ChatAnalysisIntentService.extract_product_codes_for_action_planning` planeja consultas paralelas **somente** com códigos da mensagem atual. Se o usuário já informou um código («estoque do produto 10080099»), códigos citados só no histórico **não** disparam N chamadas. Follow-ups («estoque desse produto») continuam resolvendo **um** código via contexto.

`CHAT_OPERATIONAL_SLIM_USER_CONTEXT` (default `true`): em modo operacional, o prompt LLM não inclui o bloco completo de perfil RBAC (reduz tokens), exceto perguntas sobre o **usuário** («quem sou eu»).

### Interpretação de dados operacionais (follow-up) — maio/2026

Após uma consulta operacional bem-sucedida (estoque, roteiro, estrutura, inspeção, KPI, SQL), mensagens como «explique os dados acima», «resume», «traduz isso» ou «não entendi»:

| Etapa | Comportamento |
|-------|----------------|
| `ChatAnalysisIntentService.is_data_interpretation_request` | Detecta referência a dados já mostrados; ativa `analysis_mode` |
| `ChatTurnPreparationService` | `skip_tools_for_data_interpretation` quando há `humanizedSummary` recente; `skipRag`; suprime bloco `/me` (perfil RBAC) |
| `ChatDataInterpretationAnswerService.build_answer` | **Fast path:** resposta direta a partir do último `humanizedSummary` (`titulo` + `linhas`) — sem LLM |
| `ExternalActionResultPresenter` | Gera resumo humanizado por rota (`/guide`, `/stock`, `/structure`, …) antes de heurística SQL genérica |
| `ChatConversationContextService` | Reidrata contexto de análise; evita título genérico «Consulta SQL» quando há resumo substantivo |
| Policy | `chat-data-interpretation.md` — fallback LLM só com contexto de dados já obtidos |
| Sem histórico (#79) | `is_data_reference_without_tool_data` → resposta canônica pedindo consulta prévia; **não** dispara SQL |

Evita o erro «Empty body — SQL not provided» ao confundir interpretação com nova consulta analítica.

Checklist manual: **#70–79** em [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md).

Testes: `test_chat_data_interpretation_answer_service.py`, `test_chat_analysis_intent_service.py`, casos `DATA_INTERPRETATION_*` em `chat_intelligence_regression_cases.py`.

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
| «Mostre vendas do produto …» | `GET /products/{code}/sales` (**api-delpi** habilitado no agente) | Estoque/busca api-externa quando api-delpi está off |
| «Faturamento do produto …» | `GET /products/{code}/sales/billing` | Usar `/sales` genérico |
| «Valor total de estoque da empresa» | `GET /supplies/stock-value` | `GET /products/{code}/stock` |
| «Compare as estruturas» | Orquestração multi-fetch | Uma única action ou só histórico |

O dígito após «grupo» **não** é código de produto (`ChatProductQueryIntentService._is_group_code_numeric_token`).

### Perguntas de capacidade

«Consegue buscar por grupo?», «coonsegue…» → `ChatCapabilitiesService.is_capability_inquiry`: resposta direta com método/rota, **sem** `execute_external_action`.

### Streaming — log de atividade, persistência incremental e carregamento (maio/2026)

Turnos em `POST .../messages/stream` expõem progresso antes do texto final:

| Camada | Comportamento |
|--------|----------------|
| **Persistência** | Com `CHAT_PERSIST_BEFORE_PLAYBACK=true` (default): `create_message(user)` **antes** do prepare → SSE `user_persisted` (envio normal **e** `resend/stream`); após tools/RAG, placeholder assistant (`delivery=generating`) → `assistant_pending`; resposta final → `playback` + `done`. Commits em checkpoints via `ChatStreamCheckpointService` + `chat_sse_stream_service`. |
| **API** | Após `user_persisted`, `status` «Conectado…»; o prepare roda em thread com `app_context` Flask; eventos `activity` durante carga de sessão, tools e RAG. |
| **SSE** | Comentário `: connected` + keepalive após `status`/`activity` (`X-Accel-Buffering: no`). Com `CHAT_PERSIST_BEFORE_PLAYBACK=false`, modo legado emite `token` até `done` (sem `user_persisted` / `playback`). |
| **Plugin** | `onUserPersisted` troca ids `optimistic-*` pelo `messageId` real; `ChatThinkingDots`; log **uma linha por fase** (`compactActivityLogForDisplay`); `flushSync` no `onActivity`. |
| **Resposta** | Com playback: texto animado (`useStreamingTextReveal` / `naturalTextReveal`) a partir do evento `playback`; durante o prepare não substitui o painel de etapas. Ao `done`, o MFE faz handoff otimista (`chatStreamHandoff` → `finalizeAssistantTurn`) para não piscar ao trocar bolha de streaming pela mensagem persistida. |

Serviços: `ChatTurnPreparationService` (`on_stream_activity`), `stream_chat_message_use_case`, `ChatStreamCheckpointService`, `chat_sse_stream_service`, `ChatStreamingActivityPanel`, `streamingActivityLog.ts`.

Validação: `scripts/validate_stream_incremental_persistence_e2e.py`, [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md) (seção **Persistência incremental no stream**).

### Apresentação rica sem duplicar markdown (maio/2026)

Quando `toolCalls[].metadata.presentation` (ou `tablePresentation`, `treePresentation`, `chartPresentation` quando não primários) traz **tabela**, **gráfico**, **árvore** ou **KPI**:

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
| Roadmap Onda 12 (backlog — desenhos PDF) | [`../roadmap/inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md`](../roadmap/inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) |

### Documentos e testes

| Recurso | Caminho |
|---------|---------|
| Changelog maio/2026 (G1–G8 + SQL + Normas + download) | [`../changelog/2026-05-inteligencia-chat-entregas.md`](../changelog/2026-05-inteligencia-chat-entregas.md) |
| Mapa intenção → rota (RAG) | [`../knowledge/api-delpi-rotas-agente.md`](../knowledge/api-delpi-rotas-agente.md) |
| Conhecimento global (Normas) | [`../knowledge/domains/global/`](../knowledge/domains/global/) |
| Bundle agente exportável | [`../knowledge/domains/agents/minha-delpi-chat/`](../knowledge/domains/agents/minha-delpi-chat/) |
| Auditoria rota a rota + status | [`../roadmap/api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md) |
| Casos de regressão | `tests/fixtures/chat_intelligence_regression_cases.py` |
| Limite upload conhecimento | `KNOWLEDGE_DOCUMENT_MAX_CHARS` (default 2M) |

```bash
docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_intelligence_regression.py \
  tests/unit/domain/services/test_chat_sql_operational_intent_service.py \
  tests/unit/domain/services/test_chat_sql_production_query_service.py \
  tests/unit/domain/services/test_chat_technical_description_intent_service.py \
  tests/unit/domain/services/test_chat_department_kpi_intent_service.py \
  tests/unit/application/services/test_external_action_selection_service.py \
  tests/unit/domain/services/test_chat_product_query_intent_service.py \
  tests/unit/application/use_cases/test_download_chat_file_use_cases.py \
  -q
```

---

## Pesquisa na internet (`web_search`)

**Tool interna nativa do chat** (não é skill nem action OpenAPI). Habilitada por `CHAT_WEB_SEARCH_ENABLED` + admin `webSearchEnabled`.

| Aspecto | Comportamento |
|---------|----------------|
| Seleção | `ChatWebSearchIntentService` + `ToolSelectionService` (triggers: «pesquise na internet», «busque na web», etc.) |
| Consulta | `WebSearchQueryService`: remove «a empresa», gera candidatos (`Tyco`, `Tyco International`, retry EN) |
| Provedores | `auto`: Tavily → Serper → Bing → **SearXNG** (OSS) → DuckDuckGo Instant Answer; fallback Wikipedia PT se todos falharem |
| Isolamento | `blocks_external_action_selection`: no mesmo turno **não** roda `execute_external_action`, roteador de actions nem loop agentic |
| Resposta simples | `ChatWebSearchDirectAnswerService` — 1 resultado útil ou fallback rápido (`directAnswer`, `skipRag`) |
| Síntese LLM | `ChatWebSearchSynthesisService` — com ≥ `CHAT_WEB_SEARCH_SYNTHESIS_MIN_RESULTS` fontes úteis, monta intro, seções, linha do tempo e conclusão em PT |
| Localização | `WebSearchPortugueseContentService` — Wikipedia PT quando snippet vier em inglês; entidades de uma palavra (ex.: «tyco») |
| Fontes na API | `webSources` → `sources[]` com `scope: web_search`, `sourceRef` = URL |
| Atividade de pesquisa | `webSearchResearch` na metadata da mensagem assistant; botão **Fontes · N** abre painel lateral (`ChatWebSearchResearchPanel`) |
| UI | Badges **Fontes** no rodapé (`ChatSources`) + links curtos no markdown como pills (`ChatMarkdown`) |
| Policy | `web-search-policy.md` — cite fontes; em `no_results`, não negar a busca |

**Pipeline típico (sucesso multi-fonte):** `ingress` → `tools` → `post_tool` → `direct_answer` → `web_search_synthesis` → `skip_rag`.

**Variáveis (compose / `.env`):**

| Variável | Default | Papel |
|----------|---------|--------|
| `CHAT_WEB_SEARCH_ENABLED` | `false` | Master switch |
| `CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED` | `true` | Resposta direta sem LLM principal |
| `CHAT_WEB_SEARCH_SYNTHESIS_ENABLED` | `true` | Síntese estruturada via LLM |
| `CHAT_WEB_SEARCH_SYNTHESIS_MIN_RESULTS` | `2` | Mínimo de snippets úteis para sintetizar |
| `CHAT_WEB_SEARCH_PROVIDER` | `auto` | Ordem: `tavily` → `serper` → `bing` → `searxng` → `duckduckgo`; ou valor único |
| `CHAT_WEB_SEARCH_RETRY_EN` | `true` | Retry em inglês quando PT/inicial vier vazio |
| `CHAT_WEB_SEARCH_MAX_RESULTS` | `5` | Limite por consulta |
| `CHAT_WEB_SEARCH_TIMEOUT_SECONDS` | `8` | Timeout HTTP dos provedores |
| `CHAT_WEB_SEARCH_SEARXNG_BASE_URL` | — (dev: `http://searxng:8080`) | Instância SearXNG self-hosted (`GET /search?format=json`) |
| `CHAT_WEB_SEARCH_SEARXNG_LANGUAGE` | `pt-BR` | Idioma enviado ao SearXNG |
| `CHAT_WEB_SEARCH_SEARXNG_CATEGORIES` | `general` | Categoria SearXNG (ex.: `general`, `images`) |
| `CHAT_WEB_SEARCH_TAVILY_API_KEY` / `SERPER` / `BING` | — | Credenciais opcionais (recomendado Tavily em prod com e-commerce) |

**SearXNG (dev):** serviço `searxng` no `infra/docker-compose.dev.yml` (profile `chat`, porta host **8088**). Config em `infra/searxng/settings.yml` com `search.formats: [html, json]` e `server.limiter: false` para chamadas internas da API.

**Testes:** `test_web_search_query_service.py`, `test_chat_web_search_intent_service.py`, `test_web_search_http_gateway.py`, `test_web_search_providers.py`, `test_chat_web_search_direct_answer_service.py`, `test_chat_web_search_synthesis_service.py`, `test_chat_web_search_research_activity_service.py`, `test_chat_web_search_blocks_external_actions.py`, `scripts/run_onda11_6_api_e2e.py` (caso W1).

**Deploy:** após alterar código Python, recriar/reiniciar `minha-delpi-ai-api` (Gunicorn não recarrega workers sozinho com imagem prod).

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
