import type { EngineeringFilterUrlState } from "./filterUrl";
import {
  appendFiltersToPath,
  buildFilterSearchParams,
  readFiltersFromUrl,
  readEngineeringFilters,
} from "./filterUrl";

export function navigateEngineering(
  path: string,
  filters?: EngineeringFilterUrlState
) {
  const [rawPath, rawSearch] = path.split("?");
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const resolvedFilters =
    filters ??
    (rawSearch ? readFiltersFromUrl(`?${rawSearch}`) : readEngineeringFilters());
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
