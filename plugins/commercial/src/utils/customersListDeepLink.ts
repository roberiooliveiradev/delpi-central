import { COMMERCIAL_BASE_PATH, normalizeBasePath } from "../app/pluginRoutes";

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
};

export type CustomersListDeepLinkInput = {
  q?: string | null;
  focus?: string | null;
  sellerId?: string | null;
};

export type CustomersListSellerAccess = {
  allowSellerId: boolean;
  validSellerIds: readonly string[];
};

const FOCUS_VALUES = new Set<string>(CUSTOMER_LIST_FOCUS_VALUES);

const DENY_SELLER_ACCESS: CustomersListSellerAccess = {
  allowSellerId: false,
  validSellerIds: [],
};

function normalizeFocus(value: string | null | undefined): CustomerListFocus {
  const normalized = (value ?? "").trim().toLowerCase();
  return FOCUS_VALUES.has(normalized) ? (normalized as CustomerListFocus) : "all";
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
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function sanitizeCustomersListSearch(
  search: string | undefined,
  access: CustomersListSellerAccess = DENY_SELLER_ACCESS,
): string {
  return buildCustomersListSearch(parseCustomersListDeepLink(search, access), access);
}

export function buildCustomersListPath(
  basePath: string | undefined,
  value: CustomersListDeepLinkInput,
  access: CustomersListSellerAccess = DENY_SELLER_ACCESS,
): string {
  const normalizedBasePath = normalizeBasePath(basePath);
  const internalBasePath =
    normalizedBasePath.startsWith("/") && !normalizedBasePath.startsWith("//")
      ? normalizedBasePath
      : COMMERCIAL_BASE_PATH;
  const path = `${internalBasePath}/customers`;
  return `${path}${buildCustomersListSearch(value, access)}`;
}
