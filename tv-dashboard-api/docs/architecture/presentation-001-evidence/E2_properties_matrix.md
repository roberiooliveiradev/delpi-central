# E2 — Persisted properties matrix (TV-DASHBOARD-PRESENTATION-001)

**Evidence class:** `CONFIRMADO_NO_CODIGO`  
**Epic:** TV-DASHBOARD-PRESENTATION-001  
**Scope:** every persisted (or explicitly runtime-only) property on `ComunicadoConfig` / `ComunicadoBlock` without “etc.”  
**Sources:** `comunicadoTypes.ts`, `comunicadoChartOptions` (= plugin-ui `SeriesChartOptions`), `comunicadoTableOptions`, `comunicadoKpiOptions`, `*Parts`, `viewProjection.ts`, `comunicadoImageCrop.ts`, serialize path in `comunicadoHelpers.ts`.

### Ownership columns

| Column | Meaning |
|---|---|
| CurrentOwner | Who writes/owns today |
| TargetOwner | Post-001 canonical owner |
| Persisted | `yes` in `native_config` / `no` runtime enrich only |
| Mutation | Primary write path |
| Materializer | Who transforms before paint |
| Renderer | Paint consumer |
| Disposition | `KEEP` / `MIGRATE_BE` / `PAINT_ONLY` / `DEPRECATE` / `RUNTIME_ONLY` |

**Target rule (parity ADR):** structural projection + display format → BE enrich; chrome/layout options → FE presentation + optional BE `blockDefaults`; MFE mutates via draft/`updateSlide` or PresentationMutation ops.

---

## A. Slide / config (`ComunicadoConfig` L833–849)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| slide | `version` | FE serialize | FE+BE | yes | save nativeConfig | parse | stage | KEEP |
| slide | `headline` | FE / legacy | FE | yes | slide fields | — | CustomMessage header (legacy) | DEPRECATE→blocks |
| slide | `subtitle` | FE / legacy | FE | yes | slide fields | — | idem | DEPRECATE→blocks |
| slide | `background.type` | FE | FE | yes | background ribbon | — | `RichComunicadoStage` | KEEP |
| slide | `background.value` (color) | FE | FE | yes | color picker | — | stage CSS | KEEP |
| slide | `background.from`/`to`/`angle`/`stops` (gradient) | FE | FE | yes | gradient UI | — | stage | KEEP |
| slide | `background.assetId`/`url`/`value` (image) | FE+assets | FE+assets | assetId yes; url enrich | media library | enrich URL | stage | KEEP |
| slide | `background.underlay` | FE | FE | yes | underlay UI | — | stage | KEEP |
| slide | `blocks[]` | FE editor | FE+ops | yes | editor / upsert_block | enrich_blocks | block views | KEEP |
| slide | `groupTransforms[groupId].rotation` | FE | FE | yes | group rotate | — | stage transform | KEEP |
| slide | `dataFilters` | FE+kiosk inputs | FE session+persist slide | yes | input blocks / panel | enrich merge | chart/table/kpi filters | KEEP |
| slide | `speakerNotes` | FE | FE | yes | notes UI | — | presenter only | KEEP |
| slide | `brandThemeKey` | FE | FE+ops `ensure_brand_logo` | yes | brand picker | logo inject | master logo | KEEP |
| slide | `customFonts[]` (`assetId`,`familyName`,`url`) | FE+assets | FE+assets | yes (url runtime) | font upload | enrich url | typography | KEEP |

---

## B. Block base (`ComunicadoBlockBase` L261–282)

Applies to **all** block types unless noted.

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| * | `id` | FE `newBlockId` | FE | yes | create* | — | selection | KEEP |
| * | `type` | FE factory | FE+ops | yes | create / upsert_block | — | switch | KEEP |
| * | `frame.x` | FE | FE | yes | drag/resize/align | — | `blockCssStyle` | KEEP |
| * | `frame.y` | FE | FE | yes | drag/resize/align | — | blockCssStyle | KEEP |
| * | `frame.w` | FE | FE | yes | resize | geometry helpers | blockCssStyle | KEEP |
| * | `frame.h` | FE | FE | yes | resize | geometry helpers | blockCssStyle | KEEP |
| * | `groupId` | FE | FE | yes | group/ungroup | — | layers/align | KEEP |
| * | `groupName` | FE | FE | yes | layers rename | — | layers panel | KEEP |
| * | `hidden` | FE | FE | yes | layers eye | — | stage skip | KEEP |
| * | `role` | FE (kpi) | FE+recipes | yes | createKpi / blueprint | partChrome | layout semantics | KEEP |
| * | `variant` | FE | FE | yes | kpi options | — | KPI layout | KEEP |
| * | `animations[].phase` | FE | FE | yes | AnimationSection | — | entrance CSS | KEEP |
| * | `animations[].kind` | FE (`fade`/`slide-in`) | FE | yes | AnimationSection | — | entrance CSS | KEEP |
| * | `animations[].delayMs` | FE | FE | yes | AnimationSection | — | entrance CSS | KEEP |
| * | `animations[].durationMs` | FE | FE | yes | AnimationSection | — | entrance CSS | KEEP |
| * | `animations[].easing` | FE | FE | yes | AnimationSection | — | entrance CSS | KEEP |
| * | `animations[].direction` | FE | FE | yes | AnimationSection | — | entrance CSS | KEEP |

