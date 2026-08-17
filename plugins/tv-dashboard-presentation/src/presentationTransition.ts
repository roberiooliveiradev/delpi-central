import type { PresentationPlaylist, PresentationSlide } from "./types";

export const PRESENTATION_TRANSITION_STYLES = [
  "fade",
  "dissolve",
  "slide",
  "push",
  "wipe",
  "zoom",
  "none",
] as const;

export type PresentationTransitionStyle = (typeof PRESENTATION_TRANSITION_STYLES)[number];

export const PRESENTATION_TRANSITION_LABELS: Record<PresentationTransitionStyle, string> = {
  fade: "Suavizar",
  dissolve: "Dissolver",
  slide: "Deslizar",
  push: "Empurrar",
  wipe: "Revelar",
  zoom: "Zoom suave",
  none: "Sem transição",
};

export function formatPresentationTransitionLabel(
  style: PresentationTransitionStyle | string,
): string {
  return isPresentationTransitionStyle(style)
    ? PRESENTATION_TRANSITION_LABELS[style]
    : style;
}

export function isPresentationTransitionStyle(
  value: string | null | undefined,
): value is PresentationTransitionStyle {
  return (
    value != null &&
    (PRESENTATION_TRANSITION_STYLES as readonly string[]).includes(value)
  );
}

/** Transição ao exibir o slide: override do slide ou fallback da playlist. */
export function resolveSlideTransitionStyle(
  slide: Pick<PresentationSlide, "transitionStyle"> | null | undefined,
  playlist: Pick<PresentationPlaylist, "transitionStyle"> | null | undefined,
): PresentationTransitionStyle {
  if (isPresentationTransitionStyle(slide?.transitionStyle)) {
    return slide.transitionStyle;
  }
  if (isPresentationTransitionStyle(playlist?.transitionStyle)) {
    return playlist.transitionStyle;
  }
  return "fade";
}
