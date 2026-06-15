import type { ProductionFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readFiltersFromUrl,
  readProductionFilters,
} from "./filterUrl";

let productionNavStackDepth = 0;
let suppressPopstateDepthChange = false;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    productionNavStackDepth = Math.max(0, productionNavStackDepth - 1);
  });
}

export function navigateProduction(
  path: string,
  filters?: ProductionFilterUrlState
) {
  const [rawPath, rawSearch] = path.split("?");
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const resolvedFilters =
    filters ??
    (rawSearch ? readFiltersFromUrl(`?${rawSearch}`) : readProductionFilters());
  const query = buildFilterSearchParams(resolvedFilters);
  const target = `${basePath}${query}`;

  if (
    window.location.pathname === basePath &&
    window.location.search === query
  ) {
    return;
  }

  window.history.pushState(null, "", target);
  productionNavStackDepth += 1;
  suppressPopstateDepthChange = true;
  window.dispatchEvent(new PopStateEvent("popstate"));
  suppressPopstateDepthChange = false;
}

export function navigateProductionBack(
  fallbackPath: string,
  filters?: ProductionFilterUrlState
) {
  if (typeof window === "undefined") return;

  if (productionNavStackDepth > 0) {
    window.history.back();
    return;
  }

  navigateProduction(fallbackPath, filters);
}

export function canNavigateProductionBack(): boolean {
  return productionNavStackDepth > 0;
}

export { appendFiltersToPath };
