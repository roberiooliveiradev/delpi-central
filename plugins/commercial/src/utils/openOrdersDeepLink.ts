import { COMMERCIAL_BASE_PATH } from "../app/pluginRoutes";
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

/** Escreve/atualiza params de atenção na URL sem apagar o restante. */
export function syncOpenOrdersAttentionQueryToUrl(
  attention: OpenOrdersAttentionDeepLink,
): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (attention.stockStatus && STOCK_QUERY_VALUES.has(attention.stockStatus)) {
    url.searchParams.set("stock", attention.stockStatus);
  } else {
    url.searchParams.delete("stock");
  }
  if (attention.lateOnly) {
    url.searchParams.set("focus", "late");
  } else {
    url.searchParams.delete("focus");
  }
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

export function syncOpenOrdersLineQueryToUrl(
  line: OpenOrdersLineDeepLink | null,
): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (!line) {
    url.searchParams.delete("pedido");
    url.searchParams.delete("linha");
    url.searchParams.delete("filial");
  } else {
    url.searchParams.set("pedido", line.pedido.trim());
    const linha = line.linha?.trim();
    if (linha) url.searchParams.set("linha", linha);
    else url.searchParams.delete("linha");
    const filial = line.filial?.trim();
    if (filial) url.searchParams.set("filial", filial);
    else url.searchParams.delete("filial");
  }
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

export function findOpenOrderLine(
  items: Array<{ filial: string; pedido: string; linha: string }>,
  link: OpenOrdersLineDeepLink,
) {
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
