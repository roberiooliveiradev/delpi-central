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
| Console `WebSocket … CONNECTION_REFUSED` / Engine.IO 400 no dev | `/socket.io` com `proxy_pass http://core-api:8000` estático (`^~`); portal usa `polling` + `websocket` |
| Regressão homologação | `smoke_features_catalog` valida handshake `socket.io` via `SMOKE_BASE_URL` |

## Interatividade — Fase 5 (fluxos guiados)

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatGuidedFlowService` — passos + chips a partir de `capabilities.json` (`guidedFlows`, `interactive.cards`) |
| Metadata | `guidedFlow`, `guidedFlowCards`, `guidedFlowSuggestions` no assistente |
| MFE | `ChatGuidedFlowBlock` — passos numerados e cards por área |

**Backlog interatividade:** menu em gráfico/chip de contexto (Fase 4).

## Admin textos (`playbook_assistente_administrativo_textos`)

| Entrega | Detalhe |
|---------|---------|
| Fase 1–2 | Policy `administrative-writing.md`, `ChatTextTaskIntentService`, estágio `text_task` no turn prep (sem tools/RAG) |
| Fase 3 (parcial) | Home: blocos «Consultas» + cards «Textos»; menu + com modelos (`chatTextTemplates.ts`) |
| Smoke | `smoke_text_task_routing.py` — correção sem tools |

**Backlog:** lousa como editor de rascunho (Fase 3), preferências sessão (Fase 4), tarefas mistas (Fase 5).

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

## Gráficos — Fase 3 e UX (combo, scatter, alternar tipo)

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatChartTypeSelectionService` — `combo`, `scatter`, `histogram`, `gauge` |
| MFE | `ComposedChart`, `ScatterChart`, `RadialBarChart`; toggles para trocar tipo no gráfico |

