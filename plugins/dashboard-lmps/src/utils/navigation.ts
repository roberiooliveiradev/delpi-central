import type { LmpsFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readLmpsFilters,
} from "./filterUrl";

let lmpsNavStackDepth = 0;
let suppressPopstateDepthChange = false;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    lmpsNavStackDepth = Math.max(0, lmpsNavStackDepth - 1);
  });
}

export function navigateLmps(path: string, filters?: LmpsFilterUrlState) {
  const [rawPath, rawSearch] = path.split("?");
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const resolvedFilters =
    filters ?? (rawSearch ? readLmpsFilters(`?${rawSearch}`) : readLmpsFilters());
  const query = buildFilterSearchParams(resolvedFilters);
  const target = `${basePath}${query}`;

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
