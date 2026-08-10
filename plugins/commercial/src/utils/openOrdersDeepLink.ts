import { COMMERCIAL_BASE_PATH } from "../app/pluginRoutes";
import type { OpenOrdersTotvsFilters } from "./filterItems";
import {
  DEFAULT_SORT,
  type SortDirection,
  type SortKey,
} from "./sortItems";
import type { StockFilter } from "./statusBadges";

export type OpenOrdersAttentionDeepLink = {
  stockStatus?: StockFilter;
  lateOnly?: boolean;
};

export type OpenOrdersLineDeepLink = {
  pedido: string;
  /** Quando omitido, abre a primeira linha do pedido (ex.: deep link OTD só com C2_PEDIDO). */
  linha?: string;
  filial?: string;
};

const STOCK_QUERY_VALUES = new Set<string>(["com_estoque", "parcial", "sem_estoque"]);
const SORT_QUERY_VALUES = new Set<SortKey>([
  "nome_cliente",
  "loja_cadastro",
  "filial",
  "pedido",
  "pedido_cliente",
  "produto",
  "data_entrega",
  "data_despacho",
  "saldo",
  "cobertura",
  "valor_aberto",
  "previsao_entrega_op",
  "atraso_dias",
]);

export type OpenOrdersSellerAccess = {
  allowSellerId: boolean;
  validSellerIds: readonly string[];
};

export type OpenOrdersListUrlState = {
  filters: OpenOrdersTotvsFilters;
  sellerId: string | null;
  sortKey: SortKey;
  sortDirection: SortDirection;
  page: number;
};

const DENY_SELLER_ACCESS: OpenOrdersSellerAccess = {
  allowSellerId: false,
  validSellerIds: [],
};

function isIsoDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

export function resolveOpenOrdersSellerId(
  rawSellerId: string | null | undefined,
  access: OpenOrdersSellerAccess = DENY_SELLER_ACCESS,
): string | null {
  const sellerId = (rawSellerId ?? "").trim();
  if (!sellerId || !access.allowSellerId) return null;
  return access.validSellerIds.includes(sellerId) ? sellerId : null;
}

export function parseOpenOrdersListUrlState(
  search = typeof window !== "undefined" ? window.location.search : "",
  sellerAccess: OpenOrdersSellerAccess = DENY_SELLER_ACCESS,
): OpenOrdersListUrlState {
  const params = new URLSearchParams(search);
  const stock = (params.get("stock") ?? "").trim();
  const focus = (params.get("focus") ?? "").trim().toLowerCase();
  const sort = (params.get("sort") ?? "").trim() as SortKey;
  const direction = (params.get("dir") ?? "").trim();
  const pageValue = Number(params.get("page"));
  const dateStart = (params.get("date_start") ?? "").trim();
  const dateEnd = (params.get("date_end") ?? "").trim();

  return {
    filters: {
      search: (params.get("q") ?? "").trim(),
      filial: (params.get("branch") ?? "").trim(),
      clientCodes: params
        .getAll("client")
        .map((value) => value.trim())
        .filter((value, index, values) => Boolean(value) && values.indexOf(value) === index),
      stockStatus: STOCK_QUERY_VALUES.has(stock) ? (stock as StockFilter) : "",
      dateStart: isIsoDate(dateStart) ? dateStart : "",
      dateEnd: isIsoDate(dateEnd) ? dateEnd : "",
      lateOnly: focus === "late",
    },
    sellerId: resolveOpenOrdersSellerId(params.get("seller_id"), sellerAccess),
    sortKey: SORT_QUERY_VALUES.has(sort) ? sort : DEFAULT_SORT.key,
    sortDirection: direction === "desc" || direction === "asc"
      ? direction
      : DEFAULT_SORT.direction,
    page: Number.isSafeInteger(pageValue) && pageValue > 0 ? pageValue : 1,
  };
}

