# Melhorias — playbooks e análises (Minha DELPI Chat)

Documentação de evolução além das **ondas 1–11** (ver [roadmap principal](../README.md)). Os arquivos desta pasta consolidam playbooks que antes ficavam em `documentos/chat ia/` na raiz do monorepo.

**Índice completo (40 arquivos):** [STATUS_ROADMAP_MELHORIAS.md](./STATUS_ROADMAP_MELHORIAS.md).

## Status de implementação (maio/2026)

| Playbook / tema | Documento | Status |
|-----------------|-----------|--------|
| Contexto, memória e assertividade | [playbook_contexto_assertividade_minha_delpi_chat.md](./playbook_contexto_assertividade_minha_delpi_chat.md) | Fases **1–5** + **Fase 4** (`ai_chat_session_memory`, `POST .../memory/clear`) |
| Chips «Próximos passos» | [playbook_interatividade_botoes_minha_delpi_chat.md](./playbook_interatividade_botoes_minha_delpi_chat.md) | Fases **1–5** + menus contextuais (tabela, árvore, gráfico, chip) |
| Anexos (Playbook 07) | [playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md](./playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md) | Indexação PDF/XLSX, welcome ao anexar, chips «Com o anexo» |
| Segurança e confiança (08) | [playbooks_melhoria_minha_delpi_chat/08_seguranca_permissoes_confianca.md](./playbooks_melhoria_minha_delpi_chat/08_seguranca_permissoes_confianca.md) | SQL seguro, trust badges, falha de API, confirmação de escrita + painel MFE; mensagem amigável em `ToolPermissionDeniedError` |
| Chat descontraído / personalidade | [playbook_chat_interativo_descontraido_minha_delpi.md](./playbook_chat_interativo_descontraido_minha_delpi.md) | Parcial — `personality_playbook.json`, starters, chips texto |
| Admin UX — abas (11) | [playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md) | **Revertido** no MFE (10 abas planas); mockups Markdown por aba → implementação no final — ver [`11_admin_ux_reorganizacao_abas/00_processo_refatoracao.md`](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas/00_processo_refatoracao.md) |
| Assistente administrativo (textos) | [playbook_assistente_administrativo_textos_minha_delpi_chat.md](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) | Fases **1–2** + templates **Textos** no menu `+` (MFE); Fases **3–5** avançadas em backlog |
| Correção de texto | [playbook_correcao_texto_minha_delpi_chat.md](./playbook_correcao_texto_minha_delpi_chat.md) | Documentado — Fase **1 parcial** (`correct` + `text_task`); Fases 2–5 planejadas |
| Escrita de e-mails | [playbook_escrita_emails_minha_delpi_chat.md](./playbook_escrita_emails_minha_delpi_chat.md) | Fases **1–5** concluídas |
| Pesquisa web | [playbook_melhoria_pesquisa_web_minha_delpi_chat.md](./playbook_melhoria_pesquisa_web_minha_delpi_chat.md) | Fases **1–5** concluídas |
| Gráficos ampliados | [playbook_ampliacao_graficos_minha_delpi_chat.md](./playbook_ampliacao_graficos_minha_delpi_chat.md) | Fases **1–3** + **heatmap** (4); dashboard multi-card backlog |
| Análise de desenhos DELPI | [playbook_skill_analise_desenhos_delpi.md](./playbook_skill_analise_desenhos_delpi.md) | Parcial (MVP) — skill `drawing-analysis-delpi`, smoke `smoke_drawing_analyser.py` |
| Visão / OCR documentos (chat base) | [playbook_skill_visao_documentos_ocr_delpi.md](./playbook_skill_visao_documentos_ocr_delpi.md) | Parcial (MVP) — [Onda 13](../inteligencia-chat-onda-13-skill-visao-documentos-ocr.md); Tesseract+PyMuPDF; Docling/VLM backlog |
| Metadados Protheus | [api-delpi-chat-intelligence-audit.md](../api-delpi-chat-intelligence-audit.md) | `/system/tables/*` + [smoke](../../testing/smoke-system-metadata-homologacao.md) |
| Análises pontuais | `analise_*.md`, `sugestoes_perguntas_*.md` | Referência arquivada — ver [STATUS](./STATUS_ROADMAP_MELHORIAS.md) |

**Changelogs:**

- [Fase 5 contexto/assertividade](../../changelog/2026-05-contexto-memoria-assertividade.md)
- [Pacote playbooks maio/2026](../../changelog/2026-05-melhorias-playbooks.md)

**Arquitetura vigente:** [`../../architecture/chat-intelligence-base.md`](../../architecture/chat-intelligence-base.md).

## Serviços novos (chat base)