---

## C. `style` (`ComunicadoBlockStyle` L191–243)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| * | `style.fontSize` | FE | FE | yes | typography ribbon | namedStyle materialize | visual box / text | KEEP |
| * | `style.color` | FE | FE | yes | color | auto contrast | text/icon | KEEP |
| * | `style.fontFamily` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.textAlign` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.verticalAlign` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.lineHeight` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.letterSpacing` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.textHighlight` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.fontWeight` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.fontStyle` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.textDecoration` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.objectFit` | FE | FE | yes | media | — | image/video | KEEP |
| * | `style.backgroundColor` | FE | FE | yes | appearance | — | box chrome | KEEP |
| * | `style.borderColor` | FE | FE | yes | appearance | — | box | KEEP |
| * | `style.borderWidth` | FE | FE | yes | appearance | — | box | KEEP |
| * | `style.borderRadius` | FE | FE | yes | appearance | — | box | KEEP |
| * | `style.boxShadow` | FE | FE | yes | appearance | — | box | KEEP |
| * | `style.textShadow` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.textStrokeColor` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.textStrokeWidth` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.textReflection` | FE | FE | yes | typography | — | text | KEEP |
| * | `style.opacity` | FE | FE | yes | organize/appearance | — | block CSS | KEEP |
| * | `style.rotation` | FE | FE | yes | rotate UI | — | transform | KEEP |
| * | `style.scaleX` | FE | FE | yes | flip H | — | transform | KEEP |
| * | `style.scaleY` | FE | FE | yes | flip V | — | transform | KEEP |
| * | `style.zIndex` | FE | FE | yes | layers bring/send | — | stacking | KEEP |
| * | `style.fill` | FE | FE | yes | shape chrome | — | SVG/CSS | KEEP |
| * | `style.stroke` | FE | FE | yes | shape chrome | — | SVG | KEEP |
| * | `style.fillPaint` | FE | FE | yes | paint picker | — | DelpiFill | KEEP |
| * | `style.colorPaint` | FE | FE | yes | paint picker | — | text fill | KEEP |
| * | `style.strokePaint` | FE | FE | yes | paint picker | — | stroke | KEEP |
| * | `style.strokeWidth` | FE | FE | yes | shape chrome | — | SVG | KEEP |
| * | `style.iconStrokeWidth` | FE | FE | yes | icon section | — | Lucide | KEEP |
| * | `style.markerRadius` | FE | FE | yes | point shape | — | marker | KEEP |
| * | `style.adjustments[]` | FE | FE | yes | yellow handles | shape paths | SVG path | KEEP |

---

## D. Text / heading / shape text (`ComunicadoTextBlock` / shape overlap)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| heading/text | `content` | FE | FE | yes | inline edit | — | visual box | KEEP |
| heading/text | `contentRuns[].text` | FE | FE | yes | rich text | displayRuns enrich | visual box | KEEP |
| heading/text | `contentRuns[].style.*` | FE | FE | yes | run format | namedStyle materialize | visual box | KEEP |
| heading/text | `contentRuns[].dataRef.field` | FE | BE display | yes | Campo panel | DisplayFormatService | paint displayRuns | MIGRATE_BE (format) |
| heading/text | `contentRuns[].dataRef.aggregation` | FE | BE | yes | Campo | enrich | displayRuns | MIGRATE_BE |
| heading/text | `contentRuns[].dataRef.format` | FE | BE DisplayFormat | yes | NumberFormat | DisplayFormatService | display* | MIGRATE_BE |
| heading/text | `contentRuns[].dataRef.displayFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | display* | MIGRATE_BE |
| heading/text | `contentRuns[].dataRef.decimalPlaces` | FE | BE | yes | NumberFormat | DisplayFormatService | display* | MIGRATE_BE |
| heading/text | `contentRuns[].dataRef.label` | FE | FE | yes | Campo | — | label | KEEP |
| heading/text | `contentRuns[].dataRef.colorRules` | FE | BE+FE | yes | rules UI | enrich tone | color | KEEP |
| heading/text | `shape` (box geometry kind) | FE | FE | yes | shape gallery | — | visual box path | KEEP |
| heading/text | `href` / `linkTarget` | FE | FE | yes | actions | — | link wrap | KEEP |
| heading/text/shape | `dataSourceId` | FE | FE+ops bind_visual | yes | DataBinding | enrich | text projection | KEEP |
| heading/text/shape | `textProjection.field` | FE | textBindingOwner | yes | Campo | enrich displayText | visual box | KEEP |
| heading/text/shape | `textProjection.aggregation` | FE | BE | yes | Campo | enrich | displayText | MIGRATE_BE |
| heading/text/shape | `textProjection.format` | FE | BE | yes | NumberFormat | DisplayFormatService | displayText | MIGRATE_BE |
| heading/text/shape | `textProjection.displayFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | displayText | MIGRATE_BE |
| heading/text/shape | `textProjection.decimalPlaces` | FE | BE | yes | NumberFormat | DisplayFormatService | displayText | MIGRATE_BE |
| heading/text/shape | `textProjection.prefix`/`suffix`/`fallback` | FE | FE+BE | yes | Campo | enrich compose | displayText | KEEP |
| heading/text/shape | `textProjection.colorRules` | FE | FE+BE | yes | rules | enrich | color | KEEP |
| heading/text/shape | `resolved` / `serverTextProjectionApplied` | BE enrich | BE | **no** | — | enrich | paint | RUNTIME_ONLY |
| shape | `shape` (ComunicadoShapeKind) | FE | FE | yes | insert/gallery | — | SVG | KEEP |
| shape | `vertices[]` `{x,y}` | FE | FE | yes | line edit | geometryToPersistedFrame | SVG | KEEP |
| shape | `connector.fromBlockId`/`toBlockId` | FE | FE | yes | connect | applyConnectorGeometry | line | KEEP |
| shape | `connector.fromAnchor`/`toAnchor` | FE | FE | yes | connect | geometry | line | KEEP |
| shape | `connector.routing` | FE | FE | yes | connect (`straight`/`elbow`/`curve`) | geometry | line | KEEP |
| shape | `efficiencyPin.workCenter` | FE | FE+fonte | yes | pin inspector | enrich pin presentation | radar pin | KEEP |
| shape | `efficiencyPin.matchField` | FE | FE | yes | pin | enrich | pin | KEEP |
| shape | `efficiencyPin.valueField` | FE | FE | yes | pin | enrich | pin | KEEP |
| shape | `efficiencyPin.showLabel` | FE | FE | yes | pin (deprecated) | — | pin | DEPRECATE→infoMode |
| shape | `efficiencyPin.infoMode` | FE | FE | yes | pin | — | pin | KEEP |
| shape | `efficiencyPin.role` | FE | FE | yes | pin/info | — | pin | KEEP |
| shape | `efficiencyPin.linkedBlockId` | FE | FE | yes | pin | — | pin | KEEP |
| shape | `efficiencyPin.bands.goodMinPct` | FE / data_source | data_source | yes | bands UI | mirror from source | pin color | KEEP |
| shape | `efficiencyPin.bands.warnMinPct` | FE / data_source | data_source | yes | bands UI | mirror | pin | KEEP |
| shape | `efficiencyPin.bands.validMaxPct` | FE / data_source | data_source | yes | bands UI | mirror | pin | KEEP |
| shape | `content` / `contentRuns` | FE | FE | yes | text in shape | same as text | visual box | KEEP |
| shape | `href` / `linkTarget` | FE | FE | yes | actions | — | link | KEEP |