export function buildOpenOrdersListSearch(state: OpenOrdersListUrlState): string {
  const params = new URLSearchParams();
  const { filters } = state;
  if (filters.search.trim()) params.set("q", filters.search.trim());
  if (filters.filial.trim()) params.set("branch", filters.filial.trim());
  for (const client of filters.clientCodes) {
    const value = client.trim();
    if (value) params.append("client", value);
  }
  if (filters.stockStatus && STOCK_QUERY_VALUES.has(filters.stockStatus)) {
    params.set("stock", filters.stockStatus);
  }
  if (filters.lateOnly) params.set("focus", "late");
  if (isIsoDate(filters.dateStart)) params.set("date_start", filters.dateStart);
  if (isIsoDate(filters.dateEnd)) params.set("date_end", filters.dateEnd);
  if (state.sellerId) params.set("seller_id", state.sellerId);
  if (state.sortKey !== DEFAULT_SORT.key) params.set("sort", state.sortKey);
  if (state.sortDirection !== DEFAULT_SORT.direction) params.set("dir", state.sortDirection);
  if (state.page > 1) params.set("page", String(state.page));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function sanitizeOpenOrdersListSearch(
  search: string,
  sellerAccess: OpenOrdersSellerAccess = DENY_SELLER_ACCESS,
): string {
  return buildOpenOrdersListSearch(parseOpenOrdersListUrlState(search, sellerAccess));
}

export function buildCommercialOpenOrderPath(
  options: OpenOrdersLineDeepLink & OpenOrdersAttentionDeepLink & { basePath?: string },
): string {
  const base = (options.basePath || COMMERCIAL_BASE_PATH).replace(/\/$/, "");
  const path = `${base}/open-orders`;
  const params = new URLSearchParams();
  const pedido = options.pedido.trim();
  const linha = options.linha?.trim();
  if (pedido) params.set("pedido", pedido);
  if (linha) params.set("linha", linha);
  const filial = options.filial?.trim();
  if (filial) params.set("filial", filial);
  if (options.stockStatus && STOCK_QUERY_VALUES.has(options.stockStatus)) {
    params.set("stock", options.stockStatus);
  }
  if (options.lateOnly) params.set("focus", "late");
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

export function parseOpenOrdersAttentionDeepLink(
  search = typeof window !== "undefined" ? window.location.search : "",
): OpenOrdersAttentionDeepLink {
  const params = new URLSearchParams(search);
  const patch: OpenOrdersAttentionDeepLink = {};
  const stock = (params.get("stock") ?? "").trim();
  if (STOCK_QUERY_VALUES.has(stock)) patch.stockStatus = stock as StockFilter;
  const focus = (params.get("focus") ?? "").trim().toLowerCase();
  if (focus === "late" || focus === "atraso") patch.lateOnly = true;
  return patch;
}

export function parseOpenOrdersLineDeepLink(
  search = typeof window !== "undefined" ? window.location.search : "",
): OpenOrdersLineDeepLink | null {
  const params = new URLSearchParams(search);
  const pedido = (params.get("pedido") ?? "").trim();
  if (!pedido) return null;
  const linha = (params.get("linha") ?? "").trim() || undefined;
  const filial = (params.get("filial") ?? "").trim() || undefined;
  return { pedido, linha, filial };
}

/** Mantém apenas o contexto reconhecido da bancada ao entrar/sair de uma ficha de OP. */
export function buildOpenOrdersContextSearch(
  search = typeof window !== "undefined" ? window.location.search : "",
  sellerAccess?: OpenOrdersSellerAccess,
): string {
  const access = sellerAccess ?? {
    allowSellerId: true,
    validSellerIds: [(new URLSearchParams(search).get("seller_id") ?? "").trim()].filter(Boolean),
  };
  return sanitizeOpenOrdersListSearch(search, access);
}

export function isOpenOrdersListPath(pathname: string, basePath = COMMERCIAL_BASE_PATH): boolean {
  const normalizedPath = pathname.replace(/\/+$/, "");
  const normalizedBase = basePath.replace(/\/+$/, "");
  return normalizedPath === `${normalizedBase}/open-orders`;
}

export function parseOpenOrdersListRouteState(
  pathname: string,
  search: string,
  basePath = COMMERCIAL_BASE_PATH,
  sellerAccess: OpenOrdersSellerAccess = DENY_SELLER_ACCESS,
): OpenOrdersListUrlState | null {
  if (!isOpenOrdersListPath(pathname, basePath)) return null;
  return parseOpenOrdersListUrlState(search, sellerAccess);
}

/** Sincroniza apenas a rota canônica da lista, sem alcançar fichas de linha/OP. */
export function syncOpenOrdersListStateToUrl(
  state: OpenOrdersListUrlState,
  basePath = COMMERCIAL_BASE_PATH,
): void {
  if (typeof window === "undefined") return;
  if (!isOpenOrdersListPath(window.location.pathname, basePath)) return;
  if (parseOpenOrdersLineDeepLink(window.location.search)) return;
  const url = new URL(window.location.href);
  const search = buildOpenOrdersListSearch(state);
  const target = `${url.pathname}${search}${url.hash}`;
  const current = `${url.pathname}${url.search}${url.hash}`;
  if (target !== current) window.history.replaceState(window.history.state, "", target);
}

export function findOpenOrderLine<T extends { filial: string; pedido: string; linha: string }>(
  items: T[],
  link: OpenOrdersLineDeepLink,
): T | null {
  const pedido = link.pedido.trim();
  const linha = link.linha?.trim();
  const filial = link.filial?.trim();
  return (
    items.find((row) => {
      if (row.pedido.trim() !== pedido) return false;
      if (linha && row.linha.trim() !== linha) return false;
      if (filial && row.filial.trim() !== filial) return false;
      return true;
    }) ?? null
  );
}
