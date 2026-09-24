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
6. **Structural chart/KPI/table projection** is also backend-owned: enrich bake via `tv_view_projection_service.apply_view_projection_to_resolved` stamps `serverProjectionApplied: true`. When that flag is set, MFE `applyViewProjection` is a no-op (paint authority = bake). Client re-aggregation remains only for pre-enrich authoring drafts without the flag. Weekend chart filter (`excludeWeekends`) is baked server-side with the same stamp.
7. **TV-DASHBOARD-FE-BE-002 (2026-09-24):**
   - **G4** — bake is sole structural authority on enrich path (`serverProjectionApplied` → MFE no-op). Includes maxCategories/Outros, projectedGoal, empty-rows clear, excludeWeekends.
   - **G5/G21** — editor preview stamps `presentationStale` when spec fingerprint diverges; never treat prior `display*` as current.
   - **G18** — NativeScreens stock KPIs via `apply_native_screen_display` (DisplayFormatService).
   - **G24** — `chart.yAxisTicks[{value,displayLabel}]` materialized in enrich; MFE maps value → px only.
   - Principle: `MFE = AUTHOR + INTERACT + LAYOUT + GEOMETRY + PAINT` / `BACKEND = RESOLVE + PROJECT + AGGREGATE + FORMAT + MATERIALIZE`.
   - **Open residuals (post-inventory):** G6/G8/G10–12/G23; draft-only `applyViewProjection`; **G25+** EfficiencyPin format/bands, chart goal precedence at paint, gauge model, KPI auto sparkline/comparison, dead FE input-filter merge mirror, table cell format fallback, unused `resolveStaleSourceIdsForPreviewChange`.

## Consequences

- Rewrite presentation-parity rule: anti-pattern is dual format (client reformat after `serverDisplayApplied`) and dual text binding, not “never trust enrich display*”.
- Ribbon «Data abreviada» persists spec + refresh enrich (no sync local reformat of paint).
- Corpus of format cases must stay mirrored TS ↔ Python.
- Mutation/patch must not leave contradictory `textProjection.field` + `contentRuns.dataRef` on the same block after Campo-panel edits (`DisplayFormatService.sanitize_contradictory_text_binding` on upsert — clears dataRefs when single-field `textProjection` is set).
- **VISTA VERIFY / outcome:** after enrich/preview, read `resolved.displayText` / `displayRuns` / `kpi.displayValue` / `table.displayRows` / chart `displayLabel|displayValue` / `yAxisTicks` (or `DisplayFormatService.display_signals_for_verify`). Do not treat raw ISO / unformatted numbers as format success.
- **Rebaseline TV-DASHBOARD-FE-BE-001 (2026-09-24):** (1) client `applyViewProjection` that drops `display*` must clear `serverDisplayApplied`; (2) MFE `serializeComunicadoConfig` drops ghost `textProjection` when dataRefs paint; (3) canvas_table enrich materializes `displayRuns` per source.
- **Rebaseline TV-DASHBOARD-FE-BE-002 (2026-09-24):** G4 bake authority; G5/G21 `presentationStale`; G18 native display; G24 `yAxisTicks`. Open: G6/G8/G10–12/G23 + **G25+** (EfficiencyPin, gauge/goal paint, KPI auto-context, dead FE filter-merge mirror). Inventários explore pré-diff (client always re-encode / native sem display / sem ticks) ficam **superados** pelo código desta tarefa.
