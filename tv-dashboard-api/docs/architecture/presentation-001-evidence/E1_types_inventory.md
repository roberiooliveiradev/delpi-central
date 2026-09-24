# E1 — Types inventory (TV-DASHBOARD-PRESENTATION-001)

**Evidence class:** `CONFIRMADO_NO_CODIGO`  
**Epic:** TV-DASHBOARD-PRESENTATION-001  
**Inventory date:** 2026-09-24  
**Sources:** discriminators, factories, BE defaults, native screens, render switches — measured from code, not manual catalogs.

---

## Totals

| Metric | Value | Derivation |
|---|---:|---|
| **TOTAL_COMPONENT_TYPES** | **16** | Discriminators of `ComunicadoBlock` (`comunicadoTypes.ts` L809–820) |
| **TOTAL_COMPONENT_VARIANTS** | **107** | 85 `ComunicadoShapeKind` + 15 `ComunicadoChartType` + 7 native `screenKey` |
| Shape kinds | 85 | `ComunicadoShapeKind` union L30–116 |
| Chart type variants | 15 | `ComunicadoChartType` L419–434 |
| Native screen keys | 7 | `native_screens.json` + `NativeSlideView` switch |
| BE `blockDefaults` keys | 13 | `presentation_ops_content.json` L507–757 (incl. `default`) |
| FE `create*` factories | 10 named + `createBlock` | `comunicadoHelpers.ts` |

### TOTAL_COMPONENT_TYPES (16)

| # | TYPE | Evidence |
|---|---|---|
| 1 | `heading` | `ComunicadoTextBlock` L284–286 |
| 2 | `text` | idem |
| 3 | `image` | `ComunicadoMediaBlock` L300–301 |
| 4 | `video` | idem |
| 5 | `shape` | `ComunicadoShapeBlock` L374–376 |
| 6 | `icon` | `ComunicadoIconBlock` L394–395 |
| 7 | `data_kpi` | `ComunicadoDataBlockType` L416 + `ComunicadoDataBlock` L600–601 |
| 8 | `data_chart` | idem |
| 9 | `data_table` | idem |
| 10 | `data_metric` | idem |
| 11 | `data_source` | `ComunicadoDataSourceBlock` L438–439 |
| 12 | `chart_view` | `ComunicadoChartViewBlock` L458–459 |
| 13 | `table_view` | `ComunicadoTableViewBlock` L470–471 |
| 14 | `canvas_table` | `ComunicadoCanvasTableBlock` L541–542 |
| 15 | `kpi_view` | `ComunicadoKpiViewBlock` L589–590 |
| 16 | `input` | `ComunicadoInputBlock` L570–571 |

Union canônica: `ComunicadoBlock` L809–820 — `CONFIRMADO_NO_CODIGO`.

> Nota: literais `"color"` / `"gradient"` / `"image"` em `ComunicadoBackground*` (L872–898) **não** são tipos de bloco.

---

## Discriminators — detalhe

### `ComunicadoShapeKind` (85) — L30–116

```
point, efficiency-pin,
rectangle, rounded-rect, snip-rect, snip-diag-rect, round-same-side-rect, round-1-rect,
ellipse, triangle, right-triangle, parallelogram, trapezoid, diamond,
pentagon, hexagon, heptagon, octagon, decagon, dodecagon,
cross, cylinder, cube, donut, pie, teardrop, frame, corner, folded-corner,
smiley, heart, lightning, cloud, moon, sun,
arrow-right, arrow-left, arrow-up, arrow-down, arrow-left-right, arrow-up-down,
chevron-right, chevron-left, notched-arrow-right, bent-arrow, u-turn-arrow,
quad-arrow, curved-right-arrow, striped-right-arrow,
star, star-4, star-6, star-7, star-8, star-10, star-12, star-16, star-24, burst-16,
banner, scroll, wave,
line, line-arrow-right, line-arrow-left, line-arrow-both, polyline, curve, scribble,
flowchart-process, flowchart-decision, flowchart-terminator, flowchart-data,
flowchart-document, flowchart-preparation,
callout-rect, callout-rounded, callout-cloud, callout-oval, callout-line,
equation-plus, equation-minus, equation-multiply, equation-divide, equation-equal
```

