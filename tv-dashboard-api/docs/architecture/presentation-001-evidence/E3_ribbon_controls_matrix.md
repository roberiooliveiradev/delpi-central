# E3 — Ribbon / selection controls matrix (TV-DASHBOARD-PRESENTATION-001)

**Evidence class:** `CONFIRMADO_NO_CODIGO`  
**Epic:** TV-DASHBOARD-PRESENTATION-001  
**Inventory date:** 2026-09-24  
**Scope:** ribbon + painel Elemento sob `plugins/tv-dashboard/src/components/selectionSections/`, format ribbon (`formatRibbon/`), ChartAxes (ribbon + Data axes editor), DataBinding, layers, align/distribute, chart quick layout, Insert create, Actions duplicate.

### Ownership columns

| Column | Meaning |
|---|---|
| Control | User-facing gesture / UI control |
| Types | Block types (or `*`) where the control appears |
| Current path | FE call chain measured in code |
| Target mutation | PRESENTATION-001 canonical op |
| Response field | Primary ack field(s) after commit / enrich |
| Paint consumer | Who renders the mutated state |
| Status | Wiring vs target (see legend) |

### Status legend (PRESENTATION-001 target)

| Status | Meaning |
|---|---|
| `WIRED_align_blocks` | FE already calls `commitAlignBlocks` → op `align_blocks` |
| `WIRED_reorder_block_z` | FE already calls `commitReorderBlockZ` → op `reorder_block_z` |
| `WIRED_create_block` | FE already calls `commitCreateBlock` → op `create_block` (+ optional place `upsert_block`) |
| `TARGET_upsert_block` | Style/frame/options: today `updateSelected`/`updateBlocks` → draft/`updateSlide`; target `upsert_block` deep-merge |
| `TARGET_duplicate_blocks` | BE op exists; FE still clones locally — **GAP** |
| `TARGET_upsert_plus_enrich` | Persist format via upsert; paint strings via BE `DisplayFormatService` (`display*` / `serverDisplayApplied`) |
| `UI_SESSION_ONLY` | Editor preference (snap/grid/panel) — not a block mutation |
| `NAV_ONLY` | Opens panel / scrolls — no nativeConfig write |
| `NOOP_DEPRECATED` | Stub / deprecated host |

### Mutation bridge (CONFIRMADO_NO_CODIGO)

| Bridge | Path |
|---|---|
| Client | `plugins/tv-dashboard/src/utils/presentationMutationClient.ts` — `commitCreateBlock`, `commitAlignBlocks`, `commitReorderBlockZ`, `commitUpsertBlocks` |
| HTTP | `POST …/slides/{slide_id}/presentation-mutations` — `tv-dashboard-api/tv_app/interface/http/routes/slide_routes.py` L289–348 |
| Ops registry | `presentation_mutation/patch_service.py` — `create_block`, `align_blocks`, `reorder_block_z`, `duplicate_blocks`, `upsert_block` |
| Response envelope | `nativeConfig`, `slide`, `appliedOps`, `fingerprint`, `persisted` |
| Local draft path | `useComunicadoEditorBlocks.updateSelected` → `updateBlocks` → `commitWithHistory` → autosave `updateSlide(nativeConfig)` |
| Display enrich | `DisplayFormatService` → `serverDisplayApplied` + `display*` on resolved (paint-only) |

### Host wiring (CONFIRMADO_NO_CODIGO)

| Surface | Path |
|---|---|
| Section resolver | `selectionSections/resolveSelectionSections.ts` + `commonSectionPresets.ts` (`COMMON_RIBBON_TAIL` = display → organize → actions) |
| Section host | `selectionSections/SelectionSectionsHost.tsx` |
| Organize UI | `formatRibbon/FormatRibbonOrganizeGroup.tsx` via `OrganizeSection.tsx` |
| Actions UI | `formatRibbon/FormatRibbonOrganizeSection.tsx` (`FormatRibbonElementActions`) via `ActionsSection.tsx` |
| Insert create | `ComunicadoInsertRibbon.tsx` → `addBlock` / `addShape` / `addChartViewBlock` / … |
| Layers panel | `deck/ComunicadoLayersPanel.tsx` (ribbon tile «Painel» → `openLayersPanel`) |
| Layers ribbon | `ComunicadoLayersRibbon.tsx` — **returns null** (deprecated) |
| Data ribbon | `ComunicadoDataRibbon.tsx` + `DataBindingInspector.tsx` / `VisualDataViewInspector.tsx` |
| Chart axes (data) | `ChartAxesProjectionEditor.tsx` (Dados / Select Data) — distinct from ribbon `ChartAxesSection` |

