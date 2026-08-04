import {
  compareDeliveryDates,
  getDeliveryOverdueDays,
  isDeliveryOverdue,
} from "../../../utils/dates.ts";
import type { PedidosVendaAbertosItem } from "../../../types/pedidosVendaAbertos.ts";
import type {
  CustomerOrderSituation,
  CustomerOrderSummary,
} from "../types/customerOrderSummary.ts";
import {
  isPartialDeliveryLine,
  toFiniteNumber,
} from "./customerAggregation.ts";
import { buildOrderKey, normalizeCadastroPart } from "./customerIdentity.ts";

function resolveNextDelivery(lines: readonly PedidosVendaAbertosItem[]): string | null {
  let next: string | null = null;
  for (const line of lines) {
    const saldo = toFiniteNumber(line.saldo);
    const data = line.data_entrega;
    if (!data || saldo <= 0) continue;
    if (isDeliveryOverdue(data, saldo)) continue;
    if (!next || compareDeliveryDates(data, next) < 0) {
      next = data;
    }
  }
  return next;
}

/**
 * Primeiro `pedido_cliente` não vazio na ordem das linhas do grupo (determinístico).
 */
export function pickPedidoCliente(lines: readonly PedidosVendaAbertosItem[]): string {
  for (const line of lines) {
    const value = normalizeCadastroPart(line.pedido_cliente);
    if (value) return value;
  }
  return "";
}

export function resolveOrderSituation(
  temAtraso: boolean,
  temParcial: boolean,
): CustomerOrderSituation {
  if (temAtraso) return "atrasado";
  if (temParcial) return "parcial";
  return "em_aberto";
}

function summarizeOrderGroup(lines: PedidosVendaAbertosItem[]): CustomerOrderSummary {
  const first = lines[0];
  const filial = normalizeCadastroPart(first?.filial);
  const pedido = normalizeCadastroPart(first?.pedido);
  const key = buildOrderKey(filial, pedido);

  let valorTotalAberto = 0;
  let quantidadeLinhasAtrasadas = 0;
  let maiorAtrasoDias = 0;
  let temParcial = false;

  for (const line of lines) {
    valorTotalAberto += toFiniteNumber(line.valor_aberto);
    const saldo = toFiniteNumber(line.saldo);
    if (isDeliveryOverdue(line.data_entrega, saldo)) {
      quantidadeLinhasAtrasadas += 1;
      const days = getDeliveryOverdueDays(line.data_entrega) ?? 0;
      if (days > maiorAtrasoDias) maiorAtrasoDias = days;
    }
    if (isPartialDeliveryLine(line)) {
      temParcial = true;
    }
  }

  const temAtraso = quantidadeLinhasAtrasadas > 0;

  return {
    key,
    filial,
    pedido,
    pedidoCliente: pickPedidoCliente(lines),
    quantidadeLinhas: lines.length,
    valorTotalAberto,
    quantidadeLinhasAtrasadas,
    maiorAtrasoDias,
    proximaEntrega: resolveNextDelivery(lines),
    temAtraso,
    temParcial,
    situacao: resolveOrderSituation(temAtraso, temParcial),
    lines,
  };
}

/**
 * Agrupa linhas do cliente por `filial|pedido`. Não muta a entrada.
 */
export function aggregateCustomerOrders(
  lines: readonly PedidosVendaAbertosItem[],
): CustomerOrderSummary[] {
  const groups = new Map<string, PedidosVendaAbertosItem[]>();

  for (const line of lines) {
    const key = buildOrderKey(line.filial, line.pedido);
    const list = groups.get(key);
    if (list) {
      list.push(line);
    } else {
      groups.set(key, [line]);
    }
  }

  const orders: CustomerOrderSummary[] = [];
  for (const groupLines of groups.values()) {
    orders.push(summarizeOrderGroup(groupLines));
  }

  return orders.sort((a, b) => {
    const byFilial = a.filial.localeCompare(b.filial, "pt-BR");
    if (byFilial !== 0) return byFilial;
    return a.pedido.localeCompare(b.pedido, "pt-BR");
  });
}

export function compareAttentionOrders(
  a: CustomerOrderSummary,
  b: CustomerOrderSummary,
): number {
  if (a.temAtraso !== b.temAtraso) {
    return a.temAtraso ? -1 : 1;
  }
  if (a.temAtraso && b.temAtraso) {
    if (a.maiorAtrasoDias !== b.maiorAtrasoDias) {
      return b.maiorAtrasoDias - a.maiorAtrasoDias;
    }
    if (a.valorTotalAberto !== b.valorTotalAberto) {
      return b.valorTotalAberto - a.valorTotalAberto;
    }
    const byPedido = a.pedido.localeCompare(b.pedido, "pt-BR");
    if (byPedido !== 0) return byPedido;
    return a.filial.localeCompare(b.filial, "pt-BR");
  }
  if (a.temParcial !== b.temParcial) {
    return a.temParcial ? -1 : 1;
  }
  if (a.valorTotalAberto !== b.valorTotalAberto) {
    return b.valorTotalAberto - a.valorTotalAberto;
  }
  return a.pedido.localeCompare(b.pedido, "pt-BR");
}

/**
 * Pedidos que exigem atenção:
 * 1) atrasados (ordenados por maior atraso, valor, pedido);
 * 2) parciais não atrasados;
 * 3) próxima entrega do cliente, se ainda não listada.
 * Não muta a entrada.
 */
export function selectAttentionOrders(
  orders: readonly CustomerOrderSummary[],
  customerNextDelivery: string | null,
): CustomerOrderSummary[] {
  const overdue = orders
    .filter((order) => order.temAtraso)
    .sort(compareAttentionOrders);
  const partial = orders
    .filter((order) => !order.temAtraso && order.temParcial)
    .sort(compareAttentionOrders);

  const result = [...overdue, ...partial];
  const seen = new Set(result.map((order) => order.key));

  if (customerNextDelivery) {
    const nextOrder = orders.find(
      (order) =>
        !seen.has(order.key) &&
        order.proximaEntrega === customerNextDelivery &&
        !order.temAtraso,
    );
    if (nextOrder) {
      result.push(nextOrder);
    }
  }

  return result;
}

export function orderSituationLabel(situacao: CustomerOrderSituation): string {
  if (situacao === "atrasado") return "Atrasado";
  if (situacao === "parcial") return "Parcialmente atendido";
  return "Em aberto";
}
