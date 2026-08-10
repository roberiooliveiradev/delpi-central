import {
  COMMERCIAL_BASE_PATH,
  normalizeBasePath,
  normalizePathname,
} from "../app/pluginRoutes";
import type {
  CustomerListSortDirection,
  CustomerListSortKey,
} from "../features/customers/types/customerSummary";

export const CUSTOMER_LIST_FOCUS_VALUES = [
  "all",
  "attention",
  "inactive",
  "growth",
  "no_sale_60",
] as const;

export type CustomerListFocus = (typeof CUSTOMER_LIST_FOCUS_VALUES)[number];

export type CustomersListDeepLink = {
  q: string;
  focus: CustomerListFocus;
  sellerId: string | null;
  sort: CustomerListSortKey;
  dir: CustomerListSortDirection;
  page: number;
};

export type CustomersListDeepLinkInput = {
  q?: string | null;
  focus?: string | null;
  sellerId?: string | null;
  sort?: string | null;
  dir?: string | null;
  page?: number | string | null;
};

export type CustomersListSellerAccess = {
  allowSellerId: boolean;
  validSellerIds: readonly string[];
};

const FOCUS_VALUES = new Set<string>(CUSTOMER_LIST_FOCUS_VALUES);
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

const DENY_SELLER_ACCESS: CustomersListSellerAccess = {
  allowSellerId: false,
  validSellerIds: [],
};

function normalizeFocus(value: string | null | undefined): CustomerListFocus {
  const normalized = (value ?? "").trim().toLowerCase();
  return FOCUS_VALUES.has(normalized) ? (normalized as CustomerListFocus) : "all";
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
  return {
    q: (value.q ?? "").trim(),
    focus: normalizeFocus(value.focus),
    sellerId: normalizeSellerId(value.sellerId, access),
    sort: normalizeSort(value.sort),
    dir: normalizeDirection(value.dir),
    page: normalizePage(value.page),
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
      sellerId: params.get("seller_id"),
      sort: params.get("sort"),
      dir: params.get("dir"),
      page: params.get("page"),
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
  if (sanitized.sellerId) params.set("seller_id", sanitized.sellerId);
  if (sanitized.sort !== DEFAULT_CUSTOMERS_LIST_SORT) params.set("sort", sanitized.sort);
  if (sanitized.dir !== DEFAULT_CUSTOMERS_LIST_DIRECTION) params.set("dir", sanitized.dir);
  if (sanitized.page !== 1) params.set("page", String(sanitized.page));
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