Runtime catalog: `COMUNICADO_SHAPE_KIND_VALUES` — `comunicadoShapeCatalog.ts` L304.

### `ComunicadoChartType` (15) — L419–434

| chartType | Label FE (`comunicadoChartView.ts` L5–22) | Basic paint (`chartTypeHasBasicRender`) |
|---|---|---|
| `line` | Linhas | yes → SeriesChartKind |
| `bar` | Colunas | yes |
| `horizontal_bar` | Barras | yes |
| `area` | Área | yes |
| `stacked_bar` | Colunas empilhadas | yes |
| `pie` | Pizza | yes |
| `doughnut` | Rosca | yes (maps to pie + innerRadius) |
| `scatter` | Dispersão | yes |
| `bubble` | Bolhas | yes |
| `radar` | Radar | yes |
| `combo` | Combinado | yes |
| `waterfall` | Cascata | yes |
| `funnel` | Funil | yes |
| `histogram` | Histograma | yes |
| `gauge` | Velocímetro | yes (dedicated path, not SeriesChartKind) |

Policy map: `chartDataPolicy.ts` `POLICIES_BASE: Record<ComunicadoChartType, …>` L124+.

### Native screens (7)

**Catalog BE:** `tv-dashboard-api/tv_app/content/native_screens.json` L1–77  
**Loader:** `playlist_repository.py` `load_native_screens_catalog`  
**Service switch:** `native_screen_data_service.py` L107–164  
**FE paint switch:** `NativeScreens.tsx` `NativeSlideView` L445–537

| screenKey | Category | FE renderer |
|---|---|---|
| `production_oee_overview` | production | `ProductionOeeOverviewScreen` |
| `production_otd_summary` | production | `ProductionOtdSummaryScreen` |
| `quality_ppm_summary` | quality | `QualityPpmSummaryScreen` |
| `supplies_stock_value` | supplies | `SuppliesStockValueScreen` |
| `supplies_stock_alert` | supplies | `SuppliesStockAlertScreen` |
| `strategic_indicators_hero` | strategic | `StrategicIndicatorsHeroScreen` |
| `custom_message` | general | `CustomMessageScreen` → `RichComunicadoStage` |

`custom_message` is the only native screen that hosts `ComunicadoBlock[]` (personalizado).

---

## FE factories — `create*Block` (`comunicadoHelpers.ts`)

| Factory | Lines | Produces TYPE | Key defaults |
|---|---|---|---|
| `createDataSourceBlock` | L340–362 | `data_source` | frame `{8,30,18,18}`, `style.zIndex=1`, `displayMode:"auto"` |
| `createChartViewBlock` | L364–384 | `chart_view` | `DEFAULT_COMUNICADO_CHART_OPTIONS` + `chartParts`, frame `{10,28,80,45}` |
| `createTableViewBlock` | L386–408 | `table_view` | `presetDefaultTableOptions` + `tableParts`, frame sized by picker |
| `createInputBlock` | L410–443 | `input` | `defaultFrame/Style("input")`, `defaultInputPartsMap()` |
| `createCanvasTableBlock` | L445–471 | `canvas_table` | 3×3 cells, `headerRow:true`, `mergeCanvasTableOptions` |
| `createKpiViewBlock` | L473–499 | `kpi_view` | `DECK_KPI_DEFAULTS.frame`, `kpiOptions`+`kpiParts`, role hero/secondary |
| `createDataBlock` | L501–535 | `data_*` | frames por `data_kpi`/`data_chart`/`data_table` |
| `createBlock` | L729–790 | heading/text/shape/image/video/icon/input/data_* | `defaultFrame`+`defaultStyle` |
| `createShapeBlock` | L792–798 | `shape` | wraps `createBlock("shape")` + efficiency-pin frame |
| `createIconBlock` | L800–802 | `icon` | wraps `createBlock("icon", iconName)` |

Helpers de default compartilhados:

- `defaultFrame` L537–597  
- `defaultStyle` L599–727  

---

## BE `blockDefaults` keys

