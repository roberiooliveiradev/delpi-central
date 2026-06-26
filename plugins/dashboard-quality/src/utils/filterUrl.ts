import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "./dates";
import { isValidCompetence, resolveLinkedDateFilters } from "./competenceFilters";
import {
  parseDynamicBranchCsv,
  serializeDynamicBranchCsv,
} from "./branchClientFilters";

export type QualityFilterUrlState = {
  dateStart: string;
  dateEnd: string;
  competence: string;
  branches: string[];
};

const FILTER_KEYS = ["date_start", "date_end", "competence", "branch"] as const;
const SESSION_STORAGE_KEY = "delpi.dashboard-quality.filters";

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function defaultFilterState(): QualityFilterUrlState {
  const defaults = resolveLinkedDateFilters({
    defaultDateStart: getFirstDayOfMonthInputValue(),
    defaultDateEnd: getTodayInputValue(),
  });

  return {
    ...defaults,
    branches: [],
  };
}

function parseStoredBranches(data: Record<string, unknown>): string[] {
  if (Array.isArray(data.branches)) {
    return parseDynamicBranchCsv(
      data.branches
        .filter((entry): entry is string => typeof entry === "string")
        .join(",")
    );
  }

  if (typeof data.branch === "string" && data.branch.trim()) {
    return parseDynamicBranchCsv(data.branch);
  }

  return [];
}

function parseFilterParams(params: URLSearchParams): QualityFilterUrlState | null {
  const dateStartParam = params.get("date_start") ?? "";
  const dateEndParam = params.get("date_end") ?? "";
  const competenceParam = params.get("competence") ?? "";
  const branchParam = params.get("branch") ?? "";
  const hasAny =
    isValidIsoDate(dateStartParam) ||
    isValidIsoDate(dateEndParam) ||
    isValidCompetence(competenceParam) ||
    branchParam.length > 0;

  if (!hasAny) return null;

  const defaults = defaultFilterState();
  const dates = resolveLinkedDateFilters({
    dateStart: isValidIsoDate(dateStartParam)
      ? dateStartParam
      : defaults.dateStart,
    dateEnd: isValidIsoDate(dateEndParam) ? dateEndParam : defaults.dateEnd,
    competence: isValidCompetence(competenceParam) ? competenceParam : "",
    defaultDateStart: defaults.dateStart,
    defaultDateEnd: defaults.dateEnd,
  });

  return {
    ...dates,
    branches: parseDynamicBranchCsv(branchParam),
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

    const data = JSON.parse(raw) as Record<string, unknown>;
    const defaults = defaultFilterState();
    const dates = resolveLinkedDateFilters({
      dateStart:
        typeof data.dateStart === "string" && isValidIsoDate(data.dateStart)
          ? data.dateStart
          : defaults.dateStart,
      dateEnd:
        typeof data.dateEnd === "string" && isValidIsoDate(data.dateEnd)
          ? data.dateEnd
          : defaults.dateEnd,
      competence:
        typeof data.competence === "string" && isValidCompetence(data.competence)
          ? data.competence
          : "",
      defaultDateStart: defaults.dateStart,
      defaultDateEnd: defaults.dateEnd,
    });
    const branches = parseStoredBranches(data);

    if (
      !dates.dateStart &&
      !dates.dateEnd &&
      !dates.competence &&
      branches.length === 0
    ) {
      return null;
    }

    return {
      ...dates,
      branches,
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

  if (state.competence) {
    params.set("competence", state.competence);
  }

  const branchCsv = serializeDynamicBranchCsv(state.branches);
  if (branchCsv) {
    params.set("branch", branchCsv);
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

export const FILTER_ROUTE_SYNC_EVENT = "delpi.dashboard-quality.route-sync";

export function dispatchFilterRouteSync(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(FILTER_ROUTE_SYNC_EVENT));
}

export function subscribeFilterRouteSync(onSync: () => void): () => void {
  if (typeof window === "undefined") return () => {};

  window.addEventListener("popstate", onSync);
  window.addEventListener(FILTER_ROUTE_SYNC_EVENT, onSync);

  return () => {
    window.removeEventListener("popstate", onSync);
    window.removeEventListener(FILTER_ROUTE_SYNC_EVENT, onSync);
  };
}

export { FILTER_KEYS };
