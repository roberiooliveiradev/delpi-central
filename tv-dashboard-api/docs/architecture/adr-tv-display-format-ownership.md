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
7. **TV-DASHBOARD-FE-BE-002 (2026-09-24 → semantic zero):**
   - **G4** — bake sole structural authority (`serverProjectionApplied`); paint views do not call `applyViewProjection`.
   - **G5/G21** — `presentationStale` on fingerprint divergence.
   - **G6/G23** — `effectiveParams` / `requestedParams` + contextValues via catalog defaults + dateRangePreset (same order as gateway).
   - **G8** — overlay/filmstrip `pickOverlayResolved` stale-safe.
   - **G10** — canvas `displaySeries[field]`.
   - **G11/G28** — `kpiPresentation` (value/comparison/progress/spark).
   - **G12** — `resolvedRouteLabel` / `fieldLabelsEffective` on views.
   - **G18** — NativeScreens via `apply_native_screen_display`.
   - **G24/G34** — `yAxisTicks`; MFE never regenerates tick labels when map present.
   - **G25** — `efficiencyPinPresentation`.
   - **G26/G27** — `chart.effectiveGoal` / `gaugeModel`.
   - **G29** — FE filter merge = AUTHORING_SPEC fingerprint only; paint uses enrich `effectiveParams`.
   - **G30–G33** — table paint prefers `displayRows`; dead stale helper deprecated; `hasServerDisplayPaint` PAINT-only; legacy `data_*` modes not used on paint path.
   - Principle: `MFE = AUTHOR + INTERACT + LAYOUT + GEOMETRY + PAINT` / `BACKEND = RESOLVE + PROJECT + AGGREGATE + FORMAT + MATERIALIZE`.
  - **Superseded for persisted LAYOUT/GEOMETRY/style/defaults (2026-09-24):** see `adr-tv-full-presentation-authority.md` (TV-DASHBOARD-PRESENTATION-001). Paint-only `display*` / `serverProjectionApplied` remains.

## Consequences

- Rewrite presentation-parity rule: anti-pattern is dual format (client reformat after `serverDisplayApplied`) and dual text binding, not “never trust enrich display*”.
- Ribbon «Data abreviada» persists spec + refresh enrich (no sync local reformat of paint).
- Corpus of format cases must stay mirrored TS ↔ Python.
- Mutation/patch must not leave contradictory `textProjection.field` + `contentRuns.dataRef` on the same block after Campo-panel edits (`DisplayFormatService.sanitize_contradictory_text_binding` on upsert — clears dataRefs when single-field `textProjection` is set).
- **VISTA VERIFY / outcome:** after enrich/preview, read `resolved.displayText` / `displayRuns` / `kpi.displayValue` / `table.displayRows` / chart `displayLabel|displayValue` / `yAxisTicks` (or `DisplayFormatService.display_signals_for_verify`). Do not treat raw ISO / unformatted numbers as format success.
- **Rebaseline TV-DASHBOARD-FE-BE-001 (2026-09-24):** (1) client `applyViewProjection` that drops `display*` must clear `serverDisplayApplied`; (2) MFE `serializeComunicadoConfig` drops ghost `textProjection` when dataRefs paint; (3) canvas_table enrich materializes `displayRuns` per source.
- **Rebaseline TV-DASHBOARD-FE-BE-002 (semantic zero):** ALL_SEMANTIC_PROJECTION_BACKEND_OWNED / ALL_BUSINESS_DISPLAY_BACKEND_OWNED; paint views consume enrich only; VISTA VERIFY via `display_signals_for_verify` (+ kpiPresentation / yAxisTicks / gaugeModel / efficiencyPinPresentation / displaySeries).