---

## E. Media / icon

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| image/video | `assetId` | FE | FE+assets | yes | upload/library | enrich url | media | KEEP |
| image/video | `url` | BE enrich | BE | **no** | — | enrich | `<img>`/`<video>` | RUNTIME_ONLY |
| video | `posterUrl` | BE enrich | BE | **no** | — | enrich | video poster | RUNTIME_ONLY |
| image/video | `href` / `linkTarget` | FE | FE | yes | actions | — | link | KEEP |
| image | `imageCrop.x` | FE | FE | yes | ImageCropSection | crop CSS | img | KEEP |
| image | `imageCrop.y` | FE | FE | yes | ImageCropSection | crop CSS | img | KEEP |
| image | `imageCrop.w` | FE | FE | yes | ImageCropSection | crop CSS | img | KEEP |
| image | `imageCrop.h` | FE | FE | yes | ImageCropSection | crop CSS | img | KEEP |
| icon | `iconName` | FE | FE | yes | IconSection | — | Lucide | KEEP |
| icon | `href` / `linkTarget` | FE | FE | yes | actions | — | link | KEEP |

---

## F. Data source / legacy data blocks

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| data_source | `queryName` | FE | FE | yes | rename | — | M query | KEEP |
| data_source | `dataBinding.operationId` | FE | BE ops | yes | upsert_data_source | catalog | fetch | MIGRATE_BE |
| data_source | `dataBinding.params` | FE | BE | yes | Dados panel | param defaults | fetch | MIGRATE_BE |
| data_source | `dataBinding.displayMode` | FE | FE | yes | upsert | — | chrome | KEEP |
| data_source | `dataBinding.label` | FE | FE+ops | yes | rename | — | chrome | KEEP |
| data_source | `dataBinding.valueField` | legacy | — | yes | — | migrate→projection | — | DEPRECATE |
| data_source | `dataBinding.selectedValueFields` | legacy | — | yes | — | migrate→projection | — | DEPRECATE |
| data_source | `dataBinding.maxRows` | FE | FE | yes | Dados | — | fetch trim | KEEP |
| data_source | `dataBinding.refreshSec` | FE | FE | yes | Dados | — | poll | KEEP |
| data_source | `dataTransform` | FE | BE `set_data_transform` | yes | DataPrepare | M reader BE | enrich | MIGRATE_BE |
| data_source | `fieldLabels` | FE | FE+ops | yes | labels UI | cascade | headers | KEEP |
| data_source | `efficiencyPinBands.*` | FE | FE | yes | map UI | mirror pins | pin | KEEP |
| data_source | `resolved` | BE | BE | **no** | — | enrich | editor chrome | RUNTIME_ONLY |
| data_* | `dataBinding.*` | FE | deprecate | yes | DataBindingInspector | enrich | TvDataBlockView | DEPRECATE |
| data_table | `tablePreset` | FE | — | yes | — | — | TvDataBlockView | DEPRECATE |
| data_table | `tableOptions` / `tableParts` | FE | — | yes | — | — | TvDataBlockView | DEPRECATE |

---

