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
import {
  parsePeriodPresetId,
  type PeriodPresetId,
} from "./periodPreset";
import {
  applyOpportunitiesViewToSearchParams,
  parseOpportunitiesView,
} from "./opportunitiesViewDeepLink";

export type AnalyticsFilterUrlState = LinkedDateFilters & {
  branches: string[];
  customerSegment: "" | "weg" | "new_business";
  /** Carteiras selecionadas (ids commercial-api); vazio = «Não filtrar» (global TOTVS). */
  sellerIds: string[];
  /** Códigos TOTVS selecionados; vazio = todos os clientes do recorte. */
  customerCodes: string[];
  /** Preset explícito na URL (`period_preset`); null = inferir / custom. */
  periodPreset: PeriodPresetId | null;
};

const SESSION_STORAGE_KEY = "delpi.commercial.analytics.filters";
const ANALYTICS_OPPORTUNITY_BACK_KEYS = [
  "start_date",
  "end_date",
  "competence",
  "branch",
  "customer_segment",
  "seller_id",
  "customer_codes",
  "period_preset",
  "search",
] as const;

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
    sellerIds: [],
    customerCodes: [],
    periodPreset: null,
  };
}

function parseCsvIds(raw: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of raw.split(",")) {
    const id = part.trim();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    out.push(id);
  }
  return out;
}

function parseSellerIdsCsv(raw: string): string[] {
  return parseCsvIds(raw);
}

function serializeSellerIdsCsv(ids: string[]): string {
  return parseCsvIds(ids.join(",")).join(",");
}

function parseCustomerCodesCsv(raw: string): string[] {
  return parseCsvIds(raw);
}

function serializeCustomerCodesCsv(codes: string[]): string {
  return parseCsvIds(codes.join(",")).join(",");
}

function parseStoredSellerIds(data: Record<string, unknown>): string[] {
  if (Array.isArray(data.sellerIds)) {
    return parseSellerIdsCsv(
      data.sellerIds
        .filter((entry): entry is string => typeof entry === "string")
        .join(","),
    );
  }
  if (typeof data.sellerId === "string" && data.sellerId.trim()) {
    return parseSellerIdsCsv(data.sellerId);
  }
  return [];
}

function parseStoredCustomerCodes(data: Record<string, unknown>): string[] {
  if (Array.isArray(data.customerCodes)) {
    return parseCustomerCodesCsv(
      data.customerCodes
        .filter((entry): entry is string => typeof entry === "string")
        .join(","),
    );
  }
  if (typeof data.customerCodes === "string" && data.customerCodes.trim()) {
    return parseCustomerCodesCsv(data.customerCodes);
  }
  return [];
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
  const sellerIdParam = (params.get("seller_id") ?? "").trim();
  const customerCodesParam = (params.get("customer_codes") ?? "").trim();
  const periodPresetParam = params.get("period_preset") ?? "";
  const hasAny =
    isValidIsoDate(dateStartParam) ||
    isValidIsoDate(dateEndParam) ||
    isValidCompetence(competenceParam) ||
    branchParam.length > 0 ||
    customerSegmentParam.length > 0 ||
    sellerIdParam.length > 0 ||
    customerCodesParam.length > 0 ||
    periodPresetParam.length > 0;

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
    sellerIds: parseSellerIdsCsv(sellerIdParam),
    customerCodes: parseCustomerCodesCsv(customerCodesParam),
    periodPreset: parsePeriodPresetId(periodPresetParam),
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
          sellerIds: parseStoredSellerIds(data),
          customerCodes: parseStoredCustomerCodes(data),
          periodPreset: parsePeriodPresetId(
            typeof data.periodPreset === "string" ? data.periodPreset : null,
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
  const sellerIds = serializeSellerIdsCsv(state.sellerIds);
  if (sellerIds) params.set("seller_id", sellerIds);
  const customerCodes = serializeCustomerCodesCsv(state.customerCodes);
  if (customerCodes) params.set("customer_codes", customerCodes);
  if (state.periodPreset && state.periodPreset !== "custom") {
    params.set("period_preset", state.periodPreset);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function buildAnalyticsOpportunityBackSearch(search?: string): string {
  const source = new URLSearchParams(
    search ?? (typeof window !== "undefined" ? window.location.search : ""),
  );
  const target = new URLSearchParams();
  for (const key of ANALYTICS_OPPORTUNITY_BACK_KEYS) {
    const value = (source.get(key) ?? "").trim();
    if (value) target.set(key, value);
  }
  const query = target.toString();
  return query ? `?${query}` : "";
}

export function readAnalyticsOpportunitySearch(
  search = typeof window !== "undefined" ? window.location.search : "",
): string {
  return (new URLSearchParams(search).get("search") ?? "").trim();
}

export function writeAnalyticsOpportunitySearchToUrl(value: string): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  const normalized = value.trim();
  if (normalized) url.searchParams.set("search", normalized);
  else url.searchParams.delete("search");
  window.history.replaceState(
    window.history.state,
    "",
    `${url.pathname}${url.search}${url.hash}`,
  );
}

export function writeAnalyticsFiltersToUrl(state: AnalyticsFilterUrlState): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignora
  }
  const nextParams = new URLSearchParams(buildAnalyticsFilterSearchParams(state));
  const opportunitySearch = readAnalyticsOpportunitySearch(window.location.search);
  if (opportunitySearch) nextParams.set("search", opportunitySearch);
  applyOpportunitiesViewToSearchParams(
    nextParams,
    parseOpportunitiesView(window.location.search),
  );
  const serialized = nextParams.toString();
  const nextSearch = serialized ? `?${serialized}` : "";
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
