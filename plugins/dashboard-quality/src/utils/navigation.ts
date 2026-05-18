import type { QualityFilterUrlState } from "./filterUrl";
import { buildFilterSearchParams } from "./filterUrl";

/** Navegação client-side dentro do portal (evita reload completo do MFE). */
export function navigateQuality(
  path: string,
  filters?: QualityFilterUrlState
) {
  const [rawPath, rawSearch] = path.split("?");
  const basePath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  const query = filters
    ? buildFilterSearchParams(filters)
    : rawSearch
      ? `?${rawSearch}`
      : "";
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
