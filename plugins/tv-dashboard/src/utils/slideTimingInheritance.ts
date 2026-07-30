/**
 * Cascata duração/transição: slide → seção → playlist (espelha a API).
 */

export function resolveSlideDurationSec(args: {
  slideDuration: number | null | undefined;
  sectionDefault?: number | null;
  playlistDefault?: number | null;
  fallback?: number;
}): number {
  const { slideDuration, sectionDefault, playlistDefault, fallback = 30 } = args;
  if (slideDuration != null) return slideDuration;
  if (sectionDefault != null) return sectionDefault;
  if (playlistDefault != null) return playlistDefault;
  return fallback;
}

export function resolveSlideTransitionStyle(args: {
  slideTransition: string | null | undefined;
  sectionTransition?: string | null;
  playlistTransition?: string | null;
  fallback?: string;
}): string {
  const {
    slideTransition,
    sectionTransition,
    playlistTransition,
    fallback = "fade",
  } = args;
  if (slideTransition) return slideTransition;
  if (sectionTransition) return sectionTransition;
  if (playlistTransition) return playlistTransition;
  return fallback;
}

export function slideDurationIsOverride(slideDuration: number | null | undefined): boolean {
  return slideDuration != null;
}

const TRANSITION_LABELS: Record<string, string> = {
  fade: "Fade",
  slide: "Deslizar",
  none: "Sem transição",
};

export function formatSlideTransitionLabel(style: string): string {
  return TRANSITION_LABELS[style] ?? style;
}
