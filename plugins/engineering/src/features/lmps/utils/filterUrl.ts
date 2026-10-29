import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
} from "./dates";
import { isValidCompetence, resolveLinkedDateFilters } from "./competenceFilters";

export type LmpsFilterUrlState = {
  dateStart: string;
  dateEnd: string;
  competence: string;
  branches: string[];
  listingTypes: string[];
  statuses: string[];
};

function isValidIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function parseCsvParam(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function serializeCsvParam(values: string[]): string {
  return values.map((value) => value.trim()).filter(Boolean).join(",");
}

export function defaultLmpsFilterState(): LmpsFilterUrlState {
  const dates = resolveLinkedDateFilters({
    defaultDateStart: getFirstDayOfMonthInputValue(),
    defaultDateEnd: getTodayInputValue(),
  });

  return {
    ...dates,
    branches: [],
    listingTypes: [],
    statuses: [],
  };
}

function parseFilterParams(params: URLSearchParams): LmpsFilterUrlState | null {
  const dateStartParam = params.get("start_date") ?? params.get("date_start") ?? "";
  const dateEndParam = params.get("end_date") ?? params.get("date_end") ?? "";
  const competenceParam = params.get("competence") ?? "";
  const branchParam = params.get("branch") ?? "";
  const listingTypeParam = params.get("listing_type") ?? "";
  const statusParam = params.get("status") ?? "";
  const hasAny =
    isValidIsoDate(dateStartParam) ||
    isValidIsoDate(dateEndParam) ||
    isValidCompetence(competenceParam) ||
    branchParam.length > 0 ||
    listingTypeParam.length > 0 ||
    statusParam.length > 0;

  if (!hasAny) return null;

  const defaults = defaultLmpsFilterState();
  const dates = resolveLinkedDateFilters({
    dateStart: isValidIsoDate(dateStartParam) ? dateStartParam : defaults.dateStart,
    dateEnd: isValidIsoDate(dateEndParam) ? dateEndParam : defaults.dateEnd,
    competence: isValidCompetence(competenceParam) ? competenceParam : "",
    defaultDateStart: getFirstDayOfMonthInputValue(),
    defaultDateEnd: getTodayInputValue(),
  });

  return {
    ...dates,
    branches: parseCsvParam(branchParam),
    listingTypes: parseCsvParam(listingTypeParam),
    statuses: parseCsvParam(statusParam),
  };
}

export function readLmpsFilters(
  search = typeof window !== "undefined" ? window.location.search : ""
): LmpsFilterUrlState {
  return parseFilterParams(new URLSearchParams(search)) ?? defaultLmpsFilterState();
}

export function buildFilterSearchParams(filters: LmpsFilterUrlState): string {
  const params = new URLSearchParams();

  if (filters.dateStart) params.set("start_date", filters.dateStart);
  if (filters.dateEnd) params.set("end_date", filters.dateEnd);
  if (filters.competence) params.set("competence", filters.competence);

  const branch = serializeCsvParam(filters.branches);
  if (branch) params.set("branch", branch);

  const listingType = serializeCsvParam(filters.listingTypes);
  if (listingType) params.set("listing_type", listingType);

  const status = serializeCsvParam(filters.statuses);
  if (status) params.set("status", status);

  const query = params.toString();
  return query ? `?${query}` : "";
}

/** Atualiza a query string da URL atual sem empilhar histórico (filtros do dashboard). */
export function syncLmpsFiltersToUrl(filters: LmpsFilterUrlState): void {
  if (typeof window === "undefined") return;

  const query = buildFilterSearchParams(filters);
  const target = `${window.location.pathname}${query}`;

  if (`${window.location.pathname}${window.location.search}` === target) {
    return;
  }

  window.history.replaceState(window.history.state, "", target);
}

export function appendFiltersToPath(
  path: string,
  filters?: LmpsFilterUrlState
): string {
  if (!filters) return path;
  const query = buildFilterSearchParams(filters);
  return `${path}${query}`;
}

export function toLmpApiDate(value?: string): string | undefined {
  if (!value) return undefined;
  const normalized = value.trim();
  if (/^\d{8}$/.test(normalized)) return normalized;
  if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    return normalized.replaceAll("-", "");
  }
  return normalized;
}

/** Primeira filial selecionada (compatível com detalhe da OV). */
export function resolveLmpsBranchFilter(filters: LmpsFilterUrlState): string | undefined {
  return filters.branches[0] || undefined;
}
