export const OPPORTUNITIES_VIEW_VALUES = ["opportunity", "collaborator"] as const;

export type OpportunitiesView = (typeof OPPORTUNITIES_VIEW_VALUES)[number];

export const DEFAULT_OPPORTUNITIES_VIEW: OpportunitiesView = "opportunity";

const VIEW_VALUES = new Set<string>(OPPORTUNITIES_VIEW_VALUES);

export function normalizeOpportunitiesView(
  value: string | null | undefined,
): OpportunitiesView {
  const normalized = (value ?? "").trim().toLowerCase();
  return VIEW_VALUES.has(normalized)
    ? (normalized as OpportunitiesView)
    : DEFAULT_OPPORTUNITIES_VIEW;
}

export function parseOpportunitiesView(
  search: string | undefined = typeof window !== "undefined" ? window.location.search : "",
): OpportunitiesView {
  const params = new URLSearchParams(
    search?.startsWith("?") ? search.slice(1) : search ?? "",
  );
  return normalizeOpportunitiesView(params.get("view"));
}

/** Applies `view` to URLSearchParams; omits param when default (`opportunity`). */
export function applyOpportunitiesViewToSearchParams(
  params: URLSearchParams,
  view: OpportunitiesView,
): void {
  if (view === DEFAULT_OPPORTUNITIES_VIEW) {
    params.delete("view");
  } else {
    params.set("view", view);
  }
}

export function writeOpportunitiesViewToUrl(view: OpportunitiesView): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  applyOpportunitiesViewToSearchParams(url.searchParams, view);
  const next = `${url.pathname}${url.search}${url.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (next === current) return;
  window.history.replaceState(window.history.state, "", next);
}
