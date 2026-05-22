import {
  getCurrentStrategicIndicatorsMonthValue,
  getDefaultMonthsToCompare,
  type StrategicIndicatorsViewMode,
} from "./strategicIndicatorsFilters";

export type StrategicIndicatorsFilterState = {
  referenceMonth: string;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  monthsToCompare: number;
};

const SESSION_STORAGE_KEY = "delpi.strategic-indicators.filters";
const VALID_MONTHS = new Set([2, 3, 4, 6, 12]);
const VALID_BRANCHES = new Set(["01", "02"]);

function defaultFilterState(): StrategicIndicatorsFilterState {
  return {
    referenceMonth: getCurrentStrategicIndicatorsMonthValue(),
    viewMode: "consolidated",
    branch: "01",
    monthsToCompare: getDefaultMonthsToCompare(),
  };
}

function isValidReferenceMonth(value: string): boolean {
  return /^\d{4}-\d{2}$/.test(value);
}

function isValidViewMode(value: string): value is StrategicIndicatorsViewMode {
  return value === "consolidated" || value === "branch";
}

function parseMonths(value: string | null): number | null {
  if (!value) return null;
  const parsed = Number(value);
  return VALID_MONTHS.has(parsed) ? parsed : null;
}

function parseFilterParams(
  params: URLSearchParams
): StrategicIndicatorsFilterState | null {
  const competence = params.get("competence") ?? "";
  const view = params.get("view") ?? "";
  const branch = params.get("branch") ?? "";
  const months = params.get("months");

  const hasAny =
    isValidReferenceMonth(competence) ||
    isValidViewMode(view) ||
    VALID_BRANCHES.has(branch) ||
    parseMonths(months) !== null;

  if (!hasAny) return null;

  const defaults = defaultFilterState();

  return {
    referenceMonth: isValidReferenceMonth(competence)
      ? competence
      : defaults.referenceMonth,
    viewMode: isValidViewMode(view) ? view : defaults.viewMode,
    branch: VALID_BRANCHES.has(branch) ? branch : defaults.branch,
    monthsToCompare: parseMonths(months) ?? defaults.monthsToCompare,
  };
}

export function readStrategicIndicatorsFilters(
  search = typeof window !== "undefined" ? window.location.search : ""
): StrategicIndicatorsFilterState {
  const fromUrl = parseFilterParams(new URLSearchParams(search));
  if (fromUrl) return fromUrl;

  if (typeof window === "undefined") return defaultFilterState();

  try {
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return defaultFilterState();

    const data = JSON.parse(raw) as Partial<StrategicIndicatorsFilterState>;
    const defaults = defaultFilterState();

    const referenceMonth =
      typeof data.referenceMonth === "string" &&
      isValidReferenceMonth(data.referenceMonth)
        ? data.referenceMonth
        : defaults.referenceMonth;

    const viewMode =
      typeof data.viewMode === "string" && isValidViewMode(data.viewMode)
        ? data.viewMode
        : defaults.viewMode;

    const branch =
      typeof data.branch === "string" && VALID_BRANCHES.has(data.branch)
        ? data.branch
        : defaults.branch;

    const monthsToCompare =
      typeof data.monthsToCompare === "number" &&
      VALID_MONTHS.has(data.monthsToCompare)
        ? data.monthsToCompare
        : defaults.monthsToCompare;

    return { referenceMonth, viewMode, branch, monthsToCompare };
  } catch {
    return defaultFilterState();
  }
}

export function persistStrategicIndicatorsFilters(
  state: StrategicIndicatorsFilterState
): void {
  if (typeof window === "undefined") return;

  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // quota ou modo privado
  }
}

export function buildStrategicIndicatorsFilterSearchParams(
  state: StrategicIndicatorsFilterState
): string {
  const params = new URLSearchParams();

  if (state.referenceMonth) {
    params.set("competence", state.referenceMonth);
  }

  if (state.viewMode && state.viewMode !== "consolidated") {
    params.set("view", state.viewMode);
  }

  if (state.viewMode === "branch" && state.branch) {
    params.set("branch", state.branch);
  }

  const defaultMonths = getDefaultMonthsToCompare(
    typeof window !== "undefined" ? window.location.pathname : "",
  );

  if (state.monthsToCompare !== defaultMonths) {
    params.set("months", String(state.monthsToCompare));
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function writeStrategicIndicatorsFiltersToUrl(
  state: StrategicIndicatorsFilterState
): void {
  if (typeof window === "undefined") return;

  persistStrategicIndicatorsFilters(state);

  const nextSearch = buildStrategicIndicatorsFilterSearchParams(state);
  const nextUrl = `${window.location.pathname}${nextSearch}${window.location.hash}`;

  if (
    `${window.location.pathname}${window.location.search}${window.location.hash}` ===
    nextUrl
  ) {
    return;
  }

  window.history.replaceState(window.history.state, "", nextUrl);
}

export function appendStrategicIndicatorsFiltersToPath(
  path: string,
  state?: StrategicIndicatorsFilterState
): string {
  const filters = state ?? readStrategicIndicatorsFilters();
  const query = buildStrategicIndicatorsFilterSearchParams(filters);
  return `${path}${query}`;
}
