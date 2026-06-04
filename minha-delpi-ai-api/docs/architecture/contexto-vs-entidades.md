# Contexto unificado (sem `lastEntities`)

## Modelo

| Conceito | Onde vive |
|----------|-----------|
| O que o usuário vê e edita | `userContextItems`, chips `kind: context` |
| Texto no LLM | Bloco «Contexto adicionado pelo usuário…» (`ChatUserContextItemService.format_prompt_block`) |
| Código/filial para tools | `userContextItems` → `resolve_product_code` |
| Cache interno do turno | `operationalFocus` no `contextSnapshot` |

Chaves **removidas** do contrato (pré-produção): `lastEntities`, `activeEntities`. Se aparecerem em JSON local antigo, `ChatSnapshotOperationalFocus.strip_removed_keys` as descarta.

## Escrita do cache

Somente `ChatUserContextItemService.sync_operational_focus` grava produto/filial/armazém em `operationalFocus`, derivando de:

1. `userContextItems` (prioridade quando existem itens), ou
2. sinais do turno (tool, mensagem explícita) quando não há itens de contexto.

`ChatWorkingMemoryService` e `ChatEntityTrackerService` alimentam o turno; o sync reconcilia com o contexto do usuário.

## Persistência (`ai_chat_session_memory`)

| `memory_type` | Conteúdo |
|---------------|----------|
| `context_item` | Itens de contexto (usuário + auto) |
| `entity` | Apenas **período** (`period`) |
| `behavior` | Preferências de comportamento |

Produto/filial/armazém **não** são mais persistidos como `memory_type=entity`.

## Serviços que leem `operationalFocus`

- `ChatSnapshotOperationalFocus.get` / `set` / `normalize`
- `ChatReferenceResolutionService` (esse produto, mesma filial)
- `ChatProductQueryIntentService.resolve_product_code`
- `ChatIntentRouterService`, seleção de actions, refinamentos operacionais

## API memória de sessão

`GET /chat/sessions/{id}/memory/context` → `usage.operationalFocus` (mapa compacto) e `usage.userContextItems` (rótulos para o modal).

## Referência

- [`chat-intelligence-base.md`](./chat-intelligence-base.md)
- [`session-memory.md`](./session-memory.md)
- Changelog: [`../changelog/2026-06-contexto-operational-focus.md`](../changelog/2026-06-contexto-operational-focus.md)
