import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "./dates";

export type QualityFilterUrlState = {
  dateStart: string;
  dateEnd: string;
  branch: string;
};

const FILTER_KEYS = ["date_start", "date_end", "branch"] as const;

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

export function readFiltersFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): QualityFilterUrlState {
  const params = new URLSearchParams(search);

  const dateStartParam = params.get("date_start") ?? "";
  const dateEndParam = params.get("date_end") ?? "";
  const branchParam = params.get("branch") ?? "";

  return {
    dateStart: isValidIsoDate(dateStartParam)
      ? dateStartParam
      : getFirstDayOfMonthInputValue(),
    dateEnd: isValidIsoDate(dateEndParam) ? dateEndParam : getTodayInputValue(),
    branch: branchParam,
  };
}

export function buildFilterSearchParams(state: QualityFilterUrlState): string {
  const params = new URLSearchParams();

  if (state.dateStart) {
    params.set("date_start", state.dateStart);
  }

  if (state.dateEnd) {
    params.set("date_end", state.dateEnd);
  }

  if (state.branch) {
    params.set("branch", state.branch);
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function writeFiltersToUrl(state: QualityFilterUrlState): void {
  if (typeof window === "undefined") return;

  const nextSearch = buildFilterSearchParams(state);
  const nextUrl = `${window.location.pathname}${nextSearch}${window.location.hash}`;

  if (`${window.location.pathname}${window.location.search}${window.location.hash}` === nextUrl) {
    return;
  }

  window.history.replaceState(window.history.state, "", nextUrl);
}

export function appendFiltersToPath(
  path: string,
  state: QualityFilterUrlState
): string {
  const query = buildFilterSearchParams(state);
  return `${path}${query}`;
}

export { FILTER_KEYS };
