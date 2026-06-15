import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "./dates";

export type LmpsFilterUrlState = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  listingType: string;
  status: string;
};

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

export function defaultLmpsFilterState(): LmpsFilterUrlState {
  return {
    dateStart: getFirstDayOfMonthInputValue(),
    dateEnd: getTodayInputValue(),
    branch: "",
    listingType: "Todos",
    status: "Todos",
  };
}

function parseFilterParams(params: URLSearchParams): LmpsFilterUrlState | null {
  const dateStartParam = params.get("date_start") ?? "";
  const dateEndParam = params.get("date_end") ?? "";
  const branchParam = params.get("branch") ?? "";
  const listingTypeParam = params.get("listing_type") ?? "";
  const statusParam = params.get("status") ?? "";
  const hasAny =
    isValidIsoDate(dateStartParam) ||
    isValidIsoDate(dateEndParam) ||
    branchParam.length > 0 ||
    listingTypeParam.length > 0 ||
    statusParam.length > 0;

  if (!hasAny) return null;

  const defaults = defaultLmpsFilterState();

  return {
    dateStart: isValidIsoDate(dateStartParam)
      ? dateStartParam
      : defaults.dateStart,
    dateEnd: isValidIsoDate(dateEndParam) ? dateEndParam : defaults.dateEnd,
    branch: branchParam,
    listingType: listingTypeParam || defaults.listingType,
    status: statusParam || defaults.status,
  };
}

export function readLmpsFilters(
  search = typeof window !== "undefined" ? window.location.search : ""
): LmpsFilterUrlState {
  return parseFilterParams(new URLSearchParams(search)) ?? defaultLmpsFilterState();
}

export function buildFilterSearchParams(filters: LmpsFilterUrlState): string {
  const params = new URLSearchParams();

  if (filters.dateStart) params.set("date_start", filters.dateStart);
  if (filters.dateEnd) params.set("date_end", filters.dateEnd);
  if (filters.branch) params.set("branch", filters.branch);
  if (filters.listingType && filters.listingType !== "Todos") {
    params.set("listing_type", filters.listingType);
  }
  if (filters.status && filters.status !== "Todos") {
    params.set("status", filters.status);
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function appendFiltersToPath(
  path: string,
  filters?: LmpsFilterUrlState
): string {
  if (!filters) return path;
  return `${path}${buildFilterSearchParams(filters)}`;
}

export function toLmpApiDate(value?: string): string | undefined {
  if (!value) return undefined;
  const normalized = value.trim();
  if (/^\d{8}$/.test(normalized)) return normalized;
  if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    return normalized.replaceAll("-", "");
  }
  return normalized;
}
