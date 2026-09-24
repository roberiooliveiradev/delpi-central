# E6 — Geometria

**Status:** IMPLEMENTED

| Capacidade | Op / serviço | Editor wire |
|---|---|---|
| Align / distribute / slide-align | `align_blocks` + `block_layout_service` | `alignSelected` → `commitAlignBlocks` |
| Z-order | `reorder_block_z` | bring/send → `commitReorderBlockZ` |
| Move/resize frame | `upsert_block` deep-merge `frame` | `updateBlock`/`updateSelected` → `commitUpsertBlocks` (ack) |
| Quick KPI layout | `SlideAutoLayoutService` (pré-existente) | mutation path pós-create |

Transient preview permanece local; commit = mutation.