## G. `chart_view` — options / parts / projection

### G1. Identity

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| chart_view | `chartType` | FE | FE | yes | ChartTypeSection | policy | ChartViewBlockView | KEEP |
| chart_view | `dataSourceId` | FE | FE+ops bind_visual | yes | DataBinding | enrich | ChartViewBlockView | KEEP |
| chart_view | `resolved` | BE | BE | **no** | — | enrich + projection | chart widgets | RUNTIME_ONLY |

### G2. `chartProjection` (`viewProjection.ts` L60–72)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| chart_view | `chartProjection.categoryField` | FE | BE TvViewProjection | yes | DataBinding wells | BE bake / applyViewProjection | series points | MIGRATE_BE |
| chart_view | `chartProjection.series[].field` | FE | BE | yes | wells | bake | series | MIGRATE_BE |
| chart_view | `chartProjection.series[].aggregation` | FE | BE | yes | wells | bake | series | MIGRATE_BE |
| chart_view | `chartProjection.series[].label` | FE | FE+BE | yes | wells | bake | legend | KEEP |
| chart_view | `chartProjection.series[].color` | FE | FE | yes | series color | — | series stroke | KEEP |
| chart_view | `chartProjection.series[].plotOn` | FE | FE | yes | axes/series | bake | dual axis | KEEP |
| chart_view | `chartProjection.maxCategories` | FE | BE | yes | wells | bake | categories | MIGRATE_BE |
| chart_view | `chartProjection.goalField` | FE | BE | yes | goal well | projectedGoal | goal line/gauge | MIGRATE_BE |
| chart_view | `chartProjection.goalAggregation` | FE | BE | yes | goal well | bake | goal | MIGRATE_BE |

### G3. `chartOptions` (`SeriesChartOptions` plugin-ui L101–209)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| chart_view | `chartOptions.title` | FE | FE | yes | title edit / parts | parts↔options | ChartTitle | KEEP |
| chart_view | `chartOptions.showTitle` | FE | FE | yes | Add element | — | title | KEEP |
| chart_view | `chartOptions.seriesName` | FE | FE | yes | series | — | legend | KEEP |
| chart_view | `chartOptions.showLegend` | FE | FE | yes | Add element | — | legend | KEEP |
| chart_view | `chartOptions.legendPosition` | FE | FE | yes | ChartLayout | — | legend | KEEP |
| chart_view | `chartOptions.legendLayout` | FE | FE | yes | ChartLayout | — | legend | KEEP |
| chart_view | `chartOptions.legendSort` | FE | FE | yes | ChartLayout | — | legend | KEEP |
| chart_view | `chartOptions.showAxes` | FE | FE | yes | ChartAxes | — | axes | KEEP |
| chart_view | `chartOptions.showXAxisLabels` | FE | FE | yes | ChartAxes | — | axes | KEEP |
| chart_view | `chartOptions.showYAxisLabels` | FE | FE | yes | ChartAxes | — | axes | KEEP |
| chart_view | `chartOptions.showXAxisTitle` | FE | FE | yes | ChartAxes | — | axisTitle | KEEP |
| chart_view | `chartOptions.showYAxisTitle` | FE | FE | yes | ChartAxes | — | axisTitle | KEEP |
| chart_view | `chartOptions.xAxisTitle` | FE | FE | yes | ChartAxes / parts | — | axisTitle | KEEP |
| chart_view | `chartOptions.yAxisTitle` | FE | FE | yes | ChartAxes / parts | — | axisTitle | KEEP |
| chart_view | `chartOptions.showDataLabels` | FE | FE | yes | ChartLabels | — | dataLabel | KEEP |
| chart_view | `chartOptions.dataLabels` | FE | FE | yes | ChartLabels | — | dataLabel | KEEP |
| chart_view | `chartOptions.showDataTable` | FE | FE | yes | Add element | — | dataTable | KEEP |
| chart_view | `chartOptions.showGrid` | FE | FE | yes | ChartAxes | — | grid | KEEP |
| chart_view | `chartOptions.showVerticalGrid` | FE | FE | yes | ChartAxes | — | grid | KEEP |
| chart_view | `chartOptions.showGoalLine` | FE | FE | yes | Add element | — | goalLine | KEEP |
| chart_view | `chartOptions.goalLineValue` | FE | FE+BE goalField | yes | goal inspector | effectiveGoal enrich | goalLine | KEEP |
| chart_view | `chartOptions.showGaugeLabel` | FE | FE | yes | gauge parts | — | gaugeLabel | KEEP |
| chart_view | `chartOptions.showMarkers` | FE | FE | yes | ChartSeries | — | markers | KEEP |
| chart_view | `chartOptions.markerMode` | FE | FE | yes | ChartSeries | — | markers | KEEP |
| chart_view | `chartOptions.areaFillGradient` | FE | FE | yes | styles | — | area | KEEP |
| chart_view | `chartOptions.smoothLines` | FE | FE | yes | styles | — | line/area | KEEP |
| chart_view | `chartOptions.valueFormat` | FE | BE DisplayFormat | yes | NumberFormat | DisplayFormatService | ticks/labels | MIGRATE_BE |
| chart_view | `chartOptions.displayValueFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | ticks/labels | MIGRATE_BE |
| chart_view | `chartOptions.displayCategoryFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | axis X | MIGRATE_BE |
| chart_view | `chartOptions.decimalPlaces` | FE | BE | yes | NumberFormat | DisplayFormatService | ticks | MIGRATE_BE |
| chart_view | `chartOptions.yAxisTicks` | BE enrich | BE | sometimes mirrored | — | G24 enrich | axis | PAINT_ONLY / RUNTIME_ONLY preferred |
| chart_view | `chartOptions.categoryLabelRotation` | FE | FE | yes | ChartAxes | — | axis X | KEEP |
| chart_view | `chartOptions.categoryLabelOverflow` | FE | FE | yes | ChartAxes | — | axis X | KEEP |
| chart_view | `chartOptions.categoryLabelFormat` | FE | BE displayCategory | yes | NumberFormat | DisplayFormatService | axis X | MIGRATE_BE |
| chart_view | `chartOptions.seriesColor` | FE | FE | yes | colors menu | — | series:0 | KEEP |
| chart_view | `chartOptions.categoryColors` | FE | FE | yes | colors menu | — | pie/bars | KEEP |
| chart_view | `chartOptions.colorScale` | FE | FE | yes | colors | — | marks | KEEP |
| chart_view | `chartOptions.theme` | FE | FE | yes | styles | — | chrome | KEEP |
| chart_view | `chartOptions.backgroundColor` | FE | FE | yes | styles | — | chartArea | KEEP |
| chart_view | `chartOptions.categoryPaddingPercent` | FE | FE | yes | layout | — | plot | KEEP |
| chart_view | `chartOptions.chromeVersion` | FE migrate | FE | yes | load migrate | migrateSeriesChartOptionsOnLoad | — | KEEP |

