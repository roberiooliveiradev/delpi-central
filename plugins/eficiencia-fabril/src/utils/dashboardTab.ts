export const DASHBOARD_TAB_EFFICIENCY = "efficiency" as const;
export const DASHBOARD_TAB_UNPRODUCTIVE_HOURS = "unproductive-hours" as const;

export type EficienciaFabrilDashboardTab =
  | typeof DASHBOARD_TAB_EFFICIENCY
  | typeof DASHBOARD_TAB_UNPRODUCTIVE_HOURS;

export const DASHBOARD_TAB_QUERY_KEY = "tab";

export function parseDashboardTab(value: string | null | undefined): EficienciaFabrilDashboardTab {
  const normalized = (value ?? "").trim().toLowerCase();
  if (normalized === DASHBOARD_TAB_UNPRODUCTIVE_HOURS) {
    return DASHBOARD_TAB_UNPRODUCTIVE_HOURS;
  }
  return DASHBOARD_TAB_EFFICIENCY;
}

export function readDashboardTabFromSearch(search: string): EficienciaFabrilDashboardTab {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  return parseDashboardTab(params.get(DASHBOARD_TAB_QUERY_KEY));
}

export function readDashboardTabFromLocation(
  search: string = typeof window !== "undefined" ? window.location.search : "",
): EficienciaFabrilDashboardTab {
  return readDashboardTabFromSearch(search);
}

/** Monta search string com `tab` (omitte se efficiency = default). */
export function buildDashboardTabSearch(
  tab: EficienciaFabrilDashboardTab,
  currentSearch: string = "",
): string {
  const params = new URLSearchParams(
    currentSearch.startsWith("?") ? currentSearch.slice(1) : currentSearch,
  );
  if (tab === DASHBOARD_TAB_EFFICIENCY) {
    params.delete(DASHBOARD_TAB_QUERY_KEY);
  } else {
    params.set(DASHBOARD_TAB_QUERY_KEY, tab);
  }
  const next = params.toString();
  return next ? `?${next}` : "";
}

export function writeDashboardTabToUrl(
  tab: EficienciaFabrilDashboardTab,
  options?: { replace?: boolean },
): void {
  if (typeof window === "undefined") return;
  const nextSearch = buildDashboardTabSearch(tab, window.location.search);
  const nextUrl = `${window.location.pathname}${nextSearch}${window.location.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (nextUrl === current) return;
  if (options?.replace === false) {
    window.history.pushState(null, "", nextUrl);
  } else {
    window.history.replaceState(null, "", nextUrl);
  }
}
