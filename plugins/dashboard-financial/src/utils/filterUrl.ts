import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "./dates";
import {
  parseBranchCsv,
  serializeBranchCsv,
} from "./branchClientFilters";

export type FinancialFilterUrlState = {
  dateStart: string;
  dateEnd: string;
  branches: string[];
};

const SESSION_STORAGE_KEY = "delpi.dashboard-financial.filters";

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function defaultFilterState(): FinancialFilterUrlState {
  return {
    dateStart: getFirstDayOfMonthInputValue(),
    dateEnd: getTodayInputValue(),
    branches: [],
  };
}

function parseStoredBranches(data: Record<string, unknown>): string[] {
  if (Array.isArray(data.branches)) {
    return parseBranchCsv(
      data.branches
        .filter((entry): entry is string => typeof entry === "string")
        .join(",")
    );
  }

  if (typeof data.branch === "string" && data.branch.trim()) {
    return parseBranchCsv(data.branch);
  }

  return [];
}

function parseFilterParams(
  params: URLSearchParams
): FinancialFilterUrlState | null {
  const dateStartParam = params.get("start_date") ?? "";
  const dateEndParam = params.get("end_date") ?? "";
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
    branches: parseBranchCsv(branchParam),
  };
}

export function readFinancialFilters(
  search = typeof window !== "undefined" ? window.location.search : ""
): FinancialFilterUrlState {
  const fromUrl = parseFilterParams(new URLSearchParams(search));
  if (fromUrl) return fromUrl;

  if (typeof window !== "undefined") {
    try {
      const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw) as Partial<FinancialFilterUrlState> &
          Record<string, unknown>;
        const defaults = defaultFilterState();
        return {
          dateStart:
            data.dateStart && isValidIsoDate(data.dateStart)
              ? data.dateStart
              : defaults.dateStart,
          dateEnd:
            data.dateEnd && isValidIsoDate(data.dateEnd)
              ? data.dateEnd
              : defaults.dateEnd,
          branches: parseStoredBranches(data),
        };
      }
    } catch {
      // ignora
    }
  }

  return defaultFilterState();
}

export function buildFilterSearchParams(state: FinancialFilterUrlState): string {
  const params = new URLSearchParams();

  if (state.dateStart) params.set("start_date", state.dateStart);
  if (state.dateEnd) params.set("end_date", state.dateEnd);
  const branchCsv = serializeBranchCsv(state.branches);
  if (branchCsv) params.set("branch", branchCsv);

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function writeFiltersToUrl(state: FinancialFilterUrlState): void {
  if (typeof window === "undefined") return;

  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignora
  }

  const nextSearch = buildFilterSearchParams(state);
  const nextUrl = `${window.location.pathname}${nextSearch}${window.location.hash}`;

  if (
    `${window.location.pathname}${window.location.search}${window.location.hash}` ===
    nextUrl
  ) {
    return;
  }

  window.history.replaceState(window.history.state, "", nextUrl);
}

export function appendFiltersToPath(
  path: string,
  state?: FinancialFilterUrlState
): string {
  const filters = state ?? readFinancialFilters();
  return `${path}${buildFilterSearchParams(filters)}`;
}

export function readFiltersFromUrl(search: string): FinancialFilterUrlState {
  return parseFilterParams(new URLSearchParams(search)) ?? defaultFilterState();
}
