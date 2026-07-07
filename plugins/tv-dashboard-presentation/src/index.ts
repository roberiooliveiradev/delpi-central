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
export type {
  ComunicadoBlock,
  ComunicadoConfig,
  ComunicadoDataBinding,
  ComunicadoDataBlock,
  ComunicadoDataFilters,
  ComunicadoScreenData,
  ComunicadoShapeKind,
} from "./comunicadoTypes";
export {
  COMUNICADO_FONT_FAMILIES,
  COMUNICADO_FONT_SIZE_MAX,
  COMUNICADO_FONT_SIZE_MIN,
  COMUNICADO_FONT_SIZE_STEP,
  COMUNICADO_LINE_HEIGHT_OPTIONS,
  COMUNICADO_SHAPE_KINDS,
} from "./comunicadoTypes";
export {
  blockCssStyle,
  buildTextDecoration,
  clampFontSize,
  clampFrame,
  comunicadoTextInnerStyle,
  createBlock,
  createDataBlock,
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
export { TvDataBlockView } from "./tvDataBlockView";
export { ComunicadoMediaPlaceholder } from "./ComunicadoMediaPlaceholder";
export type { KpiScreenData, NativeSlidePayload } from "./NativeScreens";
