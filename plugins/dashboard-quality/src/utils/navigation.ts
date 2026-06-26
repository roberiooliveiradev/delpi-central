import type { QualityFilterUrlState } from "./filterUrl";
import { appendFiltersToPath, readQualityFilters } from "./filterUrl";

let qualityNavStackDepth = 0;
let suppressPopstateDepthChange = false;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    qualityNavStackDepth = Math.max(0, qualityNavStackDepth - 1);
  });
}

export function navigateQuality(path: string, filterState?: QualityFilterUrlState) {
  const basePath = path.startsWith("/") ? path : `/${path}`;
  const target = filterState ? appendFiltersToPath(basePath, filterState) : basePath;

  if (window.location.pathname + window.location.search === target) {
    return;
  }

  window.history.pushState(null, "", target);
  qualityNavStackDepth += 1;
  suppressPopstateDepthChange = true;
  window.dispatchEvent(new PopStateEvent("popstate"));
  suppressPopstateDepthChange = false;
}

export function navigateQualityBack(
  fallbackPath: string,
  filterState?: QualityFilterUrlState
) {
  if (typeof window === "undefined") return;

  if (qualityNavStackDepth > 0) {
    window.history.back();
    return;
  }

  navigateQuality(fallbackPath, filterState ?? readQualityFilters());
}
