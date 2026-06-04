# Contexto unificado vs. vestígios de «entidades»

## Modelo alvo (UI + prompt)

| Conceito | Onde vive |
|----------|-----------|
| O que o usuário vê e edita | `userContextItems`, chips `kind: context` |
| Texto no LLM | Bloco «Contexto adicionado pelo usuário…» (`ChatUserContextItemService.format_prompt_block`) |
| Código/filial para tools | Último item de contexto → `resolve_product_code` / `sync_operational_focus` |

## Uso interno legítimo (não é UI de entidade)

| Campo / serviço | Papel |
|-----------------|-------|
| `operationalFocus` | Cache derivado no snapshot (ex-`lastEntities` / `activeEntities`) |
| `ChatSnapshotOperationalFocus` | Leitura/escrita com compatibilidade de snapshots antigos |
| `sync_operational_focus` | **Único escritor** de produto/filial/armazém em `operationalFocus` |
| `productCode` em APIs/actions | Parâmetro operacional Protheus (não confundir com tipo «entidade» da memória) |
| `memory_type=entity` no Postgres | Só **período** em gravações novas; linhas antigas de produto/filial lidas como legado até expirar |
| `ChatEntityTrackerService` | SQL recente, pedido, anexo; depois passa por `sync_operational_focus` |
| `ChatReferenceResolutionService` | «esse produto», «mesma filial» → lê `lastEntities` já sincronizado |

## O que foi consolidado nesta revisão

- `ChatUserContextItemService.sync_operational_focus` no pré/pós-turno, entity tracker, overlay Postgres, pins.
- `load_active_overlay`: produto/filial/armazém vêm de `context_item`; linhas `entity` antigas só se não houver itens.
- `remove_pin`: remove `context_item` correspondente (não só `deactivate_entity`).
- `upsert_entity`: restrito a `period` (legado documentado).
- Regra em `.cursor/rules/chat-intelligence-base.mdc`.

## Vestígios que ainda existem (não são o modelo de UI)

- Leitura de `lastEntities` / `activeEntities` em mensagens antigas (`ChatSnapshotOperationalFocus.get`).
- Nomes `entity_key_for_kind`, `deactivate_entity` — mapeamento interno Postgres/API legado.
- `usage.entities` no admin (alias de `operationalFocus` na API de memória).
- Testes e regressões com snapshot `lastEntities` (contrato interno).
- Módulos **fora** do chat de sessão: RBAC entity, knowledge entity, `productCode` em presenters — domínios diferentes.

## Próximos passos opcionais

1. Migração one-shot: converter linhas `memory_type=entity` (product/branch/warehouse) em `context_item`.
2. ~~Renomear `lastEntities` → `operationalFocus`~~ — feito; leitura legada mantida.
3. Remover `entity_context_labels` e port `upsert_entity` quando não houver callers.