**File:** `tv-dashboard-api/tv_app/content/presentation_ops_content.json` L507–757  
**Loader:** `presentation_ops_content_service.py` L69 (`defaults = _load().get("blockDefaults")`)

| Key | Present | Notes vs FE |
|---|---|---|
| `default` | yes | frame `{20,30,60,30}`, `zIndex:2` |
| `text` | yes | fontSize 28, white, center |
| `heading` | yes | fontSize 48 (FE create uses **56**) |
| `shape` | yes | fill/stroke/shadow Office-like |
| `image` | yes | objectFit contain |
| `video` | yes | objectFit contain |
| `data_source` | yes | bg `#0d2840` (FE create omits color) |
| `data_kpi` | yes | + `kpiParts` card/title/value/icon |
| `kpi_view` | yes | mirror of `data_kpi` |
| `data_chart` | yes | dark chrome |
| `chart_view` | yes | mirror of `data_chart` (sem chartOptions nested) |
| `data_table` | yes | |
| `table_view` | yes | |

**Ausentes no BE (só FE):** `icon`, `canvas_table`, `input`, `data_metric` — drift `CONFIRMADO_NO_CODIGO`.

---

## Materializers / projection / display

| Stage | Module | Role |
|---|---|---|
| Enrich entry | `ComunicadoDataEnrichmentService.enrich_blocks` (`comunicado_data_enrichment_service.py` ~L1191) | Fetch + bake |
| Shared resolve | `SlideDataResolutionService` → same enrich | preview-block ≡ present |
| Structural projection | `tv_view_projection_service.py` / FE `applyViewProjection` (`viewProjection.ts`) | KPI/chart/table encoding; no-op when `serverProjectionApplied` |
| Display strings | `DisplayFormatService` | `display*` / `serverDisplayApplied` |
| Native display | `native_screen_display_service.apply_native_screen_display` | G18 paint strings |
| Named text styles | `visualBoxTextFormat.materializeNamedStylesForContainerOverride` | FE authoring |
| Input free-layout frames | `materializeInputPartsFreeLayoutFromRoot` (plugin-ui) | FE chrome |
| Builder → ops | `POST …/to-presentation-ops` | draft → typed PresentationMutation ops |

---

## Render switches

### Block paint — `comunicadoBlockView.tsx` L115–350+

| Branch | Renderer |
|---|---|
| visual box (`heading`/`text`/`shape`) | `ComunicadoVisualBoxView` |
| `image` | `<img>` / `ComunicadoMediaPlaceholder` |
| `video` | `ComunicadoPresentationVideo` / `<video>` |
| `icon` | `ComunicadoIconGraphic` |
| `data_*` | `TvDataBlockView` |
| `data_source` | `DataSourceBlockView` (editor only; null on kiosk) |
| `chart_view` | `ChartViewBlockView` |
| `table_view` | `TableViewBlockView` |
| `canvas_table` | `ComunicadoCanvasTableView` |
| `kpi_view` | `KpiViewBlockView` |
| `input` | `ComunicadoInputBlockView` |

### Chart subtype — `chartViewBlockView.tsx`

- `gauge` → gauge widget  
- SeriesChartKind via `toSeriesChartKind` → `TvDataSeriesChartWidget` / `ConfigurableSeriesChart`  
- else → “em breve” placeholder  

### Stage host

- Editor + TV personalizado: `RichComunicadoStage`  
- Native (non-custom): `NativeSlideView`  

---

## Master table — TYPE × defaults × mutation × renderer × ownership

**Ownership legend (epic target):**

- **currentOwner** = who invents/writes the value today  
- **targetOwner** = canônico pós-001 (paint FE; semantics/defaults mutáveis via BE `presentation_ops` / enrich)

