import type {
  PedidosVendaAbertosItem,
  PedidosVendaAbertosSummary,
} from "../types/pedidosVendaAbertos";
import { formatEntityCodeStore } from "./entityCodeStore";
import { isDeliveryOverdue, isWithinDateRange } from "./dates";
import {
  getLineStatus,
  isFaturavelStatus,
  isParcialStatus,
  matchesStockFilter,
  type StockFilter,
} from "./statusBadges";

export type ClientOption = {
  key: string;
  name: string;
};

export type PedidosVendaAbertosFilters = {
  search: string;
  filial: string;
  clientCodes: string[];
  stockStatus: StockFilter;
  dateStart: string;
  dateEnd: string;
};

export const DEFAULT_FILTERS: PedidosVendaAbertosFilters = {
  search: "",
  filial: "",
  clientCodes: [],
  stockStatus: "",
  dateStart: "",
  dateEnd: "",
};

export function getClientKey(item: PedidosVendaAbertosItem): string {
  return item.nome_cliente?.trim() || item.codigo_cliente?.trim() || "";
}

function includesInsensitive(value: string | null | undefined, query: string): boolean {
  if (!query.trim()) return true;
  if (!value) return false;
  return value.toLocaleLowerCase("pt-BR").includes(query.trim().toLocaleLowerCase("pt-BR"));
}

export function filterPedidosItems(
  items: PedidosVendaAbertosItem[],
  filters: PedidosVendaAbertosFilters,
): PedidosVendaAbertosItem[] {
  return items.filter((item) => {
    if (filters.filial && item.filial !== filters.filial) return false;
    if (
      filters.clientCodes.length > 0 &&
      !filters.clientCodes.includes(getClientKey(item))
    ) {
      return false;
    }
    if (!matchesStockFilter(item, filters.stockStatus)) return false;

    if (filters.dateStart || filters.dateEnd) {
      if (!isWithinDateRange(item.data_entrega, filters.dateStart, filters.dateEnd)) {
        return false;
      }
    }

    if (filters.search.trim()) {
      const q = filters.search;
      const matchesSearch =
        includesInsensitive(item.nome_cliente, q) ||
        includesInsensitive(item.pedido, q) ||
        includesInsensitive(item.pedido_cliente, q) ||
        includesInsensitive(item.produto, q) ||
        includesInsensitive(item.codigo_cliente, q) ||
        includesInsensitive(item.codigo_cadastro, q) ||
        includesInsensitive(item.loja_cadastro, q) ||
        includesInsensitive(
          formatEntityCodeStore(item.codigo_cadastro, item.loja_cadastro) ?? undefined,
          q,
        );
      if (!matchesSearch) return false;
    }

    return true;
  });
}

export function computeSummaryFromItems(
  items: PedidosVendaAbertosItem[],
): PedidosVendaAbertosSummary {
  return {
    total_linhas: items.length,
    valor_total_aberto: items.reduce((acc, item) => acc + (item.valor_aberto ?? 0), 0),
    itens_com_estoque: items.filter((item) => isFaturavelStatus(getLineStatus(item).kind)).length,
    itens_estoque_parcial: items.filter((item) => isParcialStatus(getLineStatus(item).kind)).length,
    linhas_em_atraso: items.filter((item) =>
      isDeliveryOverdue(item.data_entrega, item.saldo),
    ).length,
  };
}

export function collectDistinctFiliais(items: PedidosVendaAbertosItem[]): string[] {
  return [...new Set(items.map((item) => item.filial).filter(Boolean))].sort();
}

export function collectDistinctClients(items: PedidosVendaAbertosItem[]): ClientOption[] {
  const clients = new Map<string, ClientOption>();

  for (const item of items) {
    const name = item.nome_cliente?.trim();
    if (!name) continue;

    const key = getClientKey(item);
    if (!key || clients.has(key)) continue;

    clients.set(key, { key, name });
  }

  return [...clients.values()].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
}