### G4. `chartParts` map keys / state (`ChartPartRef` + `ChartPartState`)

Part kinds (keys via `serializeChartPartRef`):  
`chartArea`, `plotArea`, `title`, `legend`, `series:{i}`, `marker:{i}:{j}`, `dataLabel:{i}:{j}`, `dataLabels`, `axes`, `axis:x|y`, `axisTitle:x|y`, `grid`, `goalLine`, `dataTable`, `gaugeTrack`, `gaugeFill`, `gaugeZone:{z}`, `gaugeNeedle`, `gaugeValue`, `gaugeLabel`, `gaugeGoalMarker`.

Per part state properties:

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| chart_view | `chartParts[key].visible` | FE | FE | yes | Add element / Del | parts↔options | part chrome | KEEP |
| chart_view | `chartParts[key].content` | FE | FE | yes | inline edit | — | title/axisTitle | KEEP |
| chart_view | `chartParts[key].contentRuns` | FE | FE | yes | rich text | — | title | KEEP |
| chart_view | `chartParts[key].frame.{x,y,w,h}` | FE | FE | yes | part drag/resize | normalize on load | layout | KEEP |
| chart_view | `chartParts[key].style.fill` | FE | FE | yes | PartFormat | — | SVG/CSS | KEEP |
| chart_view | `chartParts[key].style.stroke` | FE | FE | yes | PartFormat | — | SVG | KEEP |
| chart_view | `chartParts[key].style.strokeWidth` | FE | FE | yes | PartFormat | — | SVG | KEEP |
| chart_view | `chartParts[key].style.opacity` | FE | FE | yes | PartFormat | — | SVG | KEEP |
| chart_view | `chartParts[key].style.fontFamily` | FE | FE | yes | typography | — | text parts | KEEP |
| chart_view | `chartParts[key].style.fontSize` | FE | FE | yes | typography | — | text parts | KEEP |
| chart_view | `chartParts[key].style.color` | FE | FE | yes | typography | — | text parts | KEEP |
| chart_view | `chartParts[key].style.fontWeight` | FE | FE | yes | typography | — | text | KEEP |
| chart_view | `chartParts[key].style.fontStyle` | FE | FE | yes | typography | — | text | KEEP |
| chart_view | `chartParts[key].style.textAlign` | FE | FE | yes | typography | — | text | KEEP |
| chart_view | `chartParts[key].style.verticalAlign` | FE | FE | yes | typography | — | text | KEEP |
| chart_view | `chartParts[key].style.markerRadius` | FE | FE | yes | series | — | markers | KEEP |
| chart_view | `chartParts[key].style.strokeDasharray` | FE | FE | yes | series | — | line | KEEP |
| chart_view | `chartParts[key].style.borderRadius` | FE | FE | yes | PartFormat | — | chartArea | KEEP |
| chart_view | `chartParts[key].style.boxShadow` | FE | FE | yes | PartFormat | — | chartArea | KEEP |
| chart_view | `chartParts[key].style.textShadow` | FE | FE | yes | typography | — | title | KEEP |
| chart_view | `chartParts[key].style.textStrokeColor` | FE | FE | yes | typography | — | title | KEEP |
| chart_view | `chartParts[key].style.textStrokeWidth` | FE | FE | yes | typography | — | title | KEEP |
| chart_view | `chartParts[key].style.textReflection` | FE | FE | yes | typography | — | title | KEEP |

---

## H. `table_view` — options / parts / projection

