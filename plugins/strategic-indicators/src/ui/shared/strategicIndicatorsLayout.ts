/** Breakpoints de layout do plugin (CSS usa os mesmos valores em @media). */
export const SI_LAYOUT_BREAKPOINT = {
  phoneNarrow: 480,
  phone: 768,
  tablet: 1100,
  desktopCompact: 1280,
} as const;

export function siMaxWidthQuery(px: number): string {
  return `(max-width: ${px}px)`;
}

export function isSiTabletOrNarrowViewport(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  return window.matchMedia(
    siMaxWidthQuery(SI_LAYOUT_BREAKPOINT.tablet),
  ).matches;
}
