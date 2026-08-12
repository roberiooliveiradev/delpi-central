import {
  COMMERCIAL_BASE_PATH,
  normalizeBasePath,
  normalizePathname,
} from "../app/pluginRoutes";
import { looksLikeUserId } from "../shared/directoryUserLabel";

export const SELLER_PORTFOLIOS_FILTER_VALUES = [
  "all",
  "active",
  "inactive",
  "overlapping",
  "uncovered",
] as const;

export const SELLER_PORTFOLIOS_VIEW_VALUES = ["list", "org"] as const;
export const SELLER_PORTFOLIOS_AXIS_VALUES = ["portfolio", "person"] as const;

export type SellerPortfoliosFilter = (typeof SELLER_PORTFOLIOS_FILTER_VALUES)[number];
export type SellerPortfoliosView = (typeof SELLER_PORTFOLIOS_VIEW_VALUES)[number];
export type SellerPortfoliosAxis = (typeof SELLER_PORTFOLIOS_AXIS_VALUES)[number];

export type SellerPortfoliosDeepLink = {
  q: string;
  filter: SellerPortfoliosFilter;
  view: SellerPortfoliosView;
  axis: SellerPortfoliosAxis;
};

export type SellerPortfoliosDeepLinkInput = {
  q?: string | null;
  filter?: string | null;
  view?: string | null;
  axis?: string | null;
};

const FILTER_VALUES = new Set<string>(SELLER_PORTFOLIOS_FILTER_VALUES);
const VIEW_VALUES = new Set<string>(SELLER_PORTFOLIOS_VIEW_VALUES);
const AXIS_VALUES = new Set<string>(SELLER_PORTFOLIOS_AXIS_VALUES);

function normalizeFilter(value: string | null | undefined): SellerPortfoliosFilter {
  const normalized = (value ?? "").trim().toLowerCase();
  return FILTER_VALUES.has(normalized) ? (normalized as SellerPortfoliosFilter) : "all";
}

function normalizeView(value: string | null | undefined): SellerPortfoliosView {
  const normalized = (value ?? "").trim().toLowerCase();
  return VIEW_VALUES.has(normalized) ? (normalized as SellerPortfoliosView) : "list";
}

function normalizeAxis(value: string | null | undefined): SellerPortfoliosAxis {
  const normalized = (value ?? "").trim().toLowerCase();
  return AXIS_VALUES.has(normalized) ? (normalized as SellerPortfoliosAxis) : "portfolio";
}

/** Id de carteira aceito na URL (uuid) — evita abrir detalhe com lixo. */
export function normalizeSellerPortfolioId(value: string | null | undefined): string | null {
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
    view: normalizeView(value.view),
    axis: normalizeAxis(value.axis),
  };
}

export function parseSellerPortfoliosDeepLink(
  search: string | undefined,
): SellerPortfoliosDeepLink {
  const params = new URLSearchParams(search?.startsWith("?") ? search.slice(1) : search ?? "");
  return sanitizeSellerPortfoliosDeepLink({
    q: params.get("q") ?? "",
    filter: params.get("filter"),
    view: params.get("view"),
    axis: params.get("axis"),
  });
}

export function buildSellerPortfoliosSearch(value: SellerPortfoliosDeepLinkInput): string {
  const sanitized = sanitizeSellerPortfoliosDeepLink(value);
  const params = new URLSearchParams();
  if (sanitized.q) params.set("q", sanitized.q);
  if (sanitized.filter !== "all") params.set("filter", sanitized.filter);
  if (sanitized.view !== "list") params.set("view", sanitized.view);
  if (sanitized.axis !== "portfolio") params.set("axis", sanitized.axis);
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function sanitizeSellerPortfoliosSearch(search: string | undefined): string {
  return buildSellerPortfoliosSearch(parseSellerPortfoliosDeepLink(search));
}

function commercialInternalBase(basePath: string | undefined): string {
  const normalizedBasePath = normalizeBasePath(basePath);
  return normalizedBasePath.startsWith("/") && !normalizedBasePath.startsWith("//")
    ? normalizedBasePath
    : COMMERCIAL_BASE_PATH;
}

/** Path canônico da lista de carteiras no hub Administração. */
function sellerPortfoliosPathname(basePath: string | undefined): string {
  return `${commercialInternalBase(basePath)}/administration/seller-portfolios`;
}

function sellerPortfoliosLegacyPathname(basePath: string | undefined): string {
  return `${commercialInternalBase(basePath)}/seller-portfolios`;
}

export function isSellerPortfoliosPathname(
  pathname: string | undefined,
  basePath: string | undefined,
): boolean {
  const normalized = normalizePathname(pathname ?? "");
  return (
    normalized === sellerPortfoliosPathname(basePath) ||
    normalized === sellerPortfoliosLegacyPathname(basePath)
  );
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

/** `/base/administration/seller-portfolios/:id` preservando o recorte da lista na query. */
export function buildSellerPortfolioDetailPath(
  basePath: string | undefined,
  portfolioId: string,
  listState?: SellerPortfoliosDeepLinkInput,
): string | null {
  const id = normalizeSellerPortfolioId(portfolioId) ?? portfolioId.trim();
  if (!id) return null;
  const search = listState ? buildSellerPortfoliosSearch(listState) : "";
  return `${sellerPortfoliosPathname(basePath)}/${encodeURIComponent(id)}${search}`;
}

function parseDetailUnderListPath(
  normalized: string,
  listPath: string,
  search: string | undefined,
): { portfolioId: string; list: SellerPortfoliosDeepLink } | null {
  if (!normalized.startsWith(`${listPath}/`)) return null;
  const rawId = normalized.slice(listPath.length + 1);
  if (!rawId || rawId.includes("/")) return null;
  let decoded = rawId;
  try {
    decoded = decodeURIComponent(rawId);
  } catch {
    return null;
  }
  const portfolioId = decoded.trim();
  if (!portfolioId) return null;
  return { portfolioId, list: parseSellerPortfoliosDeepLink(search) };
}

export function parseSellerPortfolioDetailRouteState(
  pathname: string | undefined,
  search: string | undefined,
  basePath: string | undefined,
): { portfolioId: string; list: SellerPortfoliosDeepLink } | null {
  const normalized = normalizePathname(pathname ?? "");
  return (
    parseDetailUnderListPath(normalized, sellerPortfoliosPathname(basePath), search) ??
    parseDetailUnderListPath(normalized, sellerPortfoliosLegacyPathname(basePath), search)
  );
}

/**
 * Legado `?id=<uuid>` na lista → detalhe canônico sob Administração.
 * Retorna o path canônico quando houve migração (o chamador navega com replace).
 */
export function migrateLegacySellerPortfolioIdParam(
  pathname: string | undefined,
  search: string | undefined,
  basePath: string | undefined,
): string | null {
  if (!isSellerPortfoliosPathname(pathname, basePath)) return null;
  const params = new URLSearchParams(search?.startsWith("?") ? search.slice(1) : search ?? "");
  const legacyId = normalizeSellerPortfolioId(params.get("id"));
  if (!legacyId) return null;
  return buildSellerPortfolioDetailPath(
    basePath,
    legacyId,
    parseSellerPortfoliosDeepLink(search),
  );
}
