import type { SuppliesFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readFiltersFromUrl,
  readSuppliesFilters,
} from "./filterUrl";

export function navigateSupplies(
  path: string,
  filters?: SuppliesFilterUrlState
) {
  const [rawPath, rawSearch] = path.split("?");
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const resolvedFilters =
    filters ??
    (rawSearch ? readFiltersFromUrl(`?${rawSearch}`) : readSuppliesFilters());
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