## Gráficos — Fase 2 (tipos e seleção automática)

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatChartTypeSelectionService` — linha temporal, ranking horizontal, donut, grouped/stacked |
| API | `ExternalActionResultPresenter._try_chart_from_rows` usa seleção automática |
| MFE | `ChatRichChart` renderiza `horizontal_bar`, `donut`, `stacked_bar`, `grouped_bar`, `multi_line` |

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

## Metadados Protheus — roteamento «qual a tabela de produtos?»

| Entrega | Detalhe |
|---------|---------|
| Seleção | `qual a tabela` (com artigo), `description=produtos`, prioridade antes de busca de produto; fallback `list_actions` para `/system/*` |
| Intent | `subIntent: system_metadata` no router (evita `product_lookup` só por conter «produto») |
| Smoke | `scripts/smoke_system_table_routing.py` (unit + API + chat E2E) |
| Testes | Regressão + `test_select_system_table_search_with_article_qual_a_tabela` |
| Apresentação | `_present_system_tables_search` (lista SX2 com relevância) |
| Erros | `systemMetadataQueryFailed` quando ERP/SQL indisponível; `error` no metadata da tool |
| Fix | Carteira de pedidos em aberto não cai mais em `/sales` genérico (`wants_open_orders` vs `wants_sales`) |
| Doc | [smoke-system-metadata-homologacao.md](../testing/smoke-system-metadata-homologacao.md) |

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

## Gráficos — dashboard multi-card (Fase 4)

| Entrega | Detalhe |
|---------|---------|
| Backend | `ChatDashboardPresentationService` + `build_dashboard_presentation` (LMP summary/charts/items) |
| MFE | `ChatRichDashboard` — grid de KPI + gráficos + tabela |
| Metadata | `preferredFormat: dashboard` quando painel composto |

## Gráficos — heatmap (Fase 4)

| Entrega | Detalhe |
|---------|---------|
| Backend | `_try_heatmap_from_rows` + detecção matriz em `ChatChartTypeSelectionService` |
| MFE | `HeatmapGrid` em `ChatRichChart` (eixo X/Y + `valueKey`) |
| Testes | `test_chat_chart_type_selection_service`, `test_external_action_result_presenter_chart` |

## Auditoria api-delpi — smoke por domínio (mock)

| Entrega | Detalhe |
|---------|---------|
| Fixture | `api_delpi_domain_routing_cases.py` — 9 domínios, 18 casos |
| Smoke | `smoke_api_delpi_domain_routing.py` — mock + amostra chat (intent/tools) |
| Doc | `docs/testing/smoke-api-delpi-domain-routing.md` |

## Anexos — indexação e preview (Playbook 07)

| Entrega | Detalhe |
|---------|---------|
| Serviço | `ChatAttachmentPreviewService` — colunas de planilha, `attachmentSummaries` |
| Index | `preview` em metadata ao indexar; CSV com separador `;` |
| Welcome | Linha «Leitura do arquivo» com colunas quando indexado |
| Smoke | `scripts/smoke_attachment_index_welcome.py` |

## Roteamento — `resolvedParams` (Playbook 01)

| Entrega | Detalhe |
|---------|---------|
| Router | `intentRoute.resolvedParams` — `productCode` na mensagem ou herdado do histórico |
| Compat | Alias `resolvedFromMemory` mantido no mesmo payload |

## Catálogo de funcionalidades — drift CI

| Entrega | Detalhe |
|---------|---------|
| Generator | `drift_report` ignora `actionCount`/`enabledActionCount` (dependem do DB no momento da geração) |
| Generator | `write_catalog` preserva contagens anteriores quando `--no-db` ou actions vazias |

## Onboarding — primeiro uso (Playbook 10)

| Entrega | Detalhe |
|---------|---------|
| Conteúdo | `assistant/onboarding.json` — welcome, cards, tour, modo treinamento |
| Chat base | `ChatOnboardingService`, resposta direta via `ChatCapabilitiesService` |
| API | `onboarding` em `GET /chat/assistant/catalog` |
| MFE | Cards no `ChatEmptyState`, `ChatOnboardingTour` (localStorage) |
| MFE | Home do chat — `chat-design-system.css`, título em duas linhas, chips só sem cards do onboarding |
| MFE | Coluna única centralizada na home (`mdc-chat-empty-composer__column`); cards em flex centralizado (sem última linha à esquerda) |
| MFE | Atalhos com `{{productCode}}`, `{{searchQuery}}`, etc. — diálogo obrigatório antes de enviar (`ChatShortcutPromptDialog`); bloqueio se `{{…}}` chegar ao `sendMessage` |
| API | Chips e templates do playbook retornam placeholders; sem injetar código 10080001 no backend |
| MFE | Tour interativo — spotlight no alvo, digitação demo no composer, menu + e chips de exemplo (`chatTourStepEffects.ts`) |
| API | `tourSteps` com `target`, `demoQuery`, `openPlusMenu`, `demoSuggestions` (6 passos em `onboarding.json`) |
| Chips | `onboardingFollowUpSuggestions` após «me ensine a usar» |
| Perfis | 5 presets (engenharia, compras, comercial, diretoria, admin) + `profileId` na API e seletor no MFE |
| Marcos | `ChatOnboardingMilestoneService` — `milestoneCelebrations` (máx. 1/turno), histórico em `onboardingMilestonesAchieved` |

## Anexos — imagens, comparação e status (Playbook 07)

| Entrega | Detalhe |
|---------|---------|
| Indexação | PNG/JPG/WebP com metadados (`image_metadata`) e preview `kind=image` |
| Comparação | `ChatAttachmentMultiCompareService` + estágio `attachment_compare` |
| MFE | Status de leitura no composer e chips de mensagem (`chatAttachmentStatus.ts`) |
| Chips | «Comparar» em follow-up quando há 2+ anexos |
| Upload | `readingStatus` + `preview` na resposta do POST; upload antecipado no composer com sessão ativa |
| Formatos legados | `.doc` / `.xls` aceitos no upload com `readingStatus` orientando conversão para DOCX/XLSX |
| OCR imagem | `ChatAttachmentImageOcrService` (Tesseract opcional); preview com `ocr`/`ocrExcerpt` quando há texto |

## Gráficos — salvar na lousa + export dashboard (Fase 5)

| Item | Entrega |
|------|---------|
| MFE | Botão **Lousa** em `ChatRichChart` e dashboard; markdown via `chartCanvasMarkdown.ts` |
| Dados | Exporta visão filtrada (Top/Janela/períodos) como tabela na lousa |
| CSV | `dashboardExportCsv.ts` — botão **↓ CSV** no header do `ChatRichDashboard` (KPI + tabela + gráfico) |
| Smoke | `smoke_api_externa_local.py` — pausa entre smokes para evitar HTTP 429 |

## Admin — design system e responsividade

| Item | Entrega |
|------|---------|
| CSS | `admin-design-system.css` — tema escuro consistente, KPIs, toolbars, breakpoints |
| Fix | Faixa de status sem fundo cinza claro; mobile nav e KPIs em coluna |

## Admin — deploy MFE e shell v2

| Item | Entrega |
|------|---------|
| Build | Correções TS no MFE; rebuild `minha-delpi-chat` publica admin em 6 seções |
| UX | Rótulo `admin-v2-6secoes` no topbar para validar bundle atual |
| Doc | `subir-ambiente-dev.md` — alterar código exige `docker compose … up --build` no plugin |

## Admin — atalho Métricas → Inteligência

| Item | Entrega |
|------|---------|
| MFE | Callout em `AdminMetricsTab` com botão para Plataforma → Inteligência |
| UX | Esclarece que toggles de pipeline saíram de Métricas (Playbook 11) |

## Exportação tabela expandida — XLSX/PDF (31/05/2026)

| Problema | Correção |
|----------|----------|
| XLSX falha em «Estoque por filial/armazém» | `sanitizeSheetName` — aba Excel não aceita `/` no nome |
| PDF sem tabela | `jspdf-autotable` v5 — usar `autoTable(doc, …)` em vez de `doc.autoTable` |

## Homologação — atalhos com preenchimento (31/05/2026)

| Verificação | Resultado |
|-------------|-----------|
| Login `rober` / token Keycloak | OK (`auth` 200, `smoke_identity_profile`) |
| `smoke_follow_up_chips.py` | OK — chips API com `{{productCode}}`; ações api-externa |
| `smoke_features_catalog.py` | OK — onboarding/tour com placeholders (container API) |
| `smoke_admin_endpoints.py` | OK |
| Vitest MFE | `chatShortcutPrompt` (6, incl. regressão regex), `chatHomeStarters`, `chatTourTooltipPosition`, `exportUtils` — 15 testes OK |
| `smoke_shortcut_placeholders.py` | OK — JSON + follow-up service sem `10080001` fixo nas queries de chip |
| MFE bundle | `App-KpZWzapI.js` — diálogo `Consulta ao chat` + `onShortcutPromptRequired` |
| Catálogo HTTP | `starterCards` / `demoQuery` com `{{productCode}}` (sem código fixo na API) |
| Diálogo automático | `onShortcutPromptRequired` abre o formulário ao bloquear `{{…}}` (sem só banner de erro) |
| Z-index modal | `mdc-chat-shortcut-prompt-backdrop` na camada 1400 (`modal-layer.css`) |
| Travamento na home | Corrigido — tour **não abre mais sozinho**; layout/scroll debounced; digitação demo ≤8 updates (`ecac82f4` + follow-up) |
| Card do tour vs. controle | `computeTourTooltipLayout` — acima do composer no rodapé; centrado; sem overlap; mobile `visualViewport` |
| **Consultar produto travava** | Bug: `RegExp` global — `.test()` em `hasShortcutPlaceholders` zerava `matchAll`; `fields.length === 0` → `sendMessage` + `onShortcutPromptRequired` em loop |
| Fluxo unificado atalhos | `promptAndSendMessage` + guarda de reentrância (`384cbd45`, `ecac82f4`) |
| Banner de placeholder | Título «Complete os campos antes de enviar» (não «Não consegui gerar…») |
| Deploy MFE dev | `docker compose build` + `up -d minha-delpi-chat` (31/05) |

**Manual:** na home (perfil Engenharia) → **Consultar produto** → modal com **Código do produto** → **Enviar pergunta**. Tour só após clicar **Ver tour rápido do chat** (não inicia no load). Hard refresh após deploy.

**Script:** `./scripts/run_chat_shortcut_homologation.sh` — placeholders + login + catálogo + follow-up (pausa configurável para rate limit).

**Revalidação pós-fix regex (31/05, host):** login Keycloak OK; catálogo Engenharia `Consultar produto` → `{{productCode}}`; smokes placeholders + identity + features_catalog OK; `tsc -b` MFE OK.

**Commits:** `f8d571bf`, `5633a777`, `0dcda7da`, `6670e510`, `a5c7e9e9`, `384cbd45`, `ecac82f4`, `df271df7`, `a1c9c33d`, `2500fc14`, `fd75c884`.

## Homologação — api-externa local

| Item | Entrega |
|------|---------|
| Script | `smoke_api_externa_local.py` — `upsert_agent_provider` + smokes operacionais |

## Gráficos — UX Fase 5 (filtros, zoom, períodos)

| Item | Entrega |
|------|---------|
| Filtro Top N | Select 5/10/20 categorias por valor no `ChatRichChart` |
| Zoom temporal | Janela 6/12/24 pontos em séries com eixo de tempo |
| Comparar períodos | Toggle quando dados trazem campo `period`/`periodo`; barras agrupadas |

## Gráficos — mini dashboard por agente (Fase 4)

| Item | Entrega |
|------|---------|
| API | `miniDashboard` + `recommendations` em `GET /chat/agents/{id}/stats` |
| Serviço | `ChatAgentMiniDashboardService` (KPI + gráfico de barras + até 4 recomendações) |
| MFE | `AgentMiniDashboard` no admin (Agentes) e no builder |

## Admin UX — 6 seções (Playbook 11)

| Item | Entrega |
|------|---------|
| Navegação | Painel, Conhecimento, Agentes, Qualidade, Plataforma, Governança + sub-abas |
| Rotas | `/admin`, `/admin/<seção>/<sub-aba>`, agente em `/admin/agentes/especializacao/:id` |
| Painel | `AdminOverviewTab` com KPIs, links rápidos e RBAC |
| Plataforma | Inteligência separada de Ferramentas; RBAC só no Painel |

## Roteamento — pendências ativas e feedback (Playbook 01)

| Entrega | Detalhe |
|---------|---------|
| Chat base | `ChatActivePendingService` — `metadata.activePending` em respostas `operational_parameter` |
| Router | Turno seguinte: `clarification_answer` com `resolvedParams` (código de produto, ano de período) |
| Feedback | Thumbs down com motivos de roteamento retorna `routingSnapshot` de `adminDebug.intentRoute` |
| MFE | Motivo `wrong_intent` em `chatFeedbackReasons.ts` + `personality_playbook.json` |
| Testes | `test_chat_active_pending_service.py` |

## Interatividade — Fase 4 (chip de contexto)

| Entrega | Detalhe |
|---------|---------|
| MFE | `chatContextChipActions.ts` — menu contextual (produto, filial, formato) |
| MFE | `ChatContextBar.tsx` — clique/botão direito via `ChatTableRowMenu` |
| Docs | `BACKLOG_ROADMAP.md`, STATUS/README roadmap sincronizados |

## Testes

- `test_chat_text_task_intent_service.py` (T1/T6/T7 lógica)
- `test_chat_reference_resolution_service.py`
- `test_chat_follow_up_intent_service.py`
- Inclusão em `run_onda11_validation.sh`
