# Changelog — contexto unificado e `operationalFocus` (jun/2026)

## Resumo

- UI e prompt: só `userContextItems` (chips `context`).
- Snapshot: `operationalFocus` substitui `lastEntities` e `activeEntities` (contrato único, sem leitura legada em produção).
- Resolução de código de produto prioriza contexto do usuário sobre histórico da conversa.
- Rótulos de chip preservam frase curta (ex.: `filial 02`).

## Breaking (aceitável — pré-produção)

| Antes | Depois |
|-------|--------|
| `contextSnapshot.lastEntities` | `contextSnapshot.operationalFocus` |
| `contextSnapshot.activeEntities` | removido (usar `operationalFocus`) |
| `usage.entities` na API de memória | `usage.operationalFocus` |
| Postgres `entity` para produto/filial | só `context_item`; `entity` fica para `period` |

## Arquivos centrais

- `ChatSnapshotOperationalFocus`
- `ChatUserContextItemService.sync_operational_focus`
- `ChatConversationMemoryService` (pré/pós-turno com `normalize`)

## Testes

```bash
cd minha-delpi-ai-api && .venv/bin/python -m pytest \
  tests/unit/domain/services/test_chat_snapshot_operational_focus.py \
  tests/unit/domain/services/test_chat_operational_focus_sync.py \
  tests/unit/application/services/test_chat_session_memory_service.py \
  tests/unit/domain/services/test_memory_context.py -q
```
