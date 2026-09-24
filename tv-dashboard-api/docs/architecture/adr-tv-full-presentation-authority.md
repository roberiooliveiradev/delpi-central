# ADR — TV full presentation authority (geometry / style / defaults)

**Status:** DECIDED  
**Date:** 2026-09-24  
**Epic:** TV-DASHBOARD-PRESENTATION-001  
**Supersedes (partial):** FE-BE-002 principle
`MFE = AUTHOR + INTERACT + LAYOUT + GEOMETRY + PAINT`
for **persisted** geometry, style, visual options and create defaults.

## Context

Display/projection/format was already backend-owned (`adr-tv-display-format-ownership.md`).
Geometry, typography chrome, chart/table/KPI visual options and insert defaults still lived in the MFE (`create*Block`, `DEFAULT_*`, drag commit + autosave). VISTA already mutated `frame`/`style` via PresentationMutation; the editor did not.

## Decision

1. **Sole persistent authority** = `native_config` materializado pelo backend após PresentationMutation (ou load normalize).
2. **MFE allowlist:** EVENT_CAPTURE | TRANSIENT_EDITOR_UI | NETWORK | SERVER_MODEL_CACHE | VIEWPORT_TRANSFORM | PAINT | ACCESSIBILITY | LOADING_UI | ERROR_UI.
3. **Editor commit path:** `POST /playlists/{id}/slides/{slideId}/presentation-mutations` aplica ops tipadas (`create_block`, `upsert_block`, `align_blocks`, `reorder_block_z`, `duplicate_blocks`, …) e **persiste** via `TvPresentationWriteService`.
4. **Defaults canônicos:** `presentation_ops_content.json` → `blockDefaults` + `_with_block_defaults` (frame/style/**options/parts**). Factories FE são stub transitório até ack.
5. **Preserved from FE-BE-002:** paint-only de `display*` / `serverProjectionApplied` / `gaugeModel` / etc. — sem regressão de formatação.
6. **Abstraction Gate:** estender ops/schemas existentes — **proibido** framework genérico tipo `SetColorCommand`.
7. **Compat:** load legado normaliza no backend; aparência equivalente; sem restaurar authority FE.

## Contract freeze (E4)

| Surface | Owner | Consumers | Compat |
|---|---|---|---|
| `TvPresentationPatchV1` ops | `presentation_mutation/` + `presentation_ops_content.json` | VISTA GPT Actions, editor mutation endpoint | **ADDITIVE** |
| `POST …/presentation-mutations` | `slide_routes` + `PresentationMutationCommitService` | MFE editor | **ADDITIVE** |
| `PATCH …/slides/{id}` autosave | WriteService | MFE flush de estado já ack | **NONE** |
| `blockDefaults` catalog | content JSON | create/upsert | **ADDITIVE** |

## Consequences

- Ribbon/drag: preview local; commit → mutation → replace canonical config.
- Paint path publicado não deve inventar `fontSize ?? 16` / palette por índice quando o modelo canônico está ausente — diagnóstico explícito.
- FE-BE-002 docs devem citar este ADR para LAYOUT/GEOMETRY persistidos.
