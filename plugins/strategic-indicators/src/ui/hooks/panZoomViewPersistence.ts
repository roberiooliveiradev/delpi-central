import type { PanZoomTransform } from "./usePanZoom";

export function loadPersistedPanZoomTransform(
  key: string,
): PanZoomTransform | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(key);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as Partial<PanZoomTransform>;
    if (
      typeof parsed.x !== "number" ||
      typeof parsed.y !== "number" ||
      typeof parsed.scale !== "number" ||
      !Number.isFinite(parsed.x) ||
      !Number.isFinite(parsed.y) ||
      !Number.isFinite(parsed.scale) ||
      parsed.scale <= 0
    ) {
      return null;
    }

    return {
      x: parsed.x,
      y: parsed.y,
      scale: parsed.scale,
    };
  } catch {
    return null;
  }
}

export function savePersistedPanZoomTransform(
  key: string,
  transform: PanZoomTransform,
): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.sessionStorage.setItem(key, JSON.stringify(transform));
  } catch {
    // quota ou modo privado
  }
}
