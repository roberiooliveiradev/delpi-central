const LAST_PLACEMENT_KEY = "pp-operator-last-placement";

export function readLastPlacementKey(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(LAST_PLACEMENT_KEY);
  } catch {
    return null;
  }
}

export function writeLastPlacementKey(placementKey: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LAST_PLACEMENT_KEY, placementKey);
  } catch {
    /* ignore quota errors */
  }
}
