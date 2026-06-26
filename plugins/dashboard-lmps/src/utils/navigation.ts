import type { LmpsFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readLmpsFilters,
} from "./filterUrl";

let lmpsNavStackDepth = 0;
let suppressPopstateDepthChange = false;

function isLmpsDetailPath(basePath: string): boolean {
  return /\/ov\/[^/]+$/.test(basePath);
}

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    lmpsNavStackDepth = Math.max(0, lmpsNavStackDepth - 1);
  });
}

export function navigateLmps(path: string, filters?: LmpsFilterUrlState) {
  const questionIndex = path.indexOf("?");
  const rawPath = questionIndex >= 0 ? path.slice(0, questionIndex) : path;
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const rawSearch = questionIndex >= 0 ? path.slice(questionIndex + 1) : "";

  const target =
    rawSearch && (filters === undefined || isLmpsDetailPath(basePath))
      ? `${basePath}?${rawSearch}`
      : (() => {
          const resolvedFilters =
            filters ??
            (rawSearch ? readLmpsFilters(`?${rawSearch}`) : readLmpsFilters());
          return `${basePath}${buildFilterSearchParams(resolvedFilters)}`;
        })();

  const query = target.includes("?") ? target.slice(target.indexOf("?")) : "";

  if (window.location.pathname === basePath && window.location.search === query) {
    return;
  }

  window.history.pushState(null, "", target);
  lmpsNavStackDepth += 1;
  suppressPopstateDepthChange = true;
  window.dispatchEvent(new PopStateEvent("popstate"));
  suppressPopstateDepthChange = false;
}

export function navigateLmpsBack(fallbackPath: string, filters?: LmpsFilterUrlState) {
  if (typeof window === "undefined") return;

  if (lmpsNavStackDepth > 0) {
    window.history.back();
    return;
  }

  navigateLmps(fallbackPath, filters);
}

export { appendFiltersToPath };
