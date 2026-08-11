import {
  COMMERCIAL_BASE_PATH,
  normalizeBasePath,
  normalizePathname,
} from "../app/pluginRoutes";
import { looksLikeUserId } from "../shared/directoryUserLabel";

export const SELLER_PORTFOLIOS_FILTER_VALUES = ["all", "active", "inactive"] as const;

export type SellerPortfoliosFilter = (typeof SELLER_PORTFOLIOS_FILTER_VALUES)[number];

export type SellerPortfoliosDeepLink = {
  q: string;
  filter: SellerPortfoliosFilter;
  id: string | null;
};

export type SellerPortfoliosDeepLinkInput = {
  q?: string | null;
  filter?: string | null;
  id?: string | null;
};

const FILTER_VALUES = new Set<string>(SELLER_PORTFOLIOS_FILTER_VALUES);

function normalizeFilter(value: string | null | undefined): SellerPortfoliosFilter {
  const normalized = (value ?? "").trim().toLowerCase();
  return FILTER_VALUES.has(normalized) ? (normalized as SellerPortfoliosFilter) : "all";
}

function normalizePortfolioId(value: string | null | undefined): string | null {
  const normalized = (value ?? "").trim();
  if (!normalized || !looksLikeUserId(normalized)) return null;
  return normalized;
}

export function sanitizeSellerPortfoliosDeepLink(
  value: SellerPortfoliosDeepLinkInput,
): SellerPortfoliosDeepLink {
  return {
    q: (value.q ?? "").trim(),
    filter: normalizeFilter(value.filter),
    id: normalizePortfolioId(value.id),
  };
}

export function parseSellerPortfoliosDeepLink(
  search: string | undefined,
): SellerPortfoliosDeepLink {
  const params = new URLSearchParams(search?.startsWith("?") ? search.slice(1) : search ?? "");
  return sanitizeSellerPortfoliosDeepLink({
    q: params.get("q") ?? "",
    filter: params.get("filter"),
    id: params.get("id"),
  });
}

export function buildSellerPortfoliosSearch(value: SellerPortfoliosDeepLinkInput): string {
  const sanitized = sanitizeSellerPortfoliosDeepLink(value);
  const params = new URLSearchParams();
  if (sanitized.q) params.set("q", sanitized.q);
  if (sanitized.filter !== "all") params.set("filter", sanitized.filter);
  if (sanitized.id) params.set("id", sanitized.id);
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function sanitizeSellerPortfoliosSearch(search: string | undefined): string {
  return buildSellerPortfoliosSearch(parseSellerPortfoliosDeepLink(search));
}

function sellerPortfoliosPathname(basePath: string | undefined): string {
  const normalizedBasePath = normalizeBasePath(basePath);
  const internalBasePath =
    normalizedBasePath.startsWith("/") && !normalizedBasePath.startsWith("//")
      ? normalizedBasePath
      : COMMERCIAL_BASE_PATH;
  return `${internalBasePath}/seller-portfolios`;
}

export function isSellerPortfoliosPathname(
  pathname: string | undefined,
  basePath: string | undefined,
): boolean {
  return normalizePathname(pathname ?? "") === sellerPortfoliosPathname(basePath);
}

export function parseSellerPortfoliosRouteState(
  pathname: string | undefined,
  search: string | undefined,
  basePath: string | undefined,
): SellerPortfoliosDeepLink | null {
  if (!isSellerPortfoliosPathname(pathname, basePath)) return null;
  return parseSellerPortfoliosDeepLink(search);
}

export function buildSellerPortfoliosPath(
  basePath: string | undefined,
  value: SellerPortfoliosDeepLinkInput,
): string {
  return `${sellerPortfoliosPathname(basePath)}${buildSellerPortfoliosSearch(value)}`;
}

export function replaceSellerPortfoliosSearch(
  basePath: string | undefined,
  value: SellerPortfoliosDeepLinkInput,
): void {
  if (typeof window === "undefined") return;
  if (!isSellerPortfoliosPathname(window.location.pathname, basePath)) return;
  const target = buildSellerPortfoliosPath(basePath, value);
  const current = `${window.location.pathname}${window.location.search}`;
  if (target !== current) window.history.replaceState(window.history.state, "", target);
}
