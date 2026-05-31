# Changelog — playbooks `docs/roadmap/melhorias` (maio/2026)

Implementação incremental dos playbooks além da Fase 5 de contexto/assertividade (`c432e742`).

## Contexto (`playbook_contexto_assertividade`)

| Entrega | Detalhe |
|---------|---------|
| Fase 2 (serviços) | `ChatFollowUpIntentService`, `ChatReferenceResolutionService` extraídos de `ChatWorkingMemoryService` |
| Fase 3 (UI) | `metadata.contextChips` + barra **Contexto ativo** no plugin (`ChatContextBar`) |
| Comportamento | Preferência «só versão final» em `ChatBehaviorInstructionService` |

**Fase 4:** tabela `ai_chat_session_memory` + `POST /chat/sessions/{id}/memory/clear`.

## Playbook 11 — restauração de funcionalidades (sem desfazer organização)

| Restaurado | Detalhe |
|------------|---------|
| 10 abas planas | Barra **Acesso direto** (Conhecimento, Métricas, Diretrizes, Skills, …) |
| RBAC em Ferramentas | `AdminRbacPanel` de volta em Plataforma → Ferramentas (também no Painel) |
| Inteligência em Métricas | `ChatIntelligenceSettingsPanel` na aba Métricas + Plataforma → Inteligência |
| Alertas globais | `AdminShellAlerts` junto com a faixa de status |
| Sub-abas no mobile | Sub-nav visível com rolagem horizontal (não oculta) |
| URLs legadas | `/admin/metrics`, `/admin/skills`, etc. redirecionam ao destino correto |

## Roadmap `docs/roadmap/melhorias` (fechamento 31/05/2026)

| Entrega | Detalhe |
|---------|---------|
| Índice | `STATUS_ROADMAP_MELHORIAS.md` — status dos 40+ arquivos da pasta |
| Playbooks raiz | `playbook_melhoria_pesquisa_web` e `playbook_ampliacao_graficos` versionados com Fase 1 marcada |
| Playbook 01 | `resolvedFromMemory` em `intentRoute` para follow-ups operacionais |
| Playbook 02 | `smoke_product_sales_routing.py` — vendas → `/sales` (api-delpi) |
| Playbook 11 | Mockups 01–10 implementados; mockup 11 aguardando aprovação |

## Arquitetura — ordem chat base → MFE (maio/2026)

| Camada | Entrega |
|--------|---------|
| Chat base | `ChatIntentRouterService` (`classify`, `resolve_executed`); `intentRoute` em `adminDebug`; estágio `intent:{nome}`; `resolvedFromMemory` |
| Playbook 08 | `trustSignals` mesclados no `adminDebug` (cliente admin) + resumo no `ChatAdminDebugPanel` |
| MFE | `buildTreePointMenuActions` + menu na árvore; chips de contexto clicáveis; seção **Textos** no menu `+` (`CHAT_TEXT_HOME_STARTERS`) |
| Smoke | `scripts/smoke_intent_route.py` — valida `adminDebug.intentRoute` e `intent:*` no pipeline |

## Correções (problemas reportados em homologação)

| Problema | Correção |
|----------|----------|
| Árvore e gráfico sumiram no chat (só Texto/Tabela) | Gráfico lê `stock.items`; parents `product`+`parents` viram árvore; `chartPresentation` no metadata; MFE lê gráfico secundário |
| «Corrija» + anexo → «sem acesso a documentos» | Instrução textual explícita + policy; `text_task` com contexto de anexo no prompt |
| «Consulte estoque e escreva e-mail» sem e-mail | `ChatTextTaskComposerService` anexa rascunho após tools no turno misto |
| «E-mail com dados da tabela» → capacidades/RAG | `is_email_from_operational_data_request` + resposta direta com resumo da consulta |
| Roteiro 360° com `Operations=[{...}]` | `_format_guide_like_item` no presenter do analyser |
| «qual o estoque do produto X?» → «Sobre esta consulta» | `ChatCapabilitiesService` não confundia pergunta operacional com inquiry de capacidade |

## Playbook 07 — Anexos (início)

- `attachmentFollowUpSuggestions` no metadata do assistant quando a mensagem do usuário trouxe anexos.
- `ChatAttachmentWelcomeService` — resposta automática ao enviar anexo (mensagem vazia ou «segue anexo»).
- Correção de quebras de linha na extração CSV/XLSX/PDF (`ChatAttachmentTextExtractor`).
- Provider no agente via API (`PUT /chat/agents/{id}/providers`) ou `scripts/upsert_agent_provider.py` — **sem** migration de dados; local usa api-externa; «Ver vendas»/faturamento exige api-delpi habilitada na API.
- Chips: Resumir, Corrigir, Traduzir, Extrair pendências, Criar checklist (`personality_playbook.json`).

## Interatividade (`playbook_interatividade_botoes`)

