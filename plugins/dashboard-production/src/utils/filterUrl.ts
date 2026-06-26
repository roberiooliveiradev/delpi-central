import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "./dates";
import { isValidCompetence, resolveLinkedDateFilters } from "./competenceFilters";
import {
  parseBranchCsv,
  serializeBranchCsv,
} from "./branchClientFilters";

export type ProductionFilterUrlState = {
  dateStart: string;
  dateEnd: string;
  competence: string;
  branches: string[];
};

const SESSION_STORAGE_KEY = "delpi.dashboard-production.filters";

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function defaultFilterState(): ProductionFilterUrlState {
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
): ProductionFilterUrlState | null {
  const dateStartParam = params.get("start_date") ?? "";
  const dateEndParam = params.get("end_date") ?? "";
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
    dateStart: isValidIsoDate(dateStartParam) ? dateStartParam : defaults.dateStart,
    dateEnd: isValidIsoDate(dateEndParam) ? dateEndParam : defaults.dateEnd,
    competence: isValidCompetence(competenceParam) ? competenceParam : "",
    defaultDateStart: defaults.dateStart,
    defaultDateEnd: defaults.dateEnd,
  });

  return {
    ...dates,
    branches: parseBranchCsv(branchParam),
  };
}

export function readProductionFilters(
  search = typeof window !== "undefined" ? window.location.search : ""
): ProductionFilterUrlState {
  const fromUrl = parseFilterParams(new URLSearchParams(search));
  if (fromUrl) return fromUrl;

  if (typeof window !== "undefined") {
    try {
      const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (raw) {
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

        return {
          ...dates,
          branches: parseStoredBranches(data),
        };
      }
    } catch {
      // ignora
    }
  }

  return defaultFilterState();
}

export function buildFilterSearchParams(state: ProductionFilterUrlState): string {
  const params = new URLSearchParams();

  if (state.dateStart) params.set("start_date", state.dateStart);
  if (state.dateEnd) params.set("end_date", state.dateEnd);
  if (state.competence) params.set("competence", state.competence);
  const branchCsv = serializeBranchCsv(state.branches);
  if (branchCsv) params.set("branch", branchCsv);

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function writeFiltersToUrl(state: ProductionFilterUrlState): void {
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
  state?: ProductionFilterUrlState
): string {
  const filters = state ?? readProductionFilters();
  return `${path}${buildFilterSearchParams(filters)}`;
}

export function readFiltersFromUrl(search: string): ProductionFilterUrlState {
  return parseFilterParams(new URLSearchParams(search)) ?? defaultFilterState();
}

export const FILTER_ROUTE_SYNC_EVENT = "delpi.dashboard-production.route-sync";

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
