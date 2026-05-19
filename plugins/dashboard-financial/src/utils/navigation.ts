import type { FinancialFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readFiltersFromUrl,
  readFinancialFilters,
} from "./filterUrl";

export function navigateFinancial(
  path: string,
  filters?: FinancialFilterUrlState
) {
  const [rawPath, rawSearch] = path.split("?");
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const resolvedFilters =
    filters ??
    (rawSearch ? readFiltersFromUrl(`?${rawSearch}`) : readFinancialFilters());
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
