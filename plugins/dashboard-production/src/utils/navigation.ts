import type { ProductionFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readFiltersFromUrl,
  readProductionFilters,
} from "./filterUrl";

let productionNavStackDepth = 0;
let suppressPopstateDepthChange = false;

function isProductionDetailPath(basePath: string): boolean {
  return /\/(otd\/op|oee\/appointment)\/[^/]+$/.test(basePath);
}

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
  const questionIndex = path.indexOf("?");
  const rawPath = questionIndex >= 0 ? path.slice(0, questionIndex) : path;
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const rawSearch = questionIndex >= 0 ? path.slice(questionIndex + 1) : "";

  const target =
    rawSearch && isProductionDetailPath(basePath)
      ? `${basePath}?${rawSearch}`
      : (() => {
          const resolvedFilters =
            filters ??
            (rawSearch
              ? readFiltersFromUrl(`?${rawSearch}`)
              : readProductionFilters());
          return `${basePath}${buildFilterSearchParams(resolvedFilters)}`;
        })();

  const query = target.includes("?") ? target.slice(target.indexOf("?")) : "";

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
