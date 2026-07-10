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
  ComunicadoBlock,
  ComunicadoBlockAnimation,
  ComunicadoBlockAnimationDirection,
  ComunicadoBlockAnimationEasing,
  ComunicadoBlockAnimationKind,
  ComunicadoConfig,
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
  ComunicadoDataBinding,
  ComunicadoDataBlock,
  ComunicadoDataFilters,
  ComunicadoIconBlock,
  ComunicadoListType,
  ComunicadoNamedTextStyle,
  ComunicadoScreenData,
  ComunicadoShapeKind,
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
export { ComunicadoShapeGraphic, ComunicadoShapePreview } from "./comunicadoShapeGraphic";
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
  displayModeLabel,
  listDataPresentationOptions,
} from "./comunicadoDataPresentation";
export type { DataPresentationOption } from "./comunicadoDataPresentation";
export {
  blockCssStyle,
  buildTextDecoration,
  clampFontSize,
  clampFrame,
  comunicadoTextInnerStyle,
  createBlock,
  createDataBlock,
  createIconBlock,
  createShapeBlock,
  defaultDataBlockTypeForRoute,
  defaultFrame,
  defaultTextBlockStyle,
  defaultVerticalAlignForBlock,
  frameStyle,
  isDataBlockType,
  mergeDataFilters,
  nextZIndex,
  parseComunicadoConfig,
  parseTextDecorationFlags,
  newBlockId,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
} from "./comunicadoHelpers";
export { ComunicadoBlockView } from "./comunicadoBlockView";
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
export { ComunicadoMediaPlaceholder } from "./ComunicadoMediaPlaceholder";
export type { KpiScreenData, NativeSlidePayload } from "./NativeScreens";
