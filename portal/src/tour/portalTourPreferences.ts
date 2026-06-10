const STORAGE_KEY = "delpi.portalTour.animationsEnabled";

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function getPortalTourAnimationsEnabled(): boolean {
  if (typeof window === "undefined") return true;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === "0" || raw === "false") return false;
    if (raw === "1" || raw === "true") return true;
  } catch {
    // ignore
  }
  return true;
}

export function setPortalTourAnimationsEnabled(enabled: boolean): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, enabled ? "1" : "0");
  } catch {
    // ignore
  }
  window.dispatchEvent(
    new CustomEvent("DELPI_PORTAL_TOUR_PREFERENCES_CHANGED"),
  );
}

export function shouldPlayPortalTourAnimations(): boolean {
  return getPortalTourAnimationsEnabled() && !prefersReducedMotion();
}
