# ADR — TV display formatting ownership + text binding single-owner

**Status:** DECIDED  
**Date:** 2026-09-24  
**Context:** MFE reformatted display values (`formatDisplayValue` / `textViewProjection`) while the inspector could write `textProjection` that paint ignored when `contentRuns.dataRef` existed (ROL/Meta → filter dates). Platform rule: frontend does not decide domain presentation of data.

## Decision

1. **`tv-dashboard-api` owns display formatting** for TV slides. Enrich (`SlideDataResolutionService` → `enrich_blocks`) applies `DisplayFormatService` and emits ready-to-paint strings on `display*` fields (`displayText`, `displayRuns`, `displayValue`, `displayLabel`) plus `serverDisplayApplied: true`.
2. **MFE is paint-only** for those values. Slide paint path must not call `formatDisplayValue` when `serverDisplayApplied` (or when `display*` is present). Kit TS formatter remains for admin/sample UI outside the slide path until retired.
3. **Persisted contract** stays on the block: `displayFormat` / legacy `valueFormat` / `textProjection` / `contentRuns[].dataRef` — authoring writes the **spec**; enrich materializes the **string**.
4. **Text binding single-owner:** paint authority is `contentRuns[].dataRef` when any run has a field; otherwise `textProjection`. The Element «Campo dinâmico» panel **reads and writes that same owner**. Writing a single field from the panel **consolidates** (materialize `textProjection`, clear dataRefs) so UI and canvas cannot diverge.
5. **VISTA** persists format via typed ops / `displayFormat` allowlist (`DisplayFormatHintsService`); VERIFY uses enrich `display*`, not client reformat.
6. **Structural chart/KPI projection** (`applyViewProjection` / `chartDataPolicy`) remains client-applied until a follow-up closes bake parity; this ADR does **not** reintroduce trusting incomplete structural bake as the sole visual source. Display **strings** from enrich are authoritative when `serverDisplayApplied`.

## Consequences

- Rewrite presentation-parity rule: anti-pattern is dual format (client reformat after `serverDisplayApplied`) and dual text binding, not “never trust enrich display*”.
- Ribbon «Data abreviada» persists spec + refresh enrich (no sync local reformat of paint).
- Corpus of format cases must stay mirrored TS ↔ Python.
- Mutation/patch must not leave contradictory `textProjection.field` + `contentRuns.dataRef` on the same block after Campo-panel edits (`DisplayFormatService.sanitize_contradictory_text_binding` on upsert — clears dataRefs when single-field `textProjection` is set).
- **VISTA VERIFY / outcome:** after enrich/preview, read `resolved.displayText` / `displayRuns` / `kpi.displayValue` / `table.displayRows` / chart `displayLabel|displayValue` (or `DisplayFormatService.display_signals_for_verify`). Do not treat raw ISO / unformatted numbers as format success.