| Entrega | Detalhe |
|---------|---------|
| Chips por outcome `text` | Após tarefas textuais (`followUpChips.text` no playbook) |
| Starters | Texto administrativo na home (`textHomeStarters` / `CHAT_TEXT_HOME_STARTERS`) |

| Menu por linha de tabela | `ChatTableRowMenu` + `buildTableRowMenuActions` (Fase 4 interatividade) |
| Menu por ponto de gráfico | `buildChartPointMenuActions` + clique em barra/fatia/ponto (`ChatRichChart`) |
| Preferência api-externa | `CHAT_PREFER_API_EXTERNA_PROVIDER` + smokes `SMOKE_REQUIRE_API_EXTERNA` |

## Playbook 08 — Segurança e confiança (início)

| Entrega | Detalhe |
|---------|---------|
| SQL seguro | `ChatSqlSafetyService` bloqueia DELETE/UPDATE/… no `ChatToolContextService` |
| Confiança UI | `metadata.trustSignals` + `ChatTrustBadges` no MFE |
| Textos | Seção `security` em `external_action_responses.json` |

| Falha de API | `ChatSecurityMessagingService` — não inventa dado quando consulta falha |
| Confirmação de escrita | `ChatWriteConfirmationService` bloqueia DELETE/escrita sem «confirmo» |

| Confirmação no MFE | `actionConfirmation` + `ChatActionConfirmationPanel` (Confirmar/Cancelar) |
| Permissão de tool | `ToolPermissionDeniedError` usa texto `security.actionNotPermitted` |

**Backlog:** badges em admin debug ampliado; menu em árvore/chip de contexto (interatividade).

## Playbook 11 — Admin UX (abas)

| Entrega | Detalhe |
|---------|---------|
| Navegação | 6 seções + sub-abas (`adminNavigation.ts`, `AdminShellTopbar`) |
| Deep links | `/admin`, `/admin/conhecimento/documentos`, `/admin/agentes/especializacao/:id` |
| Painel | `AdminOverviewTab` + RBAC; default `/admin` → Painel |
| Reagrupamento | Inteligência fora de Métricas; RBAC fora de Ferramentas; Skills → Comportamentos |

| Fase 4 polish | Status strip, cross-links Governança/Agentes↔Builder, animação sub-abas, mobile sem sub-nav duplicada, testes 6 seções |

**Playbook 11 concluído** (fases 1–4). E2E admin dedicado permanece evolução futura.

## Atalhos «Próximos passos» vs chat comum

| Entrega | Detalhe |
|---------|---------|
| Agente padrão | `ChatPlatformDefaultAgentService` — sessão sem agente usa agente de sistema (nome/ID via env) |
| Chips condicionais | Operacionais exigem `userActivatedAgent` (agente no composer); genéricos/texto sem agente |
| Sem agentic em chip | `ChatFollowUpChipQueryService` + `should_skip_agentic_loop` para consultas explícitas dos atalhos |

## Infra local (gateway)

| Problema | Correção |
|----------|----------|
| 502 em `/core-api/*` após restart de containers | `gateway/nginx.dev.conf` — upstreams com variável + `resolver` (DNS dinâmico Docker) |

**Backlog interatividade:** menu em gráfico/chip de contexto, fluxos guiados (`ChatGuidedFlow`).

## Admin textos (`playbook_assistente_administrativo_textos`)

| Entrega | Detalhe |
|---------|---------|
| Fase 1–2 | Policy `administrative-writing.md`, `ChatTextTaskIntentService`, estágio `text_task` no turn prep (sem tools/RAG) |

**Backlog:** templates no input (Fase 3), skill registry dedicada, testes E2E com LLM.

## Descontraído (`playbook_chat_interativo_descontraido`)

| Entrega | Detalhe |
|---------|---------|
| Parcial | Starters e chips de texto alinhados ao `personality_playbook.json` |

**Backlog:** ampliar `stream.json` / variantes por outcome.

## Pesquisa web — Fase 4 (cruzamento ERP)

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatWebSearchErpCrossReferenceService` — seção «Cruzamento ERP × web» |
| Pipeline | `ChatToolContextService` mantém fontes web em turno híbrido |

## Autoajuda — Fase 1 (identity ↔ catálogo)

| Entrega | Detalhe |
|---------|---------|
| Conteúdo | `identity.json` — `catalogSync`, respostas alinhadas a KPIs/web/?/system |
| CI | `scripts/check_identity_catalog_alignment.py` — versão e `featureIds` vs `features_catalog` |
| Catálogo | Feature `production_indicators` |

## Autoajuda — Fase 5 (personalização por perfil)

| Entrega | Detalhe |
|---------|---------|
| API | `userContext`, `availability.requiresProfilePermission`; cards ERP ocultos sem `chat.tools.use` |
| Registry | `AssistantCapabilitiesRegistry.resolve_availability` diferencia perfil vs agente vs API |
| MFE | Badges «Seu perfil não tem permissão» / «Agente sem API habilitada» no `ChatHelpPanel` |

## Autoajuda — Fase 5 (novidades e métricas)

| Entrega | Detalhe |
|---------|---------|
| API | `contextualHighlights` + `releaseVersion` em `/chat/assistant/catalog` |
| MFE | Banner «Novidades» na home vazia e no painel `?` |
| Métricas | `POST /chat/assistant/help-events` — log `help-adoption` |

## Autoajuda — Fase 5 (parcial)

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatHelpErrorFollowUpService` — chips após falha (`helpErrorFollowUpSuggestions`) |
| MFE | Grupo «Ajuda após erro» em `ChatMessageList` |
| CI | `check_help_pr_gate.py` — actions/skills exigem atualização de ajuda |

