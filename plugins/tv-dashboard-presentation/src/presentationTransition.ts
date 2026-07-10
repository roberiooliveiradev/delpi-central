import type { PresentationPlaylist, PresentationSlide } from "./types";

export const PRESENTATION_TRANSITION_STYLES = ["fade", "slide", "none"] as const;

export type PresentationTransitionStyle = (typeof PRESENTATION_TRANSITION_STYLES)[number];

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