---

## Totals

| Metric | Value |
|---|---:|
| **CONTROL_ROWS** | **78** |
| Selection section ids (`types.ts`) | 34 |
| Chart quick layouts | 5 (`chartQuickLayouts.ts`) |
| Align/distribute commands (organize menu) | 14 geometry + 3 session toggles |
| Z-order commands | 4 |
| BE mutation ops in scope | 5 (`create` / `align` / `reorder_z` / `duplicate` / `upsert`) |

---

## A. Create (Insert ribbon)

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Insert text / heading | `text`, `heading` | `ComunicadoInsertRibbon` → `addBlock` → `commitCreateBlock` (+ place `commitUpsertBlocks`) / local `createBlock` fallback — `useComunicadoEditorBlocks.ts` L289–344 | `create_block` | `nativeConfig` | `RichComunicadoStage` / visual box views | `WIRED_create_block` |
| Insert shape (gallery / line tool) | `shape` | `addShape` / draw tool → insert path (same hook) | `create_block` | `nativeConfig` | shape paint (`ComunicadoShape*`) | `WIRED_create_block` / `TARGET_upsert_block` for draw finalize |
| Insert icon | `icon` | `addIconBlock` | `create_block` | `nativeConfig` | icon view | `WIRED_create_block` (when wired via create) / else local insert |
| Insert chart | `chart_view` | `addChartViewBlock` / catalog | `create_block` | `nativeConfig` | `ChartViewBlockView` | `WIRED_create_block` / local |
| Insert table_view | `table_view` | `addTableViewBlock` | `create_block` | `nativeConfig` | `TableViewBlockView` | `WIRED_create_block` / local |
| Insert canvas_table | `canvas_table` | `addCanvasTableBlock` | `create_block` | `nativeConfig` | canvas table view | `WIRED_create_block` / local |
| Insert kpi_view | `kpi_view` | `addKpiViewBlock` | `create_block` | `nativeConfig` | KPI card views | `WIRED_create_block` / local |
| Insert input | `input` | `addInputBlock` | `create_block` | `nativeConfig` | input view | `WIRED_create_block` / local |
| Insert media (library/upload) | `image`, `video` | `openMediaLibrary` / `triggerUpload` → media hook `createBlock` | `create_block` then `upsert_block` (asset fields) | `nativeConfig` | media views | `TARGET_upsert_block` (+ create) |
| Insert data / open catalog | data-bound types | `openDataCatalog` → data block insert `addDataBlock` (local) | `create_block` | `nativeConfig` | chart/table/kpi/data views | `TARGET_upsert_block` / create — **catalog insert still local** `CONFIRMADO_NO_CODIGO` |
| Connect two shapes | `shape` connector | `connectSelected` → `createConnectorBlock` + `commitAndSelectInserted` (local) | `create_block` | `nativeConfig` | connector paint | `TARGET_upsert_block` / create — **GAP local** |

---

## B. Geometry — align / distribute / same-size

