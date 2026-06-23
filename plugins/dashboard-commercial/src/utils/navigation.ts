import type { CommercialFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readCommercialFilters,
} from "./filterUrl";

let commercialNavStackDepth = 0;
let suppressPopstateDepthChange = false;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    commercialNavStackDepth = Math.max(0, commercialNavStackDepth - 1);
  });
}

export function navigateCommercial(path: string, filters?: CommercialFilterUrlState) {
  const [rawPath, rawSearch] = path.split("?");
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const resolvedFilters =
    filters ??
    (rawSearch ? readCommercialFilters(`?${rawSearch}`) : readCommercialFilters());
  const query = buildFilterSearchParams(resolvedFilters);
  const target = `${basePath}${query}`;

  if (window.location.pathname === basePath && window.location.search === query) {
    return;
  }

  window.history.pushState(null, "", target);
  commercialNavStackDepth += 1;
  suppressPopstateDepthChange = true;
  window.dispatchEvent(new PopStateEvent("popstate"));
  suppressPopstateDepthChange = false;
}

export function navigateCommercialBack(
  fallbackPath: string,
  filters?: CommercialFilterUrlState
) {
  if (typeof window === "undefined") return;

  if (commercialNavStackDepth > 0) {
    window.history.back();
    return;
  }

  navigateCommercial(fallbackPath, filters);
}

export { appendFiltersToPath };