### H1. Identity + projection

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| table_view | `tablePreset` | FE | FE | yes | TableStyles | presetDefaultTableOptions | ConfigurableTable | KEEP |
| table_view | `dataSourceId` | FE | FE+ops | yes | DataBinding | enrich | TableViewBlockView | KEEP |
| table_view | `maxRows` / `maxCols` | FE | FE | yes | TableLayoutData | trim display | table | KEEP |
| table_view | `tableProjection.columns[].key` | FE | BE | yes | DataBinding columns | bake | columns | MIGRATE_BE |
| table_view | `tableProjection.columns[].label` | FE | FE+BE | yes | columns | bake | header | KEEP |
| table_view | `tableProjection.columns[].visible` | FE | BE | yes | columns | bake | columns | MIGRATE_BE |
| table_view | `tableProjection.columns[].widthPct` | FE | FE | yes | column resize / distribute | — | col widths | KEEP |
| table_view | `tableProjection.columns[].displayFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | displayRows | MIGRATE_BE |
| table_view | `tableProjection.columns[].valueFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | displayRows | MIGRATE_BE |
| table_view | `resolved` | BE | BE | **no** | — | enrich | table | RUNTIME_ONLY |

### H2. `tableOptions` (`ConfigurableTableOptions` L30–70)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| table_view | `tableOptions.title` | FE | FE | yes | title | parts↔options | table title | KEEP |
| table_view | `tableOptions.showTitle` | FE | FE | yes | TableStyleOptions | — | title | KEEP |
| table_view | `tableOptions.showHeader` | FE | FE | yes | TableStyleOptions | — | header | KEEP |
| table_view | `tableOptions.showTotalRow` | FE | FE | yes | TableStyleOptions | — | footer | KEEP |
| table_view | `tableOptions.emphasizeFirstColumn` | FE | FE | yes | TableStyleOptions | — | cells | KEEP |
| table_view | `tableOptions.emphasizeLastColumn` | FE | FE | yes | TableStyleOptions | — | cells | KEEP |
| table_view | `tableOptions.bandedColumns` | FE | FE | yes | TableStyleOptions | — | cells | KEEP |
| table_view | `tableOptions.headerBg` | FE | FE | yes | TableStyles/PartFormat | — | header | KEEP |
| table_view | `tableOptions.headerTextColor` | FE | FE | yes | TableTypography | — | header | KEEP |
| table_view | `tableOptions.cellBg` | FE | FE | yes | styles | — | cells | KEEP |
| table_view | `tableOptions.cellTextColor` | FE | FE | yes | typography | — | cells | KEEP |
| table_view | `tableOptions.borderColor` | FE | FE | yes | TableBorders | — | grid | KEEP |
| table_view | `tableOptions.borderWidth` | FE | FE | yes | TableBorders | — | grid | KEEP |
| table_view | `tableOptions.borderStyle` | FE | FE | yes | TableBorders | — | grid | KEEP |
| table_view | `tableOptions.fontSize` | FE | FE | yes | TableTypography | — | cells | KEEP |
| table_view | `tableOptions.fontFamily` | FE | FE | yes | TableTypography | — | cells | KEEP |
| table_view | `tableOptions.fontWeight` | FE | FE | yes | TableTypography | — | cells | KEEP |
| table_view | `tableOptions.fontStyle` | FE | FE | yes | TableTypography | — | cells | KEEP |
| table_view | `tableOptions.textAlign` | FE | FE | yes | TableLayoutAlign | — | cells | KEEP |
| table_view | `tableOptions.zebraStripe` | FE | FE | yes | TableStyleOptions | — | rows | KEEP |
| table_view | `tableOptions.showBorders` | FE | FE | yes | TableBorders | — | grid | KEEP |
| table_view | `tableOptions.valueFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | displayRows | MIGRATE_BE |
| table_view | `tableOptions.displayValueFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | displayRows | MIGRATE_BE |
| table_view | `tableOptions.headerUppercase` | FE | FE | yes | TableTypography | — | header | KEEP |
| table_view | `tableOptions.wrapText` | FE | FE | yes | TableLayout | — | cells | KEEP |
| table_view | `tableOptions.rowHeightPx` | FE | FE | yes | TableLayoutSize | — | rows | KEEP |

### H3. `tableParts` (`TablePartRef` kinds: frame/title/header/headerCell/row/cell)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| table_view | `tableParts[key].visible` | FE | FE | yes | delete part / options | parts↔options | ConfigurableTable | KEEP |
| table_view | `tableParts[key].content` | FE | FE | yes | inline header | — | headerCell | KEEP |
| table_view | `tableParts[key].style.fill` | FE | FE | yes | PartFormat | — | cell bg | KEEP |
| table_view | `tableParts[key].style.color` | FE | FE | yes | typography | — | text | KEEP |
| table_view | `tableParts[key].style.fontWeight` | FE | FE | yes | typography | — | text | KEEP |
| table_view | `tableParts[key].style.fontFamily` | FE | FE | yes | typography | — | text | KEEP |
| table_view | `tableParts[key].style.fontSize` | FE | FE | yes | typography | — | text | KEEP |
| table_view | `tableParts[key].style.fontStyle` | FE | FE | yes | typography | — | text | KEEP |
| table_view | `tableParts[key].style.textDecoration` | FE | FE | yes | typography | — | text | KEEP |
| table_view | `tableParts[key].style.textAlign` | FE | FE | yes | align | — | text | KEEP |
| table_view | `tableParts[key].style.verticalAlign` | FE | FE | yes | align | — | text | KEEP |
| table_view | `tableParts[key].style.stroke` | FE | FE | yes | PartFormat frame | — | frame | KEEP |
| table_view | `tableParts[key].style.strokeWidth` | FE | FE | yes | PartFormat | — | frame | KEEP |
| table_view | `tableParts[key].style.borderRadius` | FE | FE | yes | PartFormat | — | frame | KEEP |
| table_view | `tableParts[key].style.boxShadow` | FE | FE | yes | PartFormat | — | frame | KEEP |

