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
export { COMUNICADO_FONT_FAMILIES, COMUNICADO_SHAPE_KINDS } from "./comunicadoTypes";
export {
  blockCssStyle,
  clampFrame,
  createBlock,
  createShapeBlock,
  defaultFrame,
  frameStyle,
  nextZIndex,
  parseComunicadoConfig,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
} from "./comunicadoHelpers";
export { ComunicadoBlockView } from "./comunicadoBlockView";
export type { KpiScreenData, NativeSlidePayload } from "./NativeScreens";
