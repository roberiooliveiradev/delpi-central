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
export type { ComunicadoBlock, ComunicadoConfig, ComunicadoScreenData } from "./comunicadoTypes";
export {
  createBlock,
  defaultFrame,
  frameStyle,
  parseComunicadoConfig,
  serializeComunicadoConfig,
} from "./comunicadoHelpers";
export type { KpiScreenData, NativeSlidePayload } from "./NativeScreens";
