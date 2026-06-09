import type { PedidosVendaAbertosItem } from "../types/pedidosVendaAbertos";
import { compareDeliveryDates } from "./dates";

export function buildStockGroupKey(item: PedidosVendaAbertosItem): string {
  return `${item.filial}::${item.produto}`;
}

export function buildLineKey(item: PedidosVendaAbertosItem): string {
  return `${item.filial}::${item.pedido}::${item.linha}::${item.produto}`;
}

export function getAllocatedStock(item: PedidosVendaAbertosItem): number {
  return item.estoque_alocado ?? 0;
}

function compareLinesForStockAllocation(
  a: PedidosVendaAbertosItem,
  b: PedidosVendaAbertosItem,
): number {
  const byDelivery = compareDeliveryDates(a.data_entrega, b.data_entrega);
  if (byDelivery !== 0) return byDelivery;

  const byPedido = (a.pedido ?? "").localeCompare(b.pedido ?? "", "pt-BR");
  if (byPedido !== 0) return byPedido;

  return (a.linha ?? "").localeCompare(b.linha ?? "", "pt-BR", { numeric: true });
}

function resolvePhysicalStock(items: PedidosVendaAbertosItem[]): number {
  return Math.max(0, ...items.map((item) => item.no_estoque ?? 0));
}

/**
 * Distribui o estoque físico repetido por produto/filial entre as linhas em aberto,
 * priorizando pedidos com data de entrega mais antiga (FIFO operacional).
 */
export function allocateStockToOrders(
  items: PedidosVendaAbertosItem[],
): PedidosVendaAbertosItem[] {
  if (items.length === 0) return [];

  const groups = new Map<string, PedidosVendaAbertosItem[]>();
  for (const item of items) {
    const key = buildStockGroupKey(item);
    const bucket = groups.get(key);
    if (bucket) bucket.push(item);
    else groups.set(key, [item]);
  }

  const allocatedByLine = new Map<string, number>();

  for (const groupItems of groups.values()) {
    let remaining = resolvePhysicalStock(groupItems);
    const sorted = [...groupItems].sort(compareLinesForStockAllocation);

    for (const item of sorted) {
      const saldo = Math.max(0, item.saldo ?? 0);
      const allocated = Math.min(remaining, saldo);
      allocatedByLine.set(buildLineKey(item), allocated);
      remaining -= allocated;
    }
  }

  return items.map((item) => ({
    ...item,
    estoque_alocado: allocatedByLine.get(buildLineKey(item)) ?? 0,
  }));
}