## Autoajuda — Fase 3 (mapeamento KPIs e produto)

| Entrega | Detalhe |
|---------|---------|
| Gerador | Regras comercial, financeiro, qualidade, RH, LMP, SQL; tokens de produto (fornecedores, estrutura, …) |
| Catálogo | Novas features `commercial_indicators`, `financial_indicators`, `quality_indicators`, `hr_indicators`, `engineering_*`, `data_sql` |
| Drift | Match por marcador mais específico; ignora `/` e `/health`; `system_metadata` mapeia rotas `/system/*` |

## Autoajuda — Fase 3 (geração do catálogo)

| Entrega | Detalhe |
|---------|---------|
| Gerador | `AssistantCapabilitiesCatalogGenerator` — actions, skills, `requiredActions`, `linkedSkills` |
| Scripts | `generate_assistant_capabilities_catalog.py` (`--check` / `--write`); check CI estendido |
| Conteúdo | `features_catalog.json` com bloco `generation` e paths não mapeados |

## Autoajuda — Fase 4 (painel de ajuda)

| Entrega | Detalhe |
|---------|---------|
| API | `GET /chat/assistant/catalog?q=&agentId=` — catálogo, busca e buckets de disponibilidade |
| Serviço | `ChatAssistantCatalogService` |
| MFE | `ChatHelpPanel`, botão `?` na topbar, exemplos enviam pergunta ao chat |

## Autoajuda — Fase 3 (validação e H1–H10)

| Entrega | Detalhe |
|---------|---------|
| CI | `check_assistant_capabilities_catalog.py` valida JSON e referências |
| Testes | `test_chat_self_help.py` — casos H1–H10 do playbook |
| Capacidades | Respostas para estoque, permissões, exclusão e textos |

## Autoajuda — Fase 2 (catálogo)

| Entrega | Detalhe |
|---------|---------|
| Conteúdo | `features_catalog.json`, `assistant_release_notes.json` |
| Serviço | `AssistantCapabilitiesRegistry` — busca, buckets de disponibilidade |
| Chat | «O que mudou?»; ajuda por tópico prioriza catálogo |
| Smoke | `scripts/smoke_features_catalog.py` |

## Autoajuda — Fase 1 (parcial)

| Entrega | Detalhe |
|---------|---------|
| `capabilities.json` | `featureAnswers` — web, lousa, gráfico, anexo, agente |
| `ChatHelpFollowUpService` | `helpFollowUpSuggestions` + chips «Explorar» no MFE |
| Starters | «Como usar», pesquisa web, lousa em `chatHomeStarters.ts` |
| Smoke | `scripts/smoke_help_capabilities.py` |

## Pesquisa web — salvar fontes no projeto

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatWebSearchSaveSourcesService` — resposta direta «salvar fontes» → `POST` ingest como `project_source` |
| UX | Chip «Salvar fontes» no playbook pós-pesquisa |

## Pesquisa web — Fase 5 (UX)

| Entrega | Detalhe |
|---------|---------|
| Backend | `ChatWebSearchFollowUpService` + chips no `personality_playbook.json` |
| MFE | Grid de cards de fontes, tag oficial, chips «Após pesquisa web» |

## Pesquisa web — Fase 4 (integração anexo / ERP)

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatWebSearchIntegrationService` — modos híbridos e queries extras |
| Pipeline | Companion operacional em produto+web; anexo no `build_context` |
| UX | Painel com rótulo de integração |

## Pesquisa web — Fase 3 (avaliação de fontes)

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatWebSearchSourceEvaluationService` — tipos, score, exclusão com `preferOfficial` |
| Pipeline | `WebSearchTool.enrich_payload`; avisos em resposta direta; metadata `webSearchResearch` |
| MFE | `ChatWebSearchResearchPanel` — tag oficial, confiança, observações |
| Testes | `test_chat_web_search_source_evaluation_service.py`; smoke estendido |

## Testes

- `test_chat_text_task_intent_service.py` (T1/T6/T7 lógica)
- `test_chat_reference_resolution_service.py`
- `test_chat_follow_up_intent_service.py`
- Inclusão em `run_onda11_validation.sh`
