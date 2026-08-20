# commercial-api — documentação

API dona do estado Delpi do **Portal Comercial** (carteiras, worklist, contatos locais, enrichment BFF, **sala de interação**). Reads TOTVS via gateway para **api-delpi** — o MFE não chama api-delpi direto.

## Roadmap / atas

| Doc | Uso |
|-----|-----|
| [ATA-ALINHAMENTO-AGO2026-2.md](../../docs/12-roadmap-e-evolucao/commercial/ATA-ALINHAMENTO-AGO2026-2.md) | Ata alinhamento 2 — P2-SALA **P0 Existe**; P2-CONF / Diretoria / MyVEG = backlog |
| [ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md](../../docs/12-roadmap-e-evolucao/commercial/ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md) | T10 P0 (sala) · T11 Graph |
| [API-ROUTES.md](../../docs/12-roadmap-e-evolucao/commercial/API-ROUTES.md) | Contrato de rotas — § 3.21 interaction rooms |
| [DATA-MODEL.md](../../docs/12-roadmap-e-evolucao/commercial/DATA-MODEL.md) | Schema `commercial` — § 8.1 sala (V019–V021) |
| [WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/commercial/WIREFRAMES.md) | WF-SALA |
| [PERFIS-E-PERMISSOES.md](../../docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md) | `access` / `manage` (sem code novo da sala) |
| [SCOPE-OWNERSHIP.md](../../docs/12-roadmap-e-evolucao/commercial/SCOPE-OWNERSHIP.md) | Ownership Portal × PVA |
| [plugins/commercial/README.md](../../plugins/commercial/README.md) | Rotas UI + tabela HTTP da sala |
| [ROADMAP-INTERACTION-ROOM.md](../../docs/12-roadmap-e-evolucao/commercial/ROADMAP-INTERACTION-ROOM.md) | Roadmap sala — **E1–E7 entregues**; E8 docs |

## Architecture (neste pacote)

| Doc | Tema |
|-----|------|
| [architecture/realtime-worklist.md](./architecture/realtime-worklist.md) | WS worklist / presença / **sala** (`room.*`) |

**Estoque FIFO / kanban:** `OpenOrderStockAllocationService` + `EnrichOpenOrdersKanbanService` gravam `estoque_alocado` **antes** de `kanbanStageCounts`. Badge da nav e chip «Pode faturar» compartilham essa contagem.

## Sala de interação (P0)

| Peça | Onde |
|------|------|
| HTTP `/interaction-rooms*` | `interaction_room_routes.py` · § 3.21 |
| Migrations | `V019__interaction_rooms.sql` · `V020__task_source_interaction_message.sql` · `V021__interaction_wall_global_unique.sql` |
| Conteúdo PT / kinds | `commercial_app/content/pt-BR/interaction_room.json` · `interaction_mention_kinds.json` |
| Tarefa a partir da mensagem | `create_task_from_interaction_message` (+ mensagem `task_ref`) |
| System events | use case `post_system_message` (**sem** rota HTTP) — `otd_event` / `process_stage` |
| Anexos | `owner_type=room_message` em `/attachments` (volume `commercial-attachments`; teto 10 × 20 MB) |
| Mensagem | `body_text` markdown; POST/PATCH 422 se HTML cru; PATCH `mentions[]` = replace; reply via `parent_id` |
| Acesso | `InteractionRoomAccessService` — **`commercial.access` global** na borda; WS `interaction` + `room:{uuid}` |
| MFE | `plugins/commercial` — inbox, page, panel na ficha; **nunca** api-delpi |

Confirmação de pedidos (P2-CONF) e Graph Outlook/Teams (T11) permanecem backlog — não misturar com o contrato da sala.
