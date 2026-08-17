/**
 * Estado da lista OTD na URL (busca, status, sort, página) —
 * separado dos filtros de período/unidade/carteira.
 */

export type OtdListStatusFilter = "" | "on_time" | "late";

export type OtdListSortKey =
  | "branch"
  | "status"
  | "order_number"
  | "customer_name"
  | "product_code"
  | "promised_date"
  | "invoice_date"
  | "days_diff"
  | "qty_sold";

export type OtdListUrlState = {
  search: string;
  status: OtdListStatusFilter;
  sortBy: OtdListSortKey | null;
  sortDir: "asc" | "desc";
  page: number;
};

const SORT_KEYS = new Set<string>([
  "branch",
  "status",
  "order_number",
  "customer_name",
  "product_code",
  "promised_date",
  "invoice_date",
  "days_diff",
  "qty_sold",
]);

const DEFAULT_STATE: OtdListUrlState = {
  search: "",
  status: "",
  sortBy: null,
  sortDir: "asc",
  page: 1,
};

function isIsoSafePage(value: number): boolean {
  return Number.isSafeInteger(value) && value > 0;
}

export function parseOtdListUrlState(
  search = typeof window !== "undefined" ? window.location.search : "",
): OtdListUrlState {
  const params = new URLSearchParams(search);
  const statusRaw = (params.get("otd_status") ?? "").trim().toLowerCase();
  const status: OtdListStatusFilter =
    statusRaw === "on_time" || statusRaw === "late" ? statusRaw : "";
  const sortRaw = (params.get("otd_sort") ?? "").trim().toLowerCase();
  const sortBy = SORT_KEYS.has(sortRaw) ? (sortRaw as OtdListSortKey) : null;
  const dirRaw = (params.get("otd_dir") ?? "").trim().toLowerCase();
  const pageValue = Number(params.get("otd_page"));
  return {
    search: (params.get("otd_q") ?? "").trim(),
    status,
    sortBy,
    sortDir: dirRaw === "desc" ? "desc" : "asc",
    page: isIsoSafePage(pageValue) ? pageValue : 1,
  };
}

export function writeOtdListUrlState(state: OtdListUrlState): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  const params = url.searchParams;
  if (state.search.trim()) params.set("otd_q", state.search.trim());
  else params.delete("otd_q");
  if (state.status) params.set("otd_status", state.status);
  else params.delete("otd_status");
  if (state.sortBy) {
    params.set("otd_sort", state.sortBy);
    params.set("otd_dir", state.sortDir);
  } else {
    params.delete("otd_sort");
    params.delete("otd_dir");
  }
  if (state.page > 1) params.set("otd_page", String(state.page));
  else params.delete("otd_page");
  const next = `${url.pathname}${params.toString() ? `?${params}` : ""}${url.hash}`;
  window.history.replaceState(window.history.state, "", next);
}

export function defaultOtdListUrlState(): OtdListUrlState {
  return { ...DEFAULT_STATE };
}
