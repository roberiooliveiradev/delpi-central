import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "./dates";
import { isValidCompetence, resolveLinkedDateFilters } from "./competenceFilters";
import {
  parseBranchCsv,
  serializeBranchCsv,
} from "./branchClientFilters";

export type SuppliesFilterUrlState = {
  dateStart: string;
  dateEnd: string;
  competence: string;
  branches: string[];
  location: string;
};

/**
 * Per-page initial period used only when no URL/session filter exists.
 * `competence` takes precedence over the dates (same rule as
 * `resolveLinkedDateFilters`).
 */
export type SuppliesFilterDefaults = {
  dateStart?: string;
  dateEnd?: string;
  competence?: string;
};

const SESSION_STORAGE_KEY = "delpi.dashboard-supplies.filters";

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function defaultFilterState(
  periodDefaults?: SuppliesFilterDefaults
): SuppliesFilterUrlState {
  const defaults = resolveLinkedDateFilters({
    dateStart: periodDefaults?.dateStart,
    dateEnd: periodDefaults?.dateEnd,
    competence: periodDefaults?.competence,
    defaultDateStart:
      periodDefaults?.dateStart ?? getFirstDayOfMonthInputValue(),
    defaultDateEnd:
      periodDefaults?.dateEnd ?? getTodayInputValue(),
  });

  return {
    ...defaults,
    branches: [],
    location: "",
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
  params: URLSearchParams,
  periodDefaults?: SuppliesFilterDefaults
): SuppliesFilterUrlState | null {
  const dateStartParam = params.get("start_date") ?? "";
  const dateEndParam = params.get("end_date") ?? "";
  const competenceParam = params.get("competence") ?? "";
  const branchParam = params.get("branch") ?? "";
  const locationParam = params.get("location") ?? "";
  const hasAny =
    isValidIsoDate(dateStartParam) ||
    isValidIsoDate(dateEndParam) ||
    isValidCompetence(competenceParam) ||
    branchParam.length > 0 ||
    locationParam.length > 0;

  if (!hasAny) return null;

  const defaults = defaultFilterState(periodDefaults);
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
    branches: parseBranchCsv(branchParam),
    location: locationParam,
  };
}

export function readSuppliesFilters(
  search = typeof window !== "undefined" ? window.location.search : "",
  periodDefaults?: SuppliesFilterDefaults
): SuppliesFilterUrlState {
  const fromUrl = parseFilterParams(
    new URLSearchParams(search),
    periodDefaults
  );
  if (fromUrl) return fromUrl;

  if (typeof window !== "undefined") {
    try {
      const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw) as Record<string, unknown>;
        const defaults = defaultFilterState(periodDefaults);
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
          location: typeof data.location === "string" ? data.location : "",
        };
      }
    } catch {
      // ignora
    }
  }

  return defaultFilterState(periodDefaults);
}

export function buildFilterSearchParams(state: SuppliesFilterUrlState): string {
  const params = new URLSearchParams();

  if (state.dateStart) params.set("start_date", state.dateStart);
  if (state.dateEnd) params.set("end_date", state.dateEnd);
  if (state.competence) params.set("competence", state.competence);
  const branchCsv = serializeBranchCsv(state.branches);
  if (branchCsv) params.set("branch", branchCsv);
  if (state.location) params.set("location", state.location);

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function writeFiltersToUrl(state: SuppliesFilterUrlState): void {
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
  state?: SuppliesFilterUrlState
): string {
  const filters = state ?? readSuppliesFilters();
  return `${path}${buildFilterSearchParams(filters)}`;
}

export function readFiltersFromUrl(search: string): SuppliesFilterUrlState {
  return parseFilterParams(new URLSearchParams(search)) ?? defaultFilterState();
}

export const FILTER_ROUTE_SYNC_EVENT = "delpi.dashboard-supplies.route-sync";

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
