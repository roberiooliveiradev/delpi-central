export type PresentationSlide = {
  id: string;
  sortOrder: number;
  slideType: "native" | "external" | string;
  durationSec?: number | null;
  title?: string;
  /** Override da transição da playlist (`fade` | `slide` | `none`). */
  transitionStyle?: string | null;
  native?: { config?: Record<string, unknown>; data?: Record<string, unknown> };
};

export type PresentationPlaylist = {
  viewportProfile?: string;
  transitionStyle?: string;
  globalRefreshSec?: number;
  defaultDurationSec?: number;
};

export type PresentationMeta = {
  nativeErrorAdvanceSec?: number;
  heartbeatIntervalSec?: number;
};

export type PresentationPayloadLike = {
  playlist: PresentationPlaylist;
  presentationMeta?: PresentationMeta;
  slides: PresentationSlide[];
};