Source: `FormatRibbonOrganizeGroup.tsx` L145–160 + `alignSelected` / `sameSizeSelected` in `useComunicadoEditorBlocks.ts` L1375–1409. Commands: `comunicadoLayoutAlign.ts`.

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Align left/center-h/right (selection) | `*` multi ≥2 | `alignSelected` → `commitAlignBlocks` / local `alignComunicadoBlocks` | `align_blocks` | `nativeConfig` | `blockCssStyle` / stage frames | `WIRED_align_blocks` |
| Align top/center-v/bottom (selection) | `*` multi ≥2 | idem | `align_blocks` | `nativeConfig` | stage frames | `WIRED_align_blocks` |
| Distribute H / V | `*` multi ≥3 | idem (`distribute-h` / `distribute-v`) | `align_blocks` | `nativeConfig` | stage frames | `WIRED_align_blocks` |
| Align to slide (6 cmds) | `*` | idem (`align-slide-*`) | `align_blocks` | `nativeConfig` | stage frames | `WIRED_align_blocks` |
| Same size both/width/height | `*` multi | `sameSizeSelected` → **local only** `resizeComunicadoBlocksSameSize` | `align_blocks` or `upsert_block` (frame.w/h) | `nativeConfig` | stage frames | `TARGET_upsert_block` — **GAP** (no BE commit yet) |
| Deprecated `FormatRibbonAlignSection` | `*` | legacy tiles → same `alignSelected` | `align_blocks` | `nativeConfig` | stage | `WIRED_align_blocks` (deprecated UI) |
| `AlignMultiSection` | — | returns `null` (`OrganizeSection.tsx` L33–35) | — | — | — | `NOOP_DEPRECATED` |

---

## C. Layers / z-order

Source: `FormatRibbonOrganizeGroup.tsx` L115–143; `applyLayerOrder` → `commitReorderBlockZ` (`useComunicadoEditorBlocks.ts` L1225–1274); panel `ComunicadoLayersPanel.tsx`.

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Bring forward | `*` | `bringForward` → `commitReorderBlockZ` command `bring-forward` | `reorder_block_z` | `nativeConfig` | `style.zIndex` stacking | `WIRED_reorder_block_z` |
| Bring to front | `*` | `bringToFront` → `bring-to-front` | `reorder_block_z` | `nativeConfig` | stacking | `WIRED_reorder_block_z` |
| Send backward | `*` | `sendBackward` → `send-backward` | `reorder_block_z` | `nativeConfig` | stacking | `WIRED_reorder_block_z` |
| Send to back | `*` | `sendToBack` → `send-to-back` | `reorder_block_z` | `nativeConfig` | stacking | `WIRED_reorder_block_z` |
| Layers panel: chevron up/down | `*` | same `bringForward` / `sendBackward` | `reorder_block_z` | `nativeConfig` | stacking | `WIRED_reorder_block_z` |
| Layers panel: drag reorder | `*` | `reorderBlockLayer` → `reorderLayerIds` + `updateBlocks` **local** | `reorder_block_z` | `nativeConfig` | stacking | `TARGET` via `reorder_block_z` — **GAP** (drag not committed) |
| Layers: hide / show eye | `*` | `updateSelected` / batch `hidden` | `upsert_block` | `nativeConfig` | stage skip hidden | `TARGET_upsert_block` |
| Layers: show all / hide all | `*` | panel toolbar | `upsert_block` (batch) | `nativeConfig` | stage | `TARGET_upsert_block` |
| Layers: rename group | `*` grouped | `groupName` patch | `upsert_block` | `nativeConfig` | layers UI | `TARGET_upsert_block` |
| Layers: entrance build map | `*` | animation delay helpers | `upsert_block` (`animations[]`) | `nativeConfig` | entrance CSS | `TARGET_upsert_block` |
| Open layers panel tile | `*` | `openLayersPanel()` | — | — | — | `NAV_ONLY` |
| `ComunicadoLayersRibbon` | — | returns `null` | — | — | — | `NOOP_DEPRECATED` |

---

## D. Organize — group / rotate / flip / session

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Group / ungroup / regroup | `*` | `groupSelected` / `ungroupSelected` / `regroupSelected` → local `groupId` | `upsert_block` (group fields) | `nativeConfig` | `GroupTransformLayer` / layers | `TARGET_upsert_block` |
| Rotate ±90° / flip H/V | `*` | `rotateSelected` / `flipSelected*` → `style.rotation` / `scaleX`/`scaleY` | `upsert_block` | `nativeConfig` | transform CSS | `TARGET_upsert_block` |
| Focus rotation field | `*` | `focusFrameRotationField` | — | — | frame UI | `NAV_ONLY` |
| Snap to grid / objects / show grid | session | `setSnapToGrid` / `setSnapToObjects` / `setShowStageGrid` | — | — | editor guides only | `UI_SESSION_ONLY` |

