import "./native-screens.css";

export { usePresentationEngine } from "./usePresentationEngine";
export {
  buildAdminPresentationWsUrl,
  buildPresentationWsUrl,
  buildPublicPresentationWsUrl,
  usePresentationRealtime,
} from "./usePresentationRealtime";
export type { PresentationRealtimeEvent } from "./usePresentationRealtime";
export { useFullscreenStage } from "./useFullscreenStage";
export { NativeSlideView } from "./NativeScreens";
export { formatPct, formatNumber } from "./nativeFormat";
export type {
  PresentationMeta,
  PresentationPayloadLike,
  PresentationPlaylist,
  PresentationSlide,
} from "./types";
export type { UsePresentationEngineOptions } from "./usePresentationEngine";
export {
  PRESENTATION_TRANSITION_STYLES,
  isPresentationTransitionStyle,
  resolveSlideTransitionStyle,
  type PresentationTransitionStyle,
} from "./presentationTransition";
export type {
  ComunicadoBackground,
  ComunicadoBlock,
  ComunicadoBlockAnimation,
  ComunicadoBlockAnimationDirection,
  ComunicadoBlockAnimationEasing,
  ComunicadoBlockAnimationKind,
  ComunicadoBlockStyle,
  ComunicadoConfig,
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
  ComunicadoDataBinding,
  ComunicadoDataBlock,
  ComunicadoDataDisplayMode,
  ComunicadoDataFilters,
  ComunicadoDataResolved,
  ComunicadoFrame,
  ComunicadoIconBlock,
  ComunicadoListType,
  ComunicadoMediaBlock,
  ComunicadoNamedTextStyle,
  ComunicadoScreenData,
  ComunicadoShapeBlock,
  ComunicadoShapeKind,
  ComunicadoGeometryVertex,
  ComunicadoTextBlock,
} from "./comunicadoTypes";
export type { ComunicadoImageCrop } from "./comunicadoImageCrop";
export {
  COMUNICADO_IMAGE_CROP_FULL,
  comunicadoImageCropCssProperties,
  isFullComunicadoImageCrop,
  normalizeComunicadoImageCrop,
} from "./comunicadoImageCrop";
export {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_FONT_SIZE_MAX,
  COMUNICADO_FONT_SIZE_MIN,
  COMUNICADO_FONT_SIZE_STEP,
  COMUNICADO_ICON_OPTIONS,
  COMUNICADO_LINE_HEIGHT_OPTIONS,
} from "./comunicadoTypes";
export {
  COMUNICADO_SHAPE_CATALOG,
  COMUNICADO_SHAPE_CATALOG_CATEGORIES,
  COMUNICADO_SHAPE_KINDS,
  COMUNICADO_SHAPE_KIND_VALUES,
  comunicadoShapeLabel,
  isComunicadoShapeKind,
} from "./comunicadoShapeCatalog";
export {
  defaultStrokeWidthForPrimitive,
  isAreaShapeKind,
  isLineShapeKind,
  isPointShapeKind,
  resolveShapePrimitive,
  shapeSupportsFill,
  shapeSupportsStroke,
  type ComunicadoVisualPrimitive,
} from "./comunicadoVisualPrimitive";
export {
  COMUNICADO_LINE_VISUAL_PAD_PCT,
  COMUNICADO_MARKER_RADIUS_DEFAULT,
  COMUNICADO_POINT_HIT_SIZE_PCT,
  clampFrameForBlock,
  clampFrameForShapeBlock,
  geometryBoundingFrame,
  geometryToPersistedFrame,
  minimumVertexCount,
  resolveBlockHitFrame,
  resolveBlockPlacementStyle,
  resolveShapeGeometry,
  shapeBlockAllowsResize,
  syncLineVerticesFromFrame,
  type ComunicadoShapeGeometry,
} from "./comunicadoShapeGeometry";
export {
  ComunicadoShapeGraphic,
  ComunicadoShapePreview,
  lineArrowHeadPolygonPoints,
} from "./comunicadoShapeGraphic";
export {
  adjustmentHandleCssPosition,
  borderRadiusPxToCornerAdjustment,
  cornerAdjustmentToBorderRadiusPx,
  defaultShapeAdjustments,
  patchShapeAdjustment,
  resolveShapeAdjustments,
  shapeAdjustmentSpecs,
  shapeHasAdjustments,
  type ShapeAdjustmentSpec,
} from "./comunicadoShapeAdjustments";
export {
  applyBlockShapeChromeAdjustment,
  blockShapeChromeAdjustmentSpecs,
  blockSupportsShapeChromeHandles,
  resolveBlockSelectionBorderRadiusPx,
  resolveBlockShapeChromeAdjustmentValues,
  resolveBlockShapeChromeCornerPx,
} from "./comunicadoBlockShapeChrome";
export {
  COMUNICADO_GOOGLE_FONT_CATALOG,
  buildGoogleFontsStylesheetUrl,
  collectFontFamiliesFromComunicadoConfig,
  comunicadoFontFamilyOptions,
  ensureComunicadoGoogleFontsLoaded,
  resolveGoogleFontEntry,
  useComunicadoGoogleFonts,
  type ComunicadoFontFamilyOption,
  type ComunicadoGoogleFontEntry,
} from "./comunicadoGoogleFonts";
export { comunicadoBackgroundCssProperties } from "./comunicadoBackgroundStyle";
export {
  blockTypeForDisplayMode,
  defaultDisplayModeForInsert,
  displayModeLabel,
  displayModeOptionLabel,
  listDataPresentationOptions,
  UNIVERSAL_DISPLAY_MODES,
} from "./comunicadoDataPresentation";
export {
  buildDataPreviewFingerprint,
  DATA_REFRESH_SEC_DEFAULT,
  DATA_REFRESH_SEC_MAX,
  DATA_REFRESH_SEC_MIN,
  resolveDataBlockRefreshSec,
} from "./dataRefresh";
export type { DataPresentationOption } from "./comunicadoDataPresentation";
export {
  blockCssStyle,
  buildTextDecoration,
  clampFontSize,
  clampFrame,
  COMUNICADO_EDITOR_FONT_SCALE,
  comunicadoTextInnerStyle,
  createBlock,
  createDataBlock,
  createDataSourceBlock,
  createChartViewBlock,
  createTableViewBlock,
  createKpiViewBlock,
  createIconBlock,
  createShapeBlock,
  defaultDataBlockTypeForRoute,
  defaultFrame,
  defaultTextBlockStyle,
  defaultVerticalAlignForBlock,
  frameStyle,
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isFetchableDataBlockType,
  getLinkedDataSourceIds,
  shouldHideDataSourceOnStage,
  listDataSourceBlocks,
  dataSourceOptionsForInspector,
  resolveDataSourceLabel,
  resolvePreferredDataSourceId,
  mergeDataFilters,
  nextZIndex,
  parseComunicadoConfig,
  parseTextDecorationFlags,
  newBlockId,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
} from "./comunicadoHelpers";
export { ComunicadoBlockView } from "./comunicadoBlockView";
export { ComunicadoVisualBoxView } from "./ComunicadoVisualBoxView";
export {
  type ComunicadoVisualBoxBlock,
  type ComunicadoVisualBoxChrome,
  type ComunicadoVisualBoxMode,
  type ComunicadoVisualBoxProfile,
  defaultVerticalAlignForVisualBox,
  isComunicadoVisualBoxBlock,
  resolveVisualBoxChrome,
  resolveVisualBoxContentLayoutStyle,
  resolveVisualBoxProfile,
  visualBoxBlockModifierClasses,
  visualBoxSupportsInlineTextEditing,
  visualBoxSupportsShapeFormatting,
  visualBoxSupportsTextFormatting,
} from "./comunicadoVisualBox";
export { ComunicadoTextRunsView } from "./ComunicadoTextRunsView";
export {
  contentRunStyleToCss,
  contentRunsFromPlainText,
  hasRichTextRuns,
  normalizeContentRuns,
  plainTextFromContentRuns,
  resolveTextBlockDisplayRuns,
  serializeContentRuns,
  shouldPersistContentRuns,
  syncTextBlockFields,
} from "./comunicadoContentRuns";
export {
  compactContentRuns,
  contentRunInlineStyleProperties,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  hasPersistableContentRuns,
  insertLineBreakAtOffset,
  renderContentRunsHtml,
  restoreEditableTextSelection,
  selectionListTypeState,
  selectionRunStyleState,
  syncTextBlockFromRuns,
  toggleContentRunStyleInRange,
  toggleListTypeInRange,
  toggleListTypeOnAllLines,
  type ContentRunListSelectionState,
  type ContentRunSelectionStyleState,
  type ContentRunStyleToggleKey,
  type TextDisplaySegment,
} from "./comunicadoContentRunEditing";
export {
  groupContentRunsForDisplay,
  hasListContentRuns,
  splitContentRunsIntoLines,
} from "./comunicadoContentList";
export {
  applyNamedStyleInRange,
  applyNamedStyleOnAllLines,
  COMUNICADO_NAMED_TEXT_STYLE_OPTIONS,
  defaultNamedStyleForBlockType,
  hasNamedStyleContentRuns,
  namedTextStylePreset,
  resolveEffectiveRunStyle,
  resolveNamedStyleSelectionForBlock,
  selectionNamedStyleState,
  type ContentRunNamedStyleSelectionState,
} from "./comunicadoNamedTextStyles";
export {
  BLOCK_ENTRANCE_DELAY_MAX_MS,
  BLOCK_ENTRANCE_DELAY_MIN_MS,
  BLOCK_ENTRANCE_DELAY_STEP_MS,
  BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
  BLOCK_ENTRANCE_DURATION_MAX_MS,
  BLOCK_ENTRANCE_DURATION_MIN_MS,
  BLOCK_ENTRANCE_DURATION_STEP_MS,
  BLOCK_ENTRANCE_PRESET_OPTIONS,
  blockEntranceAnimationClass,
  blockEntranceAnimationStyle,
  assignStaggeredEntranceDelays,
  clearEntranceAnimations,
  syncEntranceDelaysSameInstant,
  entranceAnimationFromPreset,
  entrancePresetValue,
  normalizeBlockAnimations,
  resolveEntranceAnimation,
  serializeBlockAnimations,
} from "./comunicadoBlockAnimations";
export {
  appendHrefLineToRuns,
  hrefLineStyle,
  isLikelyExternalUrl,
  normalizeHrefInput,
  partitionTextBlockRunsAndHref,
  renderTextBlockEditorHtml,
} from "./comunicadoTextBlockLink";
export { TvDataBlockView } from "./tvDataBlockView";
export { ChartViewBlockView } from "./chartViewBlockView";
export { KpiViewBlockView } from "./kpiViewBlockView";
export {
  DEFAULT_COMUNICADO_KPI_OPTIONS,
  mergeComunicadoKpiOptions,
  type ComunicadoKpiOptions,
} from "./comunicadoKpiOptions";
export {
  resolveKpiViewPresentation,
  type KpiViewPresentation,
} from "./resolveKpiPresentation";
export {
  KPI_ELEMENT_CATALOG,
  KPI_PART_DATA_ATTR,
  applyKpiElementVisibility,
  deleteKpiPart,
  getKpiPartState,
  isKpiElementEnabled,
  isKpiElementOpenForPart,
  kpiElementPrimaryPartRef,
  kpiPartAllowsDelete,
  kpiPartAllowsEdit,
  mergeKpiPartsWithOptions,
  normalizeKpiPartsForLoad,
  partsToKpiOptions,
  serializeKpiPartRef,
  upsertKpiPartState,
  type ComunicadoKpiInteraction,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiPartsMap,
  type KpiElementId,
} from "./comunicadoKpiParts";
export { TableViewBlockView } from "./tableViewBlockView";
export { DataSourceBlockView } from "./dataSourceBlockView";
export {
  CHART_ELEMENT_CATALOG,
  isChartElementApplicable,
  isChartElementEnabled,
  setChartElementEnabled,
  applyChartElementVisibility,
  chartElementPartRefs,
  chartElementPrimaryPartRef,
  chartElementIdForPartRef,
  isChartElementOpenForPart,
  type ChartElementDefinition,
  type ChartElementId,
} from "./chartElementCatalog";
export {
  CHART_MARKER_RADIUS,
  CHART_PART_DATA_ATTR,
  CHART_SERIES_LINE_STROKE_WIDTH,
  applyMarkerStyleToAll,
  bindChartPartPointer,
  chartOptionsToParts,
  chartPartAllowsDelete,
  chartPartAllowsEdit,
  chartPartAllowsMove,
  chartPartAllowsResize,
  chartPartCapabilities,
  clampChartPartFrame,
  deleteChartPart,
  filterVisibleSeriesPoints,
  findChartPartFromTarget,
  getChartPartState,
  isChartPartRefEqual,
  mergeChartPartsWithOptions,
  mergeSeriesChartOptionsWithParts,
  normalizeChartPartsForLoad,
  nudgeChartPartFrame,
  parseChartPartRef,
  partsToChartOptions,
  resizeChartPartFrame,
  resolveChartAreaStyle,
  resolveChartPartFrameRoot,
  resolvePlotAreaStyle,
  serializeChartPartRef,
  upsertChartPartState,
  chartPartVisualPrimitive,
  chartPrimitiveSupportsFill,
  chartPrimitiveSupportsStroke,
  type ComunicadoChartPartCapabilities,
  type ComunicadoChartInteraction,
  type ComunicadoChartPartFrame,
  type ComunicadoChartPartRef,
  type ComunicadoChartPartResizeHandle,
  type ComunicadoChartPartsMap,
} from "./comunicadoChartParts";
export {
  chartTypeLabel,
  tablePresetLabel,
  chartTypeToLegacyDisplayMode,
  chartTypeHasBasicRender,
  toSeriesChartKind,
  pieInnerRadiusForChartType,
} from "./comunicadoChartView";
export {
  CHART_LEGEND_POSITION_OPTIONS,
  CHART_VALUE_FORMAT_OPTIONS,
  DEFAULT_COMUNICADO_CHART_OPTIONS,
  OFFICE_CHART_AREA_FILL,
  OFFICE_CHART_AREA_STROKE,
  OFFICE_CHART_PLOT_FILL,
  OFFICE_CHART_PLOT_STROKE,
  OFFICE_CHART_SERIES_COLOR,
  formatSeriesChartValue,
  mergeComunicadoChartOptions,
  resolveChartDisplayOptions,
  type ComunicadoChartLegendPosition,
  type ComunicadoChartOptions,
  type ComunicadoChartValueFormat,
} from "./comunicadoChartOptions";
export {
  DEFAULT_COMUNICADO_TABLE_OPTIONS,
  TABLE_TEXT_ALIGN_OPTIONS,
  TABLE_VALUE_FORMAT_OPTIONS,
  formatTableCellValue,
  mergeComunicadoTableOptions,
  presetDefaultTableOptions,
  resolveTableDisplayOptions,
  type ComunicadoTableOptions,
  type ComunicadoTableTextAlign,
  type ComunicadoTableValueFormat,
} from "./comunicadoTableOptions";
export {
  TABLE_PART_DATA_ATTR,
  deleteTablePart,
  isTablePartRefEqual,
  mergeTablePartsWithOptions,
  parseTablePartRef,
  partsToTableOptions,
  serializeTablePartRef,
  tableElementPrimaryPartRef,
  tableOptionsToParts,
  tablePartAllowsDelete,
  tablePartAllowsEdit,
  upsertTablePartState,
  type ComunicadoTableInteraction,
  type ComunicadoTablePartRef,
  type ComunicadoTablePartsMap,
} from "./comunicadoTableParts";
export {
  TABLE_ELEMENT_CATALOG,
  isTableElementEnabled,
  setTableElementEnabled,
  type TableElementDefinition,
  type TableElementId,
} from "./tableElementCatalog";
export { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
export { ConfigurableTable } from "./ConfigurableTable";
export type { ComunicadoChartType, ComunicadoTablePreset, ComunicadoDataSourceBlock, ComunicadoChartViewBlock, ComunicadoTableViewBlock, ComunicadoKpiViewBlock } from "./comunicadoTypes";
export {
  resolveChartType,
  resolveEffectiveDisplayMode,
  resolveTableColumns,
  type TvDataTableColumn,
} from "./tvDataPresentation";
export { ComunicadoMediaPlaceholder } from "./ComunicadoMediaPlaceholder";
export type { KpiScreenData, NativeSlidePayload } from "./NativeScreens";