| Serviço | Playbook |
|---------|----------|
| `ChatFollowUpIntentService` | Contexto — follow-up |
| `ChatReferenceResolutionService` | Contexto — reuso de entidade |
| `ChatTextTaskIntentService` | Admin textos — modo sem API |
| [playbook_escrita_emails_minha_delpi_chat.md](./playbook_escrita_emails_minha_delpi_chat.md) | E-mails corporativos — `ChatEmailIntentService`, validador, chips |
| [playbook_correcao_texto_minha_delpi_chat.md](./playbook_correcao_texto_minha_delpi_chat.md) | Correção/revisão — `ChatTextTaskIntentService` (`correct`), validador e chips (planejados) |
| `ChatWorkingMemoryService.build_context_chips` | Contexto + interatividade — UI |
| `ChatSessionMemoryService` | Fase 4 — memória persistida entre reloads |
| `ChatSqlSafetyService` | Playbook 08 — bloqueio SQL destrutivo |
| `ChatTrustSignalsService` | Playbook 08 — sinais de confiança no metadata |
| `ChatSecurityMessagingService` | Playbook 08 — mensagens quando API falha |
| `ChatWriteConfirmationService` | Playbook 08 — confirmação antes de escrita/destrutiva |
| `ChatIntentRouterService` | Playbook 01 — roteamento de intenção (`adminDebug.intentRoute`) |

## Smokes automatizados

| Script | O que valida |
|--------|----------------|
| `scripts/smoke_follow_up_chips.py` | Chips «Próximos passos» com código de produto |
| `scripts/smoke_context_assertiveness_multiturn.py` | Assertividade multi-turno |
| `scripts/run_onda11_validation.sh` | Regressão Onda 11 + Fase 5 + serviços de melhorias |
| `scripts/smoke_operational_routing.py` | Estoque com produto não cai em «Sobre esta consulta» |
| `scripts/smoke_session_memory_persist.py` | Memória persistida + `memory/clear` |
| `scripts/upsert_agent_provider.py` | Habilitar/desabilitar provider no agente (API, sem migration) |
| `scripts/smoke_sql_safety.py` | Bloqueio de SQL destrutivo (Playbook 08) |
| `scripts/smoke_intent_route.py` | `intentRoute` + estágio `intent:*` (Playbook 01) |
| `scripts/smoke_product_sales_routing.py` | Vendas do produto → `/sales` (api-delpi), não estoque/busca |
| `scripts/smoke_web_search_planning.py` | Planejamento web (`plannedQueries`, modo rápido/profundo) |

## Chat «comum» e atalhos operacionais

No **chat comum**, o agente de sistema (`CHAT_PLATFORM_DEFAULT_AGENT_NAME`) pode executar consultas em background quando configurado, mas chips operacionais («Ver estoque», «Ver estrutura», etc.) só aparecem com **`userActivatedAgent`** — usuário escolheu o agente no composer (`session.agent_id` ou `agentId` na mensagem). Chips genéricos («O que você pode fazer?») e de texto seguem sem agente. Cliques em atalhos explícitos **não entram no loop agentic**.

## Homologação local (api-externa)

Com **api-delpi** indisponível no ambiente local, use:

- `CHAT_PREFER_API_EXTERNA_PROVIDER=true` no `minha-delpi-ai-api` (já padrão em `docker-compose.dev.yml`)
- Providers no agente via API: `scripts/upsert_agent_provider.py --provider api-externa --enabled true --provider api-delpi --enabled false` (sem migration de dados)
- Smokes HTTP com `SMOKE_REQUIRE_API_EXTERNA=true` (padrão) — chip «Ver vendas» é omitido (rota só em api-delpi)
- Smoke único: `PYTHONPATH=. .venv/bin/python scripts/smoke_api_externa_local.py` (configura providers + estoque + chips; pausa 65s entre smokes — `SMOKE_RATE_LIMIT_PAUSE=0` para pular)
- Se o Alembic estiver em revision removida `p8q9r0s1t3`: `flask db stamp o7p8q9r0s1t2`

## Ordem de implementação (arquitetura)

1. **Chat base** — `ChatIntentRouterService`, `adminDebug.intentRoute`, estágio `intent:*` no pipeline.
2. **Playbook 08** — `trustSignals` espelhados no painel admin debug.
3. **MFE** — menu contextual na árvore, chips de contexto clicáveis, seção «Textos» no menu `+`.
4. **Backlog** — Playbook 07 indexação completa; interatividade Fase 5 guiados.

## Próximo backlog

Ver **[BACKLOG_ROADMAP.md](./BACKLOG_ROADMAP.md)** (prioridades: Admin mockup 11, anexos 07, router 01, heatmap, onboarding 10).

## Regra

Melhorias de inteligência transversal devem ir no **chat base**, não duplicadas em prompts de agente isolados — ver `chat-intelligence-base.mdc`.
