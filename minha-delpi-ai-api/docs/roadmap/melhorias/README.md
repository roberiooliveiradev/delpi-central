# Melhorias — playbooks e análises (Minha DELPI Chat)

Documentação de evolução além das **ondas 1–11** (ver [roadmap principal](../README.md)). Os arquivos desta pasta consolidam playbooks que antes ficavam em `documentos/chat ia/` na raiz do monorepo.

## Status de implementação (maio/2026)

| Playbook / tema | Documento | Status |
|-----------------|-----------|--------|
| Contexto, memória e assertividade | [playbook_contexto_assertividade_minha_delpi_chat.md](./playbook_contexto_assertividade_minha_delpi_chat.md) | Fases **1–5** + **Fase 4** (`ai_chat_session_memory`, `POST .../memory/clear`) |
| Chips «Próximos passos» | [playbook_interatividade_botoes_minha_delpi_chat.md](./playbook_interatividade_botoes_minha_delpi_chat.md) | Fases **1–3** + menu por linha de tabela e **ponto de gráfico** (MFE); Fase **5** guiados em backlog |
| Anexos (Playbook 07) | [playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md](./playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md) | Indexação PDF/XLSX, welcome ao anexar, chips «Com o anexo» |
| Segurança e confiança (08) | [playbooks_melhoria_minha_delpi_chat/08_seguranca_permissoes_confianca.md](./playbooks_melhoria_minha_delpi_chat/08_seguranca_permissoes_confianca.md) | SQL seguro, trust badges, falha de API, confirmação de escrita + painel MFE; mensagem amigável em `ToolPermissionDeniedError` |
| Chat descontraído / personalidade | [playbook_chat_interativo_descontraido_minha_delpi.md](./playbook_chat_interativo_descontraido_minha_delpi.md) | Parcial — `personality_playbook.json`, starters, chips texto |
| Assistente administrativo (textos) | [playbook_assistente_administrativo_textos_minha_delpi_chat.md](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) | Fases **1–2** (detecção + policy, sem ERP); Fases **3–5** em backlog |
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

## Chat «comum» e atalhos operacionais

Sessões **sem agente escolhido** passam a herdar o agente de sistema configurado (`CHAT_PLATFORM_DEFAULT_AGENT_NAME`, padrão **Agente Minha DELPI**) para que chips como «Ver estoque» executem consultas reais. Chips operacionais só aparecem quando `actionsEnabled`; cliques em atalhos com código de produto **não entram no loop agentic** (fast path de seleção OpenAPI).

## Homologação local (api-externa)

Com **api-delpi** indisponível no ambiente local, use:

- `CHAT_PREFER_API_EXTERNA_PROVIDER=true` no `minha-delpi-ai-api` (já padrão em `docker-compose.dev.yml`)
- Providers no agente via API: `scripts/upsert_agent_provider.py --provider api-externa --enabled true --provider api-delpi --enabled false` (sem migration de dados)
- Smokes HTTP com `SMOKE_REQUIRE_API_EXTERNA=true` (padrão) — chip «Ver vendas» é omitido (rota só em api-delpi)
- Se o Alembic estiver em revision removida `p8q9r0s1t3`: `flask db stamp o7p8q9r0s1t2`

## Próximo backlog sugerido

1. **Playbook 07 completo** — indexação PDF/Excel; resposta automática ao upload.
2. **Interatividade Fase 4** — menu por nó de árvore / chip de contexto (gráfico feito no MFE).
3. **Admin textos Fase 3** — templates no composer e seção «Textos» no menu `+`.
4. **Playbook 08** — mensagens de permissão e badges de confiança no presenter.

## Regra

Melhorias de inteligência transversal devem ir no **chat base**, não duplicadas em prompts de agente isolados — ver `chat-intelligence-base.mdc`.