---

## E. Frame / display / appearance (common tail)

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Size & position (x/y/w/h/rotation) | `*` (part-aware) | `DisplaySection` → `FormatRibbonFrameSection` → frame patches / `updateSelected` | `upsert_block` | `nativeConfig` | `blockCssStyle` / part frames | `TARGET_upsert_block` |
| `FrameSizeSection` | `*` | delegates to `DisplaySection` | `upsert_block` | `nativeConfig` | same | `TARGET_upsert_block` (alias) |
| Opacity / objectFit (Exibição) | `*` / media | `AppearanceSection` → `FormatRibbonOpacityFields` → `updateSelectedStyle` | `upsert_block` | `nativeConfig` | block CSS | `TARGET_upsert_block` |
| Part frame (chart/kpi/input) | parts | frame section clamps via presentation helpers | `upsert_block` | `nativeConfig` | part overlays | `TARGET_upsert_block` |

---

## F. Style — typography / chrome / shape / media

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Font / weight / align / effects | `text`, `heading`, `shape`, chart/kpi/table parts, `canvas_table`, `input` | `TypographySection` → `FormatRibbonTypographySections` → `updateSelectedStyle` / `updateSelectedTextFormatStyle` | `upsert_block` | `nativeConfig` | visual box / text paint | `TARGET_upsert_block` |
| Visual box Forma chrome (fill/outline) | `text`, `heading`, `shape` | `VisualBoxElementSections` → `VisualBoxFormaChrome` | `upsert_block` | `nativeConfig` | shape chrome | `TARGET_upsert_block` |
| Shape gallery change | `shape` | `ShapeGallerySection` → `updateSelected({ shape })` | `upsert_block` | `nativeConfig` | shape path | `TARGET_upsert_block` |
| ShapeChrome (fill/line) | `shape`, `input`, kpi parts | `ShapeChromeSection` | `upsert_block` | `nativeConfig` | chrome | `TARGET_upsert_block` |
| Icon picker / color | `icon` | `IconSection` → `updateSelected` / style | `upsert_block` | `nativeConfig` | icon view | `TARGET_upsert_block` |
| Text box margins | text-like | `TextBoxSection` | `upsert_block` | `nativeConfig` | text box | `TARGET_upsert_block` |
| Media library / upload | `image`, `video` | `MediaSection` | `upsert_block` (url/assetId) | `nativeConfig` | media views | `TARGET_upsert_block` |
| Image crop | `image` | `ImageCropSection` | `upsert_block` (crop) | `nativeConfig` | image paint | `TARGET_upsert_block` |
| Part format chrome | chart/table part | `PartFormatSection` → `ChartRibbonShapeChrome` / `TableRibbonShapeChrome` | `upsert_block` | `nativeConfig` | part chrome | `TARGET_upsert_block` |
| Animation entrance | `*` pane | `AnimationSection` → `updateSelected({ animations })` (ribbon returns null) | `upsert_block` | `nativeConfig` | entrance CSS | `TARGET_upsert_block` |

---

## G. Display format (Número)

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Number / date / % format ribbon | `chart_view`, `kpi_view`, `table_view`, `canvas_table`, text with dataRef | `NumberFormatSection` → `applyDisplayFormatSpecToBlock` → `updateSelected` (`displayFormatSelection.ts`) | `upsert_block` + BE enrich | persisted format fields on block; paint `display*` / `serverDisplayApplied` | `serverDisplayPaint` / chart·kpi·table views | `TARGET_upsert_plus_enrich` (**enrich already BE**) |
| Format dialog (modal) | same | `DisplayFormatDialog` same `onChange` | same | same | same | `TARGET_upsert_plus_enrich` |

---

## H. Chart design — layout / quick layout / axes / series

