export type PresentationSlide = {
  id: string;
  sortOrder: number;
  slideType: "native" | "external" | string;
  durationSec?: number | null;
  title?: string;
  sectionId?: string | null;
  /** Override da transição da playlist (`fade` | `slide` | `none`). */
  transitionStyle?: string | null;
  native?: { config?: Record<string, unknown>; data?: Record<string, unknown> };
};

export type PresentationSection = {
  id: string;
  name: string;
  sortOrder: number;
  isActive?: boolean;
  isMain?: boolean;
};

export type PresentationPlaylist = {
  viewportProfile?: string;
  /** Dimensões custom em px (quando viewportProfile === "custom"). */
  viewportWidth?: number | null;
  viewportHeight?: number | null;
  transitionStyle?: string;
  globalRefreshSec?: number;
  defaultDurationSec?: number;
  /** presentation = auto-advance; meeting = manual. */
  playbackMode?: "presentation" | "meeting";
};

export type PresentationMeta = {
  nativeErrorAdvanceSec?: number;
  heartbeatIntervalSec?: number;
};

export type PresentationPayloadLike = {
  playlist: PresentationPlaylist;
  presentationMeta?: PresentationMeta;
  sections?: PresentationSection[];
  slides: PresentationSlide[];
};
