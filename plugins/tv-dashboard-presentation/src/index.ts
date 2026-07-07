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
  createShapeBlock,
  defaultFrame,
  defaultTextBlockStyle,
  defaultVerticalAlignForBlock,
  frameStyle,
  nextZIndex,
  parseComunicadoConfig,
  parseTextDecorationFlags,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
} from "./comunicadoHelpers";
export { ComunicadoBlockView } from "./comunicadoBlockView";
export { ComunicadoMediaPlaceholder } from "./ComunicadoMediaPlaceholder";
export type { KpiScreenData, NativeSlidePayload } from "./NativeScreens";