Sources: `ChartDesignSections.tsx`, `chartQuickLayouts.ts`, `ChartSeriesSection.tsx`.

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Add chart element menu | `chart_view` | `applyAddElementChoice` / `toggleElement` → `updateSelected` chartOptions/parts | `upsert_block` | `nativeConfig` | `ChartViewBlockView` | `TARGET_upsert_block` |
| Quick layout presets (5) | `chart_view` | `applyLayout` → `applyChartQuickLayout` → `updateSelected` | `upsert_block` | `nativeConfig` | chart elements visibility | `TARGET_upsert_block` |
| Chart colors / styles menu | `chart_view` | `ChartStylesSection` → `persistOptions` | `upsert_block` | `nativeConfig` | series chart widget | `TARGET_upsert_block` |
| Change chart type | `chart_view` | `setChartType` → `updateSelected({ chartType })` | `upsert_block` | `nativeConfig` | chart type switch | `TARGET_upsert_block` |
| Chart labels toggles | `chart_view` | `ChartLabelsSection` element toggles | `upsert_block` | `nativeConfig` | labels paint | `TARGET_upsert_block` |
| Chart axes toggles (axes/grid/goal) | `chart_view` | `ChartAxesSection` → `toggleElement` / `persistOptions` (legendSort) | `upsert_block` | `nativeConfig` | axes/grid/goal line | `TARGET_upsert_block` |
| Series color picker | `chart_view` | `ChartSeriesSection` → `patchChartSeriesAppearance` | `upsert_block` | `nativeConfig` | series stroke/fill | `TARGET_upsert_block` |
| Open Dados from chart layout | `chart_view` | `openDataPanel` | — | — | — | `NAV_ONLY` |

### ChartAxes (data projection) — Data surface (not Elemento section)

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Category / series / goal wells | `chart_view` | `ChartAxesProjectionEditor` via `VisualDataViewInspector` / `ChartSelectDataModal` → `updateSelected({ chartProjection })` | `upsert_block` | `nativeConfig`; enrich → `serverProjectionApplied` | bake + chart paint | `TARGET_upsert_block` (+ projection enrich) |
| Series aggregation / reorder | `chart_view` | same editor `persist` | `upsert_block` | `nativeConfig` | projected series | `TARGET_upsert_block` |

---

## I. Table / KPI / canvas table (typed Elemento)

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Table style options / styles / borders / typography | `table_view` | `TableDesignSections` / `TableTypographySection` → `updateSelected` | `upsert_block` | `nativeConfig` | `TableViewBlockView` | `TARGET_upsert_block` |
| Table layout data / size / align | `table_view` | `TableLayoutSections` → `applyOptions` / projection column width | `upsert_block` | `nativeConfig` | table layout | `TARGET_upsert_block` |
| KPI appearance / colors | `kpi_view` | `KpiAppearanceSection` → `persistOptions` / pane inspector | `upsert_block` | `nativeConfig` | KPI views | `TARGET_upsert_block` |
| Canvas table cells / merge / style | `canvas_table` | `CanvasTableSection` → cell patches | `upsert_block` | `nativeConfig` | canvas table paint | `TARGET_upsert_block` |
| Input binding (pane) | `input` | `InputBindingSection` → inspectors (ribbon null) | `upsert_block` | `nativeConfig` | input view + filters | `TARGET_upsert_block` |
| Data source hint | data / `data_source` | `DataSourceHintSection` | mostly NAV / label | — | Elemento hint | `NAV_ONLY` / light upsert |

---

## J. DataBinding (Dados ribbon / side panel)

Sources: `DataBindingInspector.tsx`, `ComunicadoDataRibbon.tsx`, `VisualDataViewInspector.tsx`, `CanvasTableDataBindingInspector.tsx`, `TextDataBindingInspector.tsx`.

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Route / params / refresh | data-bound | `DataBindingInspector` → `updateSelected` / `updateBlock` on `dataBinding` | `upsert_block` | `nativeConfig`; runtime enrich rows | views via resolved data | `TARGET_upsert_block` |
| Field labels | data-bound | `FieldLabelsEditor` | `upsert_block` | `nativeConfig` | labels in paint | `TARGET_upsert_block` |
| Duplicate from Dados | selected data block | button → `duplicateSelected()` | `duplicate_blocks` | `nativeConfig` | clones on stage | `TARGET_duplicate_blocks` (**GAP**) |
| Preview / test route | data-bound | `previewTvDataRoute` (read-only) | — | preview payload | inspector only | `NAV_ONLY` |
| Chart projection in Dados | `chart_view` | see §H ChartAxesProjectionEditor | `upsert_block` | `nativeConfig` | chart | `TARGET_upsert_block` |