---

## I. `kpi_view` — options / parts / projection

### I1. Projection (`KpiMetricProjection` L31–45)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| kpi_view | `dataSourceId` | FE | FE+ops | yes | DataBinding | enrich | KpiViewBlockView | KEEP |
| kpi_view | `kpiProjection.metrics[].field` | FE | BE | yes | wells | bake | metrics | MIGRATE_BE |
| kpi_view | `kpiProjection.metrics[].aggregation` | FE | BE | yes | wells | bake | metrics | MIGRATE_BE |
| kpi_view | `kpiProjection.metrics[].label` | FE | FE+BE | yes | wells | bake | title | KEEP |
| kpi_view | `kpiProjection.metrics[].format` | FE | BE | yes | NumberFormat | DisplayFormatService | displayValue | MIGRATE_BE |
| kpi_view | `kpiProjection.metrics[].displayFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | displayValue | MIGRATE_BE |
| kpi_view | `kpiProjection.metrics[].decimalPlaces` | FE | BE | yes | NumberFormat | DisplayFormatService | displayValue | MIGRATE_BE |
| kpi_view | `kpiProjection.metrics[].colorRules` | FE | FE+BE | yes | rules | enrich | value color | KEEP |
| kpi_view | `kpiProjection.metrics[].visible` | FE | BE | yes | wells | bake | metrics | MIGRATE_BE |
| kpi_view | `kpiProjection.metrics[].target` | FE | FE+BE | yes | KPI appearance | kpiPresentation | comparison | KEEP |
| kpi_view | `kpiProjection.metrics[].comparisonMode` | FE | FE+BE | yes | KPI appearance | kpiPresentation | comparison | KEEP |
| kpi_view | `kpiProjection.metrics[].higherIsBetter` | FE | FE | yes | KPI appearance | kpiPresentation | tone | KEEP |
| kpi_view | `resolved` | BE | BE | **no** | — | enrich | KPI card | RUNTIME_ONLY |

### I2. `kpiOptions` (`comunicadoKpiOptions.ts` L13–50)

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| kpi_view | `kpiOptions.title` | FE | FE | yes | title / parts | parts↔options | card | KEEP |
| kpi_view | `kpiOptions.subtitle` | FE | FE | yes | appearance | — | hint | KEEP |
| kpi_view | `kpiOptions.unit` | FE | FE | yes | appearance | — | value | KEEP |
| kpi_view | `kpiOptions.iconName` | FE | FE | yes | appearance | — | icon | KEEP |
| kpi_view | `kpiOptions.showIcon` | FE | FE | yes | appearance | — | icon | KEEP |
| kpi_view | `kpiOptions.showTitle` | FE | FE | yes | appearance | — | title | KEEP |
| kpi_view | `kpiOptions.tone` | FE | FE | yes | appearance | — | card | KEEP |
| kpi_view | `kpiOptions.valueColor` | FE | FE | yes | appearance | — | value | KEEP |
| kpi_view | `kpiOptions.backgroundColor` | FE | FE | yes | appearance | — | card | KEEP |
| kpi_view | `kpiOptions.valueFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | value | MIGRATE_BE |
| kpi_view | `kpiOptions.displayValueFormat` | FE | BE | yes | NumberFormat | DisplayFormatService | value | MIGRATE_BE |
| kpi_view | `kpiOptions.decimalPlaces` | FE | BE | yes | NumberFormat | DisplayFormatService | value | MIGRATE_BE |
| kpi_view | `kpiOptions.colorRules` | FE | FE+BE | yes | rules | enrich | value | KEEP |
| kpi_view | `kpiOptions.target` | FE | FE+BE | yes | appearance | kpiPresentation | progress | KEEP |
| kpi_view | `kpiOptions.comparisonMode` | FE | FE+BE | yes | appearance | kpiPresentation | comparison | KEEP |
| kpi_view | `kpiOptions.higherIsBetter` | FE | FE | yes | appearance | kpiPresentation | tone | KEEP |
| kpi_view | `kpiOptions.showComparison` | FE | FE | yes | appearance | — | comparison part | KEEP |
| kpi_view | `kpiOptions.showProgress` | FE | FE | yes | appearance | — | progress | KEEP |
| kpi_view | `kpiOptions.showSparkline` | FE | FE | yes | appearance | — | sparkline | KEEP |
| kpi_view | `kpiOptions.comparisonLabel` | FE | FE | yes | appearance | — | comparison | KEEP |
| kpi_view | `kpiOptions.contextMode` | FE | FE | yes | create default auto | enrich context | spark/progress | KEEP |
| kpi_view | `kpiOptions.variant` | FE | FE | yes | create/appearance | — | hero/row/scorecard | KEEP |

