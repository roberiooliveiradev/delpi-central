import {
  BRANCH_STORAGE_KEY,
  DEFAULT_BRANCH,
  DEFAULT_SUBPLUGIN,
  FINANCIAL_BASE_PATH,
} from "../constants/routes";
import type { FinancialBranch } from "../types";

export type FinancialRoute = {
  subpluginId: string;
  branch: FinancialBranch;
  startDate: string | null;
  endDate: string | null;
  search: string | null;
  costCenter: string | null;
  supplierCode: string | null;
  supplierStore: string | null;
  customerCode: string | null;
  customerStore: string | null;
  clientKey: string | null;
  status: string | null;
  delayRange: string | null;
  granularity: string | null;
  excludeMp: boolean;
  /** Mês em foco no detalhamento de despesas (`AAAA-MM`). */
  month: string | null;
  page: number;
  pathname: string;
};

/** Situação do título aceita na URL — espelha o contrato do BFF. */
const TITLE_STATUSES = new Set(["all", "on_time", "late"]);
const GRANULARITIES = new Set(["day", "week", "month", "year"]);

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const YEAR_MONTH = /^\d{4}-(0[1-9]|1[0-2])$/;

export function isBranch(value: string | null): value is FinancialBranch {
  return value === "01" || value === "02" || value === "all";
}

export function readStoredBranch(): FinancialBranch {
  if (typeof window === "undefined") return DEFAULT_BRANCH;
  const stored = window.sessionStorage.getItem(BRANCH_STORAGE_KEY);
  return isBranch(stored) ? stored : DEFAULT_BRANCH;
}

export function storeBranch(branch: FinancialBranch) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(BRANCH_STORAGE_KEY, branch);
}

function isoDateOrNull(value: string | null): string | null {
  const text = value?.trim() ?? "";
  return ISO_DATE.test(text) ? text : null;
}

function yearMonthOrNull(value: string | null): string | null {
  const text = value?.trim() ?? "";
  return YEAR_MONTH.test(text) ? text : null;
}

function positiveIntOrOne(value: string | null): number {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

function parseBooleanFlag(value: string | null): boolean {
  const text = value?.trim().toLowerCase() ?? "";
  return text === "1" || text === "true" || text === "yes";
}

export function parseFinancialPath(
  pathname: string,
  search = "",
  storedBranch: FinancialBranch = DEFAULT_BRANCH,
): FinancialRoute {
  const path = pathname.replace(/\/+$/, "") || "/";
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const rest = path.startsWith(FINANCIAL_BASE_PATH)
    ? path.slice(FINANCIAL_BASE_PATH.length)
    : path;
  const segment = rest.replace(/^\/+/, "").split("/")[0] || DEFAULT_SUBPLUGIN;
  const branchRaw = params.get("branch");
  const statusRaw = params.get("status")?.trim() || "";
  const granularityRaw = params.get("granularity")?.trim().toLowerCase() || "";

  return {
    subpluginId: segment || DEFAULT_SUBPLUGIN,
    branch: isBranch(branchRaw) ? branchRaw : storedBranch,
    startDate: isoDateOrNull(params.get("startDate")),
    endDate: isoDateOrNull(params.get("endDate")),
    search: params.get("q")?.trim() || null,
    costCenter: params.get("costCenter")?.trim() || null,
    supplierCode: params.get("supplier")?.trim() || null,
    supplierStore: params.get("supplierStore")?.trim() || null,
    customerCode: params.get("customer")?.trim() || null,
    customerStore: params.get("customerStore")?.trim() || null,
    clientKey: params.get("client")?.trim() || null,
    status: TITLE_STATUSES.has(statusRaw) ? statusRaw : null,
    delayRange: params.get("delayRange")?.trim() || null,
    granularity: GRANULARITIES.has(granularityRaw) ? granularityRaw : null,
    excludeMp: parseBooleanFlag(params.get("excludeMp")),
    month: yearMonthOrNull(params.get("month")),
    page: positiveIntOrOne(params.get("page")),
    pathname: path || FINANCIAL_BASE_PATH,
  };
}

export function buildFinancialHref(input: {
  subpluginId: string;
  branch: FinancialBranch;
  startDate?: string | null;
  endDate?: string | null;
  search?: string | null;
  costCenter?: string | null;
  supplierCode?: string | null;
  supplierStore?: string | null;
  customerCode?: string | null;
  customerStore?: string | null;
  clientKey?: string | null;
  status?: string | null;
  delayRange?: string | null;
  granularity?: string | null;
  excludeMp?: boolean | null;
  month?: string | null;
  page?: number | null;
}): string {
  const path =
    input.subpluginId === DEFAULT_SUBPLUGIN
      ? FINANCIAL_BASE_PATH
      : `${FINANCIAL_BASE_PATH}/${input.subpluginId}`;
  const params = new URLSearchParams();
  params.set("branch", input.branch);
  if (input.startDate) params.set("startDate", input.startDate);
  if (input.endDate) params.set("endDate", input.endDate);
  if (input.search) params.set("q", input.search);
  if (input.costCenter) params.set("costCenter", input.costCenter);
  if (input.supplierCode) params.set("supplier", input.supplierCode);
  if (input.supplierStore) params.set("supplierStore", input.supplierStore);
  if (input.customerCode) params.set("customer", input.customerCode);
  if (input.customerStore) params.set("customerStore", input.customerStore);
  if (input.clientKey) params.set("client", input.clientKey);
  if (input.status) params.set("status", input.status);
  if (input.delayRange) params.set("delayRange", input.delayRange);
  if (input.granularity) params.set("granularity", input.granularity);
  if (input.excludeMp) params.set("excludeMp", "1");
  if (input.month) params.set("month", input.month);
  if (input.page && input.page > 1) params.set("page", String(input.page));
  return `${path}?${params.toString()}`;
}

export function navigateFinancial(href: string) {
  if (typeof window === "undefined") return;
  const url = new URL(href, window.location.origin);
  const current = `${window.location.pathname}${window.location.search}`;
  const next = `${url.pathname}${url.search}`;
  if (current === next) return;
  window.history.pushState(null, "", next);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

/** Atualiza filtros sem empilhar histórico — usado por busca e paginação. */
export function replaceFinancialQuery(href: string) {
  if (typeof window === "undefined") return;
  const url = new URL(href, window.location.origin);
  const current = `${window.location.pathname}${window.location.search}`;
  const next = `${url.pathname}${url.search}`;
  if (current === next) return;
  window.history.replaceState(null, "", next);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
