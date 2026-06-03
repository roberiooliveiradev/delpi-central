# Changelog — contexto manual, Q&A e fechamento documental (jun/2026)

Extensões pós-Fase 9 do [playbook memória e contexto](../roadmap/playbook-memoria-e-contexto.md) e sincronização do índice [STATUS_ROADMAP_MELHORIAS](../roadmap/melhorias/STATUS_ROADMAP_MELHORIAS.md).

---

## 1. Contexto livre (usuário)

| Item | Detalhe |
|------|---------|
| Serviço | `ChatUserContextItemService` — classificação automática (produto, filial, tabela, nota, arquivo, conhecimento) |
| Persistência | `memory_type=context_item` em `ai_chat_session_memory` (sem migration nova) |
| API | `POST/DELETE /chat/sessions/{id}/memory/context-items` |
| MFE | `ChatAddContextDialog` — texto, arquivo, drag-and-drop; barra `ChatContextBar` |

---

## 2. Perguntas e respostas no contexto

| Item | Detalhe |
|------|---------|
| Tipos | `question`, `answer` (par via `question` + `answer` no body) |
| API | `role`, `messageId`, deduplicação por mensagem ao re-adicionar |
| MFE | Ações nas mensagens (marcador); par Q+A no assistente; lista «Da conversa» no diálogo «+» |
| Chips | `chip.value` = `id` do item (remoção via DELETE) |

---

## 3. UX e deploy

| Item | Detalhe |
|------|---------|
| Modais | `ModalPortal` tela cheia, `z-index` 1600, `data-theme` — memória usada e adicionar contexto |
| Barra de contexto | Grid mobile, tokens de tema, safe-area |
| Migrations | `minha-delpi-ai-api/docker-entrypoint.sh` — `flask db upgrade` no boot (dev/prod) |

---

## 4. Correções correlatas (assertividade / SQL)

- `ChatWorkingMemoryService` — carryover `previousProductCodes`; compare «com o anterior» fora do fluxo BOM
- Sessão longa — review SQL e incremental não bloqueados por ambiguidade de memória (`dbe374d4`, `c859f0e5`)

---

## 5. Validação

```bash
cd minha-delpi-ai-api
./scripts/run_memory_context_validation.sh
pytest tests/unit/domain/services/test_chat_user_context_item_service.py -q
```

MFE: `npm run test -- --run src/ui/chatContextFromMessage.test.ts`

---

## 6. Roadmap — o que permanece em backlog

Itens **parciais** com escopo explícito (não reimplementar do zero): ver [BACKLOG_ROADMAP.md](../roadmap/melhorias/BACKLOG_ROADMAP.md) — Admin mockup 11, onboarding 10, visão/OCR Onda 13, gráficos refinamentos.

**Memória e contexto (playbook principal):** fechado nas Fases 1–9 + extensões acima.