---

## K. Actions — duplicate / remove

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Duplicate | `*` | `ActionsSection` → `FormatRibbonElementActions` → `duplicateSelected` → **local** `duplicateBlocksWithDataPolicy` + `updateBlocks` (`useComunicadoEditorBlocks.ts` L1019–1067). BE: `duplicate_blocks` in `patch_service.py` / `block_layout_service.py` — **no FE commit helper** | `duplicate_blocks` | `nativeConfig` | stage clones | `TARGET_duplicate_blocks` (**GAP**) |
| Remove | `*` | `removeSelected` | delete op / upsert remove — out of ribbon create/style set; today local filter blocks | (persist via updateSlide / future delete op) | stage | `TARGET_upsert_block` or dedicated delete — local today |
| Media shortcuts in Actions | `image`/`video` | crop scroll / library / upload | `upsert_block` / NAV | `nativeConfig` | media | mixed `NAV_ONLY` / `TARGET_upsert_block` |

---

## L. Context menu / keyboard (sibling surfaces)

Same mutations as ribbon; cited for completeness — `CONFIRMADO_NO_CODIGO`.

| Control | Types | Current path | Target mutation | Response field | Paint consumer | Status |
|---|---|---|---|---|---|---|
| Context align / z / duplicate | `*` | `ComunicadoStageContextMenu.tsx` → same editor actions | align / reorder_z / duplicate_blocks | `nativeConfig` | stage | same as §§B–C–K |
| Ctrl+D duplicate | `*` | `useComunicadoEditorKeyboard` → `duplicateSelected` | `duplicate_blocks` | `nativeConfig` | stage | `TARGET_duplicate_blocks` (**GAP**) |

---

## Gap summary (vs PRESENTATION-001 target)

| Area | Current | Target | Evidence |
|---|---|---|---|
| Align / distribute / slide-align | `commitAlignBlocks` wired | `align_blocks` | `presentationMutationClient.ts` L59–76; blocks hook L1375–1397 |
| Z-order menu / panel chevrons | `commitReorderBlockZ` wired | `reorder_block_z` | client L78–95; hook L1225–1254 |
| Layers drag reorder | local `updateBlocks` | `reorder_block_z` | hook L1275–1280 |
| Same-size | local only | `align_blocks` or `upsert_block` | hook L1402–1409 |
| Create (basic addBlock) | `commitCreateBlock` + place upsert | `create_block` | hook L289–344 |
| Style / frame / options / dataBinding / chart·table options | draft `updateSelected` | `upsert_block` deep-merge | hook L749–757; client `commitUpsertBlocks` L97–112 exists but not on every style write |
| Duplicate | FE-only clone | `duplicate_blocks` | BE `_op_duplicate_blocks`; no `commitDuplicate*` in client |
| Display format | FE persists format fields; BE enrich paints | `upsert_block` + enrich | `NumberFormatSection` + `DisplayFormatService` |

---

## Control count

| Bucket | Rows |
|---|---:|
| A Create | 11 |
| B Align/distribute/same-size | 7 |
| C Layers/z | 12 |
| D Organize group/rotate/session | 4 |
| E Frame/display/appearance | 4 |
| F Style chrome | 10 |
| G Display format | 2 |
| H Chart design + axes data | 10 |
| I Table/KPI/canvas/input | 6 |
| J DataBinding | 5 |
| K Actions | 3 |
| L Context/keyboard | 2 |
| **CONTROL_ROWS** | **78** |

All rows: **CONFIRMADO_NO_CODIGO**.
