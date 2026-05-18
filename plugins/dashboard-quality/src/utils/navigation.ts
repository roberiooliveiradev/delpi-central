import type { QualityFilterUrlState } from "./filterUrl";
import {
  buildFilterSearchParams,
  readFiltersFromUrl,
  readQualityFilters,
} from "./filterUrl";

/** Navegação client-side dentro do portal (evita reload completo do MFE). */
export function navigateQuality(
  path: string,
  filters?: QualityFilterUrlState
) {
  const [rawPath, rawSearch] = path.split("?");
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const resolvedFilters =
    filters ??
    (rawSearch ? readFiltersFromUrl(`?${rawSearch}`) : readQualityFilters());
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
