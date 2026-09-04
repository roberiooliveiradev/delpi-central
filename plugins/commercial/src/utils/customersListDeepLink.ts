import {
  COMMERCIAL_BASE_PATH,
  normalizeBasePath,
  normalizePathname,
} from "../app/pluginRoutes";
import {
  DEFAULT_PORTFOLIO_BILLING_NATURE,
  normalizePortfolioBillingNature,
  type PortfolioBillingAmountNature,
} from "../content/billingNature";
import {
  DEFAULT_PORTFOLIO_BILLING_METRIC,
  normalizePortfolioBillingMetric,
  type PortfolioBillingMetric,
} from "../content/billingMetric";
import type {
  CustomerListSortDirection,
  CustomerListSortKey,
} from "../features/customers/types/customerSummary";

export const CUSTOMER_LIST_FOCUS_VALUES = [
  "all",
  "attention",
  "active",
  "no_sale_60",
] as const;

export const CUSTOMER_LIST_TREND_VALUES = ["all", "up", "stable", "down"] as const;

export const CUSTOMER_LIST_PANEL_VALUES = [
  "billing",
  "abc",
  "ranking",
  "customers",
] as const;

export type CustomerListFocus = (typeof CUSTOMER_LIST_FOCUS_VALUES)[number];
export type CustomerListTrend = (typeof CUSTOMER_LIST_TREND_VALUES)[number];
export type CustomerListPanel = (typeof CUSTOMER_LIST_PANEL_VALUES)[number];

export type CustomersListDeepLink = {
  q: string;
  focus: CustomerListFocus;
  trend: CustomerListTrend;
  sellerId: string | null;
  sort: CustomerListSortKey;
  dir: CustomerListSortDirection;
  page: number;
  panel: CustomerListPanel;
  billingNature: PortfolioBillingAmountNature;
  billingMetric: PortfolioBillingMetric;
};

export type CustomersListDeepLinkInput = {
  q?: string | null;
  focus?: string | null;
  trend?: string | null;
  sellerId?: string | null;
  sort?: string | null;
  dir?: string | null;
  page?: number | string | null;
  panel?: string | null;
  billingNature?: string | null;
  billingMetric?: string | null;
};

export type CustomersListSellerAccess = {
  allowSellerId: boolean;
  validSellerIds: readonly string[];
};

const FOCUS_VALUES = new Set<string>(CUSTOMER_LIST_FOCUS_VALUES);
const TREND_VALUES = new Set<string>(CUSTOMER_LIST_TREND_VALUES);
const PANEL_VALUES = new Set<string>(CUSTOMER_LIST_PANEL_VALUES);
const LEGACY_FOCUS_GROWTH = "growth";
const LEGACY_FOCUS_INACTIVE = "inactive";
export const CUSTOMER_LIST_SORT_VALUES = [
  "attention",
  "nome",
  "quantidadePedidosAtrasados",
  "maiorAtrasoDias",
  "valorTotalAberto",
  "quantidadePedidosAbertos",
  "proximaEntrega",
  "billed12m",
  "lastPurchaseDate",
  "city",
  "sellerName",
  "billingTrend",
] as const satisfies readonly CustomerListSortKey[];
const SORT_VALUES = new Set<string>(CUSTOMER_LIST_SORT_VALUES);
export const DEFAULT_CUSTOMERS_LIST_SORT: CustomerListSortKey = "attention";
export const DEFAULT_CUSTOMERS_LIST_DIRECTION: CustomerListSortDirection = "asc";
export const DEFAULT_CUSTOMERS_LIST_PANEL: CustomerListPanel = "customers";

const DENY_SELLER_ACCESS: CustomersListSellerAccess = {
  allowSellerId: false,
  validSellerIds: [],
};

function normalizeFocus(value: string | null | undefined): CustomerListFocus {
  const normalized = (value ?? "").trim().toLowerCase();
  return FOCUS_VALUES.has(normalized) ? (normalized as CustomerListFocus) : "all";
}

function normalizeTrend(value: string | null | undefined): CustomerListTrend {
  const normalized = (value ?? "").trim().toLowerCase();
  return TREND_VALUES.has(normalized) ? (normalized as CustomerListTrend) : "all";
}

function normalizePanel(value: string | null | undefined): CustomerListPanel {
  const normalized = (value ?? "").trim().toLowerCase();
  return PANEL_VALUES.has(normalized)
    ? (normalized as CustomerListPanel)
    : DEFAULT_CUSTOMERS_LIST_PANEL;
}

function normalizeSort(value: string | null | undefined): CustomerListSortKey {
  const normalized = (value ?? "").trim();
  return SORT_VALUES.has(normalized)
    ? (normalized as CustomerListSortKey)
    : DEFAULT_CUSTOMERS_LIST_SORT;
}

function normalizeDirection(value: string | null | undefined): CustomerListSortDirection {
  return value === "desc" ? "desc" : DEFAULT_CUSTOMERS_LIST_DIRECTION;
}

function normalizePage(value: number | string | null | undefined): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isInteger(parsed) && parsed >= 1 ? parsed : 1;
}

