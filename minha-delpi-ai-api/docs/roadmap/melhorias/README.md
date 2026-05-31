# Melhorias — playbooks e análises (Minha DELPI Chat)

Documentação de evolução além das **ondas 1–11** (ver [roadmap principal](../README.md)). Os arquivos desta pasta consolidam playbooks que antes ficavam em `documentos/chat ia/` na raiz do monorepo.

## Status de implementação (maio/2026)

| Playbook / tema | Documento | Status |
|-----------------|-----------|--------|
| Contexto, memória e assertividade | [playbook_contexto_assertividade_minha_delpi_chat.md](./playbook_contexto_assertividade_minha_delpi_chat.md) | Fases **1–5** + **Fase 4** (`ai_chat_session_memory`, `POST .../memory/clear`) |
| Chips «Próximos passos» | [playbook_interatividade_botoes_minha_delpi_chat.md](./playbook_interatividade_botoes_minha_delpi_chat.md) | Fases **1–4** (tabela, gráfico, **árvore**, chip contexto); Fase **5** guiados em backlog |
| Anexos (Playbook 07) | [playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md](./playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md) | Indexação PDF/XLSX, welcome ao anexar, chips «Com o anexo» |
| Segurança e confiança (08) | [playbooks_melhoria_minha_delpi_chat/08_seguranca_permissoes_confianca.md](./playbooks_melhoria_minha_delpi_chat/08_seguranca_permissoes_confianca.md) | SQL seguro, trust badges, falha de API, confirmação de escrita + painel MFE; mensagem amigável em `ToolPermissionDeniedError` |
| Chat descontraído / personalidade | [playbook_chat_interativo_descontraido_minha_delpi.md](./playbook_chat_interativo_descontraido_minha_delpi.md) | Parcial — `personality_playbook.json`, starters, chips texto |
| Admin UX — abas (11) | [playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md) | Fases **1–4** concluídas (6 seções, Painel, status strip, cross-links, mobile) |
| Assistente administrativo (textos) | [playbook_assistente_administrativo_textos_minha_delpi_chat.md](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) | Fases **1–2** + templates **Textos** no menu `+` (MFE); Fases **3–5** avançadas em backlog |
| Análises pontuais | `analise_*.md`, `sugestoes_perguntas_*.md` | Referência; itens críticos migrados para código/testes |

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

## Chat «comum» e atalhos operacionais

No **chat comum**, o agente de sistema (`CHAT_PLATFORM_DEFAULT_AGENT_NAME`) pode executar consultas em background quando configurado, mas chips operacionais («Ver estoque», «Ver estrutura», etc.) só aparecem com **`userActivatedAgent`** — usuário escolheu o agente no composer (`session.agent_id` ou `agentId` na mensagem). Chips genéricos («O que você pode fazer?») e de texto seguem sem agente. Cliques em atalhos explícitos **não entram no loop agentic**.

## Homologação local (api-externa)

Com **api-delpi** indisponível no ambiente local, use:

- `CHAT_PREFER_API_EXTERNA_PROVIDER=true` no `minha-delpi-ai-api` (já padrão em `docker-compose.dev.yml`)
- Providers no agente via API: `scripts/upsert_agent_provider.py --provider api-externa --enabled true --provider api-delpi --enabled false` (sem migration de dados)
- Smokes HTTP com `SMOKE_REQUIRE_API_EXTERNA=true` (padrão) — chip «Ver vendas» é omitido (rota só em api-delpi)
- Se o Alembic estiver em revision removida `p8q9r0s1t3`: `flask db stamp o7p8q9r0s1t2`

## Ordem de implementação (arquitetura)

1. **Chat base** — `ChatIntentRouterService`, `adminDebug.intentRoute`, estágio `intent:*` no pipeline.
2. **Playbook 08** — `trustSignals` espelhados no painel admin debug.
3. **MFE** — menu contextual na árvore, chips de contexto clicáveis, seção «Textos» no menu `+`.
4. **Backlog** — Playbook 07 indexação completa; interatividade Fase 5 guiados.

## Próximo backlog sugerido

1. **Playbook 07 completo** — indexação PDF/Excel; resposta automática ao upload.
2. **Playbook 01** — `resolvedParams` e pendências ativas no router.
3. **Interatividade Fase 5** — fluxos guiados no MFE.

## Regra

Melhorias de inteligência transversal devem ir no **chat base**, não duplicadas em prompts de agente isolados — ver `chat-intelligence-base.mdc`.
