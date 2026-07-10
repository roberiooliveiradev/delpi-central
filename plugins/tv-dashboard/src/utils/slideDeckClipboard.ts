import type { Slide } from "../api/tvDashboardApi";

export type SlideClipboardPayload = {
  slideType: Slide["slideType"];
  title: string;
  durationSec?: number;
  nativeScreenKey?: string | null;
  nativeConfig?: Record<string, unknown> | null;
  externalUrl?: string | null;
  transitionStyle?: string | null;
};

export function slidePayloadForClipboard(slide: Slide): SlideClipboardPayload {
  return {
    slideType: slide.slideType,
    title: slide.title,
    durationSec: slide.durationSec ?? undefined,
    nativeScreenKey: slide.nativeScreenKey ?? undefined,
    nativeConfig: slide.nativeConfig ? { ...slide.nativeConfig } : slide.nativeConfig,
    externalUrl: slide.externalUrl ?? undefined,
    transitionStyle: slide.transitionStyle ?? undefined,
  };
}

export function pasteTitleFromClipboard(payload: SlideClipboardPayload): string {
  const base = payload.title.trim() || "Tela";
  return base.endsWith(" (cópia)") ? base : `${base} (cópia)`;
}
