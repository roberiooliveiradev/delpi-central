import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "./dates";

export type CommercialFilterUrlState = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  customerSegment: "" | "weg" | "new_business";
};

const SESSION_STORAGE_KEY = "delpi.dashboard-commercial.filters";

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function defaultFilterState(): CommercialFilterUrlState {
  return {
    dateStart: getFirstDayOfMonthInputValue(),
    dateEnd: getTodayInputValue(),
    branch: "",
    customerSegment: "",
  };
}

function parseCustomerSegment(
  value: string | null
): CommercialFilterUrlState["customerSegment"] {
  if (value === "weg" || value === "new_business") {
    return value;
  }
  return "";
}

function parseFilterParams(params: URLSearchParams): CommercialFilterUrlState | null {
  const dateStartParam = params.get("start_date") ?? "";
  const dateEndParam = params.get("end_date") ?? "";
  const branchParam = params.get("branch") ?? "";
  const customerSegmentParam = params.get("customer_segment") ?? "";
  const hasAny =
    isValidIsoDate(dateStartParam) ||
    isValidIsoDate(dateEndParam) ||
    branchParam.length > 0 ||
    customerSegmentParam.length > 0;

  if (!hasAny) return null;

  const defaults = defaultFilterState();

  return {
    dateStart: isValidIsoDate(dateStartParam)
      ? dateStartParam
      : defaults.dateStart,
    dateEnd: isValidIsoDate(dateEndParam) ? dateEndParam : defaults.dateEnd,
    branch: branchParam,
    customerSegment: parseCustomerSegment(customerSegmentParam),
  };
}

export function readCommercialFilters(
  search = typeof window !== "undefined" ? window.location.search : ""
): CommercialFilterUrlState {
  const fromUrl = parseFilterParams(new URLSearchParams(search));
  if (fromUrl) return fromUrl;

  if (typeof window !== "undefined") {
    try {
      const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw) as Partial<CommercialFilterUrlState>;
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
          branch: typeof data.branch === "string" ? data.branch : "",
          customerSegment: parseCustomerSegment(
            typeof data.customerSegment === "string" ? data.customerSegment : null
          ),
        };
      }
    } catch {
      // ignora
    }
  }

  return defaultFilterState();
}

export function buildFilterSearchParams(state: CommercialFilterUrlState): string {
  const params = new URLSearchParams();

  if (state.dateStart) params.set("start_date", state.dateStart);
  if (state.dateEnd) params.set("end_date", state.dateEnd);
  if (state.branch) params.set("branch", state.branch);
  if (state.customerSegment) {
    params.set("customer_segment", state.customerSegment);
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

export function writeFiltersToUrl(state: CommercialFilterUrlState): void {
  if (typeof window === "undefined") return;

  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignora
  }

  const nextSearch = buildFilterSearchParams(state);
  const nextUrl = `${window.location.pathname}${nextSearch}${window.location.hash}`;

  if (`${window.location.pathname}${window.location.search}${window.location.hash}` === nextUrl) {
    return;
  }

  window.history.replaceState(window.history.state, "", nextUrl);
}

export function appendFiltersToPath(
  path: string,
  state: CommercialFilterUrlState
): string {
  return `${path}${buildFilterSearchParams(state)}`;
}
