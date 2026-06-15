import type { ProductionFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readFiltersFromUrl,
  readProductionFilters,
} from "./filterUrl";

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
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export { appendFiltersToPath };