function normalizeSellerId(
  value: string | null | undefined,
  access: CustomersListSellerAccess,
): string | null {
  if (!access.allowSellerId) return null;
  const normalized = (value ?? "").trim();
  if (!normalized) return null;
  return access.validSellerIds.some((sellerId) => sellerId === normalized)
    ? normalized
    : null;
}

export function sanitizeCustomersListDeepLink(
  value: CustomersListDeepLinkInput,
  access: CustomersListSellerAccess = DENY_SELLER_ACCESS,
): CustomersListDeepLink {
  const rawFocus = (value.focus ?? "").trim().toLowerCase();
  const hasExplicitTrend = Boolean((value.trend ?? "").trim());
  return {
    q: (value.q ?? "").trim(),
    focus: rawFocus === LEGACY_FOCUS_GROWTH || rawFocus === LEGACY_FOCUS_INACTIVE
      ? "all"
      : normalizeFocus(value.focus),
    trend:
      rawFocus === LEGACY_FOCUS_GROWTH && !hasExplicitTrend
        ? "up"
        : normalizeTrend(value.trend),
    sellerId: normalizeSellerId(value.sellerId, access),
    sort: normalizeSort(value.sort),
    dir: normalizeDirection(value.dir),
    page: normalizePage(value.page),
    panel: normalizePanel(value.panel),
    billingNature: normalizePortfolioBillingNature(value.billingNature),
    billingMetric: normalizePortfolioBillingMetric(value.billingMetric),
  };
}

export function parseCustomersListDeepLink(
  search: string | undefined,
  access: CustomersListSellerAccess = DENY_SELLER_ACCESS,
): CustomersListDeepLink {
  const params = new URLSearchParams(search?.startsWith("?") ? search.slice(1) : search ?? "");
  return sanitizeCustomersListDeepLink(
    {
      q: params.get("q") ?? "",
      focus: params.get("focus") ?? "all",
      trend: params.get("trend"),
      sellerId: params.get("seller_id"),
      sort: params.get("sort"),
      dir: params.get("dir"),
      page: params.get("page"),
      panel: params.get("panel"),
      billingNature: params.get("billingNature"),
      billingMetric: params.get("billingMetric"),
    },
    access,
  );
}

export function buildCustomersListSearch(
  value: CustomersListDeepLinkInput,
  access: CustomersListSellerAccess = DENY_SELLER_ACCESS,
): string {
  const sanitized = sanitizeCustomersListDeepLink(value, access);
  const params = new URLSearchParams();
  if (sanitized.q) params.set("q", sanitized.q);
  if (sanitized.focus !== "all") params.set("focus", sanitized.focus);
  if (sanitized.trend !== "all") params.set("trend", sanitized.trend);
  if (sanitized.sellerId) params.set("seller_id", sanitized.sellerId);
  if (sanitized.sort !== DEFAULT_CUSTOMERS_LIST_SORT) params.set("sort", sanitized.sort);
  if (sanitized.dir !== DEFAULT_CUSTOMERS_LIST_DIRECTION) params.set("dir", sanitized.dir);
  if (sanitized.page !== 1) params.set("page", String(sanitized.page));
  if (sanitized.panel !== DEFAULT_CUSTOMERS_LIST_PANEL) params.set("panel", sanitized.panel);
  if (sanitized.billingNature !== DEFAULT_PORTFOLIO_BILLING_NATURE) {
    params.set("billingNature", sanitized.billingNature);
  }
  if (sanitized.billingMetric !== DEFAULT_PORTFOLIO_BILLING_METRIC) {
    params.set("billingMetric", sanitized.billingMetric);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function sanitizeCustomersListSearch(
  search: string | undefined,
  access: CustomersListSellerAccess = DENY_SELLER_ACCESS,
): string {
  return buildCustomersListSearch(parseCustomersListDeepLink(search, access), access);
}

function customersListPathname(basePath: string | undefined): string {
  const normalizedBasePath = normalizeBasePath(basePath);
  const internalBasePath =
    normalizedBasePath.startsWith("/") && !normalizedBasePath.startsWith("//")
      ? normalizedBasePath
      : COMMERCIAL_BASE_PATH;
  return `${internalBasePath}/customers`;
}

export function isCustomersListPathname(
  pathname: string | undefined,
  basePath: string | undefined,
): boolean {
  return normalizePathname(pathname ?? "") === customersListPathname(basePath);
}

export function parseCustomersListRouteState(
  pathname: string | undefined,
  search: string | undefined,
  basePath: string | undefined,
  access: CustomersListSellerAccess = DENY_SELLER_ACCESS,
): CustomersListDeepLink | null {
  if (!isCustomersListPathname(pathname, basePath)) return null;
  return parseCustomersListDeepLink(search, access);
}

export function buildCustomersListPath(
  basePath: string | undefined,
  value: CustomersListDeepLinkInput,
  access: CustomersListSellerAccess = DENY_SELLER_ACCESS,
): string {
  const path = customersListPathname(basePath);
  return `${path}${buildCustomersListSearch(value, access)}`;
}
