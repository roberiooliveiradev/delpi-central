import { getTodayIsoDate } from "../../../utils/dates";
import {
  isValidCompetence,
  resolveLinkedDateFilters,
  type LinkedDateFilters,
} from "./competenceFilters";
import {
  parseAnalyticsBranchCsv,
  serializeAnalyticsBranchCsv,
} from "./analyticsBranchFilters";

export type AnalyticsFilterUrlState = LinkedDateFilters & {
  branches: string[];
  customerSegment: "" | "weg" | "new_business";
};

const SESSION_STORAGE_KEY = "delpi.commercial.analytics.filters";

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function getFirstDayOfMonthInputValue(reference = new Date()): string {
  const year = reference.getFullYear();
  const month = String(reference.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}-01`;
}

function defaultFilterState(): AnalyticsFilterUrlState {
  const defaults = resolveLinkedDateFilters({
    defaultDateStart: getFirstDayOfMonthInputValue(),
    defaultDateEnd: getTodayIsoDate(),
  });
  return {
    ...defaults,
    branches: [],
    customerSegment: "",
  };
}

function parseCustomerSegment(
  value: string | null,
): AnalyticsFilterUrlState["customerSegment"] {
  if (value === "weg" || value === "new_business") return value;
  return "";
}

function parseStoredBranches(data: Record<string, unknown>): string[] {
  if (Array.isArray(data.branches)) {
    return parseAnalyticsBranchCsv(
      data.branches
        .filter((entry): entry is string => typeof entry === "string")
        .join(","),
    );
  }
  if (typeof data.branch === "string" && data.branch.trim()) {
    return parseAnalyticsBranchCsv(data.branch);
  }
  return [];
}

function parseFilterParams(params: URLSearchParams): AnalyticsFilterUrlState | null {
  const dateStartParam = params.get("start_date") ?? "";
  const dateEndParam = params.get("end_date") ?? "";
  const competenceParam = params.get("competence") ?? "";
  const branchParam = params.get("branch") ?? "";
  const customerSegmentParam = params.get("customer_segment") ?? "";
  const hasAny =
    isValidIsoDate(dateStartParam) ||
    isValidIsoDate(dateEndParam) ||
    isValidCompetence(competenceParam) ||
    branchParam.length > 0 ||
    customerSegmentParam.length > 0;

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
    branches: parseAnalyticsBranchCsv(branchParam),
    customerSegment: parseCustomerSegment(customerSegmentParam),
  };
}

export function readAnalyticsFilters(
  search = typeof window !== "undefined" ? window.location.search : "",
): AnalyticsFilterUrlState {
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
          customerSegment: parseCustomerSegment(
            typeof data.customerSegment === "string" ? data.customerSegment : null,
          ),
        };
      }
    } catch {
      // ignora
    }
  }

  return defaultFilterState();
}

export function buildAnalyticsFilterSearchParams(state: AnalyticsFilterUrlState): string {
  const params = new URLSearchParams();
  if (state.dateStart) params.set("start_date", state.dateStart);
  if (state.dateEnd) params.set("end_date", state.dateEnd);
  if (state.competence) params.set("competence", state.competence);
  const branch = serializeAnalyticsBranchCsv(state.branches);
  if (branch) params.set("branch", branch);
  if (state.customerSegment) params.set("customer_segment", state.customerSegment);
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function writeAnalyticsFiltersToUrl(state: AnalyticsFilterUrlState): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignora
  }
  const nextSearch = buildAnalyticsFilterSearchParams(state);
  const nextUrl = `${window.location.pathname}${nextSearch}${window.location.hash}`;
  if (
    `${window.location.pathname}${window.location.search}${window.location.hash}` ===
    nextUrl
  ) {
    return;
  }
  window.history.replaceState(window.history.state, "", nextUrl);
}

export const ANALYTICS_FILTER_ROUTE_SYNC_EVENT = "delpi.commercial.gestao.route-sync";

export function subscribeAnalyticsFilterRouteSync(onSync: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("popstate", onSync);
  window.addEventListener(ANALYTICS_FILTER_ROUTE_SYNC_EVENT, onSync);
  return () => {
    window.removeEventListener("popstate", onSync);
    window.removeEventListener(ANALYTICS_FILTER_ROUTE_SYNC_EVENT, onSync);
  };
}
