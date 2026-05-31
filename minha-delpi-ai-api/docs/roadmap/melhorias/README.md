# Melhorias — playbooks e análises (Minha DELPI Chat)

Documentação de evolução além das **ondas 1–11** (ver [roadmap principal](../README.md)). Os arquivos desta pasta consolidam playbooks que antes ficavam em `documentos/chat ia/` na raiz do monorepo.

## Status de implementação (maio/2026)

| Playbook / tema | Documento | Status |
|-----------------|-----------|--------|
| Contexto, memória e assertividade | [playbook_contexto_assertividade_minha_delpi_chat.md](./playbook_contexto_assertividade_minha_delpi_chat.md) | Fases **1–5** + **Fase 4** (`ai_chat_session_memory`, `POST .../memory/clear`) |
| Chips «Próximos passos» | [playbook_interatividade_botoes_minha_delpi_chat.md](./playbook_interatividade_botoes_minha_delpi_chat.md) | Fases **1–3** + menu por linha de tabela (MFE); Fase **5** guiados em backlog |
| Anexos (Playbook 07) | [playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md](./playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md) | Indexação PDF/XLSX, welcome ao anexar, chips «Com o anexo» |
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

## Smokes automatizados

| Script | O que valida |
|--------|----------------|
| `scripts/smoke_follow_up_chips.py` | Chips «Próximos passos» com código de produto |
| `scripts/smoke_context_assertiveness_multiturn.py` | Assertividade multi-turno |
| `scripts/run_onda11_validation.sh` | Regressão Onda 11 + Fase 5 + serviços de melhorias |
| `scripts/smoke_operational_routing.py` | Estoque com produto não cai em «Sobre esta consulta» |
| `scripts/smoke_session_memory_persist.py` | Memória persistida + `memory/clear` |

## Homologação local (api-externa)

Com **api-delpi** indisponível no ambiente local, use:

- `CHAT_PREFER_API_EXTERNA_PROVIDER=true` no `minha-delpi-ai-api` (já padrão em `docker-compose.dev.yml`)
- Smokes HTTP com `SMOKE_REQUIRE_API_EXTERNA=true` (padrão) — chip «Ver vendas» é omitido (rota só em api-delpi)

## Próximo backlog sugerido

1. **Playbook 07 completo** — indexação PDF/Excel; resposta automática ao upload.
2. **Interatividade Fase 4** — menu em gráfico / chip de contexto.
3. **Admin textos Fase 3** — templates no composer e seção «Textos» no menu `+`.
4. **Playbook 08** — mensagens de permissão e badges de confiança no presenter.

## Regra

Melhorias de inteligência transversal devem ir no **chat base**, não duplicadas em prompts de agente isolados — ver `chat-intelligence-base.mdc`.
