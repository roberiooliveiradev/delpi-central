# Melhorias — playbooks e análises (Minha DELPI Chat)

Documentação de evolução além das **ondas 1–11** (ver [roadmap principal](../README.md)). Os arquivos desta pasta consolidam playbooks que antes ficavam em `documentos/chat ia/` na raiz do monorepo.

## Status de implementação (maio/2026)

| Playbook / tema | Documento | Status |
|-----------------|-----------|--------|
| Contexto, memória e assertividade | [playbook_contexto_assertividade_minha_delpi_chat.md](./playbook_contexto_assertividade_minha_delpi_chat.md) | **Fases 1–2 e 5** entregues na API; fases 3–4 (UI chips de contexto, tabela `ai_chat_session_memory`) em backlog |
| Chips «Próximos passos» | [playbook_interatividade_botoes_minha_delpi_chat.md](./playbook_interatividade_botoes_minha_delpi_chat.md) | Queries com `product_code` resolvido; smoke `scripts/smoke_follow_up_chips.py` |
| Chat descontraído / personalidade | [playbook_chat_interativo_descontraido_minha_delpi.md](./playbook_chat_interativo_descontraido_minha_delpi.md) | Parcial (playbook + `personality_playbook.json`) |
| Assistente administrativo (textos) | [playbook_assistente_administrativo_textos_minha_delpi_chat.md](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) | Backlog |
| Análises pontuais | `analise_*.md`, `sugestoes_perguntas_*.md` | Referência; itens críticos migrados para código/testes |

**Changelog detalhado:** [`../../changelog/2026-05-contexto-memoria-assertividade.md`](../../changelog/2026-05-contexto-memoria-assertividade.md).

**Arquitetura vigente:** [`../../architecture/chat-intelligence-base.md`](../../architecture/chat-intelligence-base.md) (memória de turno, assertividade, policies).

## Smokes automatizados

| Script | O que valida |
|--------|----------------|
| `scripts/smoke_follow_up_chips.py` | Chips «Próximos passos» com código de produto nas queries |
| `scripts/smoke_context_assertiveness_multiturn.py` | Score e flags de assertividade em conversa multi-turno |
| `scripts/run_onda11_validation.sh` | Regressão Onda 11 + bloco Fase 5 (pytest + smoke assertividade no E2E) |

## Regra

Melhorias de inteligência transversal devem ir no **chat base** (`ChatIntelligencePipelineService`, serviços em `app/application/services/` e `app/domain/services/`), não duplicadas em prompts de agente isolados — ver regra do repositório `chat-intelligence-base.mdc`.