| TYPE | defaults FE | defaults BE | mutation path | renderer | currentOwner | targetOwner |
|---|---|---|---|---|---|---|
| `heading` | `createBlock`/`defaultStyle` L600–617; fontSize **56** | `blockDefaults.heading` L539–557; fontSize **48** | MFE `updateSelected` → draft → `updateSlide(nativeConfig)`; ops `upsert_block` / `patch_native_config` | `ComunicadoVisualBoxView` | FE `comunicadoHelpers` | BE `blockDefaults` + FE paint |
| `text` | `defaultStyle` L619–636; fontSize 28 | `blockDefaults.text` L519–537 | idem | `ComunicadoVisualBoxView` | FE helpers | BE defaults + FE paint |
| `shape` | `createShapeBlock` + `defaultStyle("shape")` L641–678 | `blockDefaults.shape` L559–574 | `updateSelected` (shape/vertices/connector/efficiencyPin) | `ComunicadoVisualBoxView` | FE shape catalog | FE paint; pin bands owner = `data_source.efficiencyPinBands` |
| `image` | `defaultFrame/Style` L565–639 | `blockDefaults.image` L576–586 | upload/library + `imageCrop` | media branch L189–205 | FE media | FE + asset service |
| `video` | L566–639 | `blockDefaults.video` L588–598 | upload/library | media L207–233 | FE media | FE + asset service |
| `icon` | `createIconBlock` / `defaultStyle("icon")` L679–689 | **ausente** | `updateSelected` iconName/style | `ComunicadoIconGraphic` | FE only | add BE default key |
| `data_source` | `createDataSourceBlock` L340–362 | `blockDefaults.data_source` L600–611 | `upsert_data_source`, `set_data_transform`, `updateSelected` | `DataSourceBlockView` (editor) | FE + PresentationMutation | **BE presentation_ops** |
| `data_kpi` | `createDataBlock` L501–535 | `blockDefaults.data_kpi` L613–654 | legacy path; prefer `kpi_view` | `TvDataBlockView` | FE legacy | deprecate → `kpi_view` |
| `data_chart` | idem | `blockDefaults.data_chart` L699–711 | legacy | `TvDataBlockView` | FE legacy | deprecate → `chart_view` |
| `data_table` | idem | `blockDefaults.data_table` L727–740 | legacy | `TvDataBlockView` | FE legacy | deprecate → `table_view` |
| `data_metric` | via `createDataBlock`/`defaultFrame` | **ausente** | legacy | `TvDataBlockView` | FE legacy | deprecate |
| `chart_view` | `createChartViewBlock` L364–384 | `blockDefaults.chart_view` L713–725 (frame/style only) | `updateSelected` chartOptions/Parts/Projection; ops `bind_visual` | `ChartViewBlockView` | FE options + BE enrich bake | **BE projection/display**; FE chrome options |
| `table_view` | `createTableViewBlock` L386–408 | `blockDefaults.table_view` L742–755 | tableOptions/Parts/Projection | `TableViewBlockView` | FE + BE enrich | **BE projection/display**; FE chrome |
| `kpi_view` | `createKpiViewBlock` L473–499 | `blockDefaults.kpi_view` L656–697 | kpiOptions/Parts/Projection | `KpiViewBlockView` | FE + BE enrich | **BE projection/display**; FE chrome |
| `canvas_table` | `createCanvasTableBlock` L445–471 | **ausente** | cells/merges/options | `ComunicadoCanvasTableView` | FE only | add BE default; enrich `serverCanvasTableProjectionApplied` |
| `input` | `createInputBlock` L410–443 | **ausente** | `input` + `inputParts` | `ComunicadoInputBlockView` | FE only | add BE default; runtime params stay session |

**Slide-level (not block TYPE):** `background`, `groupTransforms`, `dataFilters`, `brandThemeKey`, `speakerNotes`, `customFonts` — `ComunicadoConfig` L833–849.

**Native screens:** mutation via slide `nativeScreenKey` + `nativeConfig`; data via `NativeScreenDataService`; paint via `NativeSlideView`.

---

## Drift checklist (E1)

| Drift | Evidence |
|---|---|
| heading fontSize FE 56 vs BE 48 | helpers L602 vs JSON L547 |
| BE missing icon/canvas_table/input/data_metric | JSON keys vs type union |
| BE chart_view/table_view defaults omit chartOptions/tableOptions | JSON L713–755 vs FE factories |
| Dual legacy `data_*` vs `*_view` | both in union + blockDefaults |

All rows above: **CONFIRMADO_NO_CODIGO**.
