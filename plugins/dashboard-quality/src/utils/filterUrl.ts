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
const SESSION_STORAGE_KEY = "delpi.dashboard-quality.filters";

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function defaultFilterState(): QualityFilterUrlState {
  return {
    dateStart: getFirstDayOfMonthInputValue(),
    dateEnd: getTodayInputValue(),
    branch: "",
  };
}

function parseFilterParams(params: URLSearchParams): QualityFilterUrlState | null {
  const dateStartParam = params.get("date_start") ?? "";
  const dateEndParam = params.get("date_end") ?? "";
  const branchParam = params.get("branch") ?? "";
  const hasAny =
    isValidIsoDate(dateStartParam) ||
    isValidIsoDate(dateEndParam) ||
    branchParam.length > 0;

  if (!hasAny) return null;

  const defaults = defaultFilterState();

  return {
    dateStart: isValidIsoDate(dateStartParam)
      ? dateStartParam
      : defaults.dateStart,
    dateEnd: isValidIsoDate(dateEndParam) ? dateEndParam : defaults.dateEnd,
    branch: branchParam,
  };
}

export function readFiltersFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): QualityFilterUrlState {
  const parsed = parseFilterParams(new URLSearchParams(search));
  return parsed ?? defaultFilterState();
}

export function readFiltersFromSession(): QualityFilterUrlState | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;

    const data = JSON.parse(raw) as Partial<QualityFilterUrlState>;
    const dateStart =
      typeof data.dateStart === "string" && isValidIsoDate(data.dateStart)
        ? data.dateStart
        : "";
    const dateEnd =
      typeof data.dateEnd === "string" && isValidIsoDate(data.dateEnd)
        ? data.dateEnd
        : "";
    const branch = typeof data.branch === "string" ? data.branch : "";

    if (!dateStart && !dateEnd && !branch) return null;

    const defaults = defaultFilterState();

    return {
      dateStart: dateStart || defaults.dateStart,
      dateEnd: dateEnd || defaults.dateEnd,
      branch,
    };
  } catch {
    return null;
  }
}

/** URL tem prioridade; sessionStorage mantém o período ao trocar de aba no portal. */
export function readQualityFilters(
  search = typeof window !== "undefined" ? window.location.search : ""
): QualityFilterUrlState {
  const fromUrl = parseFilterParams(new URLSearchParams(search));
  if (fromUrl) return fromUrl;

  return readFiltersFromSession() ?? defaultFilterState();
}

export function persistFiltersToSession(state: QualityFilterUrlState): void {
  if (typeof window === "undefined") return;

  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // quota ou modo privado — ignora
  }
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

  persistFiltersToSession(state);

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