### I3. `kpiParts` kinds: `card`,`title`,`value`,`hint`,`icon`,`comparison`,`progress`,`sparkline`,`metricCard:{field}`

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| kpi_view | `kpiParts[key].visible` | FE | FE | yes | Add element | parts↔options | DelpiKpiCard | KEEP |
| kpi_view | `kpiParts[key].content` | FE | FE | yes | inline | — | title | KEEP |
| kpi_view | `kpiParts[key].frame.*` | FE | FE | yes | part drag | normalize | layout | KEEP |
| kpi_view | `kpiParts[key].style.*` | FE | FE | yes | PartFormat/typography | — | part paint | KEEP |

(style fields mirror chart part style subset used by KPI card — fill/backgroundColor/fontSize/color/fontWeight/iconSize etc. as stored in BE defaults L628–653.)

---

## J. `canvas_table`

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| canvas_table | `rows` / `cols` | FE | FE | yes | CanvasTableSection | normalize cells | grid | KEEP |
| canvas_table | `cells[][].kind` | FE | FE | yes | cell UI | — | cell | KEEP |
| canvas_table | `cells[][].text` | FE | FE | yes | edit | — | text | KEEP |
| canvas_table | `cells[][].value` | FE | FE | yes | number | — | number | KEEP |
| canvas_table | `cells[][].format` | FE | FE+BE display | yes | NumberFormat | DisplayFormat when bound | number | KEEP |
| canvas_table | `cells[][].series` | FE | FE | yes | sparkline | — | spark | KEEP |
| canvas_table | `cells[][].style.*` | FE | FE | yes | typography | — | cell | KEEP |
| canvas_table | `cells[][].contentRuns` | FE | FE | yes | rich | — | cell | KEEP |
| canvas_table | `cells[][].dataRef.*` | FE | BE display | yes | Campo | enrich | display | MIGRATE_BE |
| canvas_table | `cells[][].dataSourceId` | FE | FE | yes | binding | enrich map | cell | KEEP |
| canvas_table | `merges[]` `{row,col,rowspan,colspan}` | FE | FE | yes | merge UI | — | grid | KEEP |
| canvas_table | `headerRow` | FE | FE | yes | CanvasTableSection | — | header | KEEP |
| canvas_table | `canvasTableOptions.fontSize` | FE | FE | yes | section | — | grid | KEEP |
| canvas_table | `canvasTableOptions.bandedRows` | FE | FE | yes | section | — | grid | KEEP |
| canvas_table | `canvasTableOptions.bandedColumns` | FE | FE | yes | section | — | grid | KEEP |
| canvas_table | `canvasTableOptions.headerStyle` | FE | FE | yes | section | — | header | KEEP |
| canvas_table | `canvasTableOptions.borderStyle` | FE | FE | yes | section | — | borders | KEEP |
| canvas_table | `canvasTableOptions.columnWidths` | FE | FE | yes | resize | — | cols | KEEP |
| canvas_table | `canvasTableOptions.rowHeights` | FE | FE | yes | resize | — | rows | KEEP |
| canvas_table | `dataSourceId` | FE | FE | yes | binding | enrich | cells | KEEP |
| canvas_table | `resolved` / `resolvedBySourceId` / `serverCanvasTableProjectionApplied` | BE | BE | **no** | — | enrich | paint | RUNTIME_ONLY |

---

## K. `input`

| Component | Property | CurrentOwner | TargetOwner | Persisted | Mutation | Materializer | Renderer | Disposition |
|---|---|---|---|---|---|---|---|---|
| input | `input.paramKey` | FE | FE | yes | InputBindingSection | schema resolve | control | KEEP |
| input | `input.label` | FE | FE | yes | InputBinding | — | label | KEEP |
| input | `input.iconName` | FE | FE | yes | InputBinding | — | icon | KEEP |
| input | `input.defaultValue` | FE | FE | yes | InputBinding | — | control | KEEP |
| input | `input.targetScope` | FE | FE | yes | InputBinding | — | filter apply | KEEP |
| input | `input.targetSourceIds` | FE | FE | yes | InputBinding | — | filter apply | KEEP |
| input | `input.resolvedField` / `paramAvailable` | BE enrich | BE | **no** | — | enrich | control kind | RUNTIME_ONLY |
| input | `inputParts` kinds `frame|icon|label|badge|control` + state/style/frame | FE | FE | yes | PartFormat | materialize frames | ComunicadoInputBlockView | KEEP |

---

## L. zIndex / rotation / animations / groupTransforms (cross-cut)

Already listed in B/C/A; summary disposition:

| Property path | Persisted | Disposition |
|---|---|---|
| `style.zIndex` | yes | KEEP (layers) |
| `style.rotation` / `scaleX` / `scaleY` | yes | KEEP (organize) |
| `animations[]` | yes | KEEP (entrance; TV gated by stage class) |
| `groupTransforms[id].rotation` | yes | KEEP |

---

## Counts (E2)

| Bucket | Persisted property rows (approx.) |
|---|---:|
| Slide/config | 14 |
| Block base + style | 50+ |
| Text/shape/media/icon | 45+ |
| Data source/legacy | 20+ |
| chart options+projection+parts fields | 70+ |
| table options+projection+parts fields | 45+ |
| kpi options+projection+parts fields | 40+ |
| canvas_table | 25+ |
| input | 12+ |
| **Total matrix rows** | **~320+** (parts style fields counted once per map pattern; part keys enumerated in G4/H3/I3) |

All entries: **CONFIRMADO_NO_CODIGO**.
