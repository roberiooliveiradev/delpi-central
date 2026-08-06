import {
  compareDeliveryDates,
  getDeliveryOverdueDays,
  isDeliveryOverdue,
} from "../../../utils/dates.ts";
import type { PedidosVendaAbertosItem } from "../../../types/pedidosVendaAbertos.ts";
import type {
  CustomerAggregationResult,
  CustomerSummary,
} from "../types/customerSummary.ts";
import {
  buildCustomerKey,
  buildOrderKey,
  normalizeCadastroPart,
} from "./customerIdentity.ts";

export function toFiniteNumber(value: unknown): number {
  if (value === null || value === undefined || value === "") return 0;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : 0;
}

export function isPartialDeliveryLine(item: PedidosVendaAbertosItem): boolean {
  const entregue = toFiniteNumber(item.entregue);
  const saldo = toFiniteNumber(item.saldo);
  return entregue > 0 && saldo > 0;
}

function pickDominantName(names: string[]): string {
  const counts = new Map<string, number>();
  for (const name of names) {
    const trimmed = name.trim();
    if (!trimmed) continue;
    counts.set(trimmed, (counts.get(trimmed) ?? 0) + 1);
  }
  let best = "";
  let bestCount = 0;
  for (const [name, count] of counts) {
    if (count > bestCount || (count === bestCount && name.localeCompare(best, "pt-BR") < 0)) {
      best = name;
      bestCount = count;
    }
  }
  return best;
}

function resolveNextDelivery(lines: PedidosVendaAbertosItem[]): string | null {
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

function summarizeGroup(
  key: string,
  codigo: string,
  loja: string,
  lines: PedidosVendaAbertosItem[],
): CustomerSummary {
  const orderKeys = new Set<string>();
  const overdueOrders = new Set<string>();
  const partialOrders = new Set<string>();
  let valorTotalAberto = 0;
  let maiorAtrasoDias = 0;
  const names: string[] = [];

  for (const line of lines) {
    names.push(line.nome_cliente ?? "");
    const orderKey = buildOrderKey(line.filial, line.pedido);
    orderKeys.add(orderKey);

    const saldo = toFiniteNumber(line.saldo);
    valorTotalAberto += toFiniteNumber(line.valor_aberto);

    if (isDeliveryOverdue(line.data_entrega, saldo)) {
      overdueOrders.add(orderKey);
      const days = getDeliveryOverdueDays(line.data_entrega) ?? 0;
      if (days > maiorAtrasoDias) maiorAtrasoDias = days;
    }

    if (isPartialDeliveryLine(line)) {
      partialOrders.add(orderKey);
    }
  }

  const quantidadePedidosAtrasados = overdueOrders.size;
  const quantidadePedidosParciais = partialOrders.size;

  return {
    key,
    codigo,
    loja,
    nome: pickDominantName(names),
    quantidadePedidosAbertos: orderKeys.size,
    quantidadeLinhasAbertas: lines.length,
    valorTotalAberto,
    quantidadePedidosAtrasados,
    maiorAtrasoDias,
    proximaEntrega: resolveNextDelivery(lines),
    quantidadePedidosParciais,
    temAtraso: quantidadePedidosAtrasados > 0,
    temPedidoParcial: quantidadePedidosParciais > 0,
    lines,
  };
}

/**
 * Agrega linhas de pedidos em aberto por `codigo_cadastro|loja_cadastro`.
 * Não muta o array de entrada. Não soma saldo em quantidade (UMs incompatíveis).
 */
export function aggregateCustomers(
  items: readonly PedidosVendaAbertosItem[],
): CustomerAggregationResult {
  const groups = new Map<string, PedidosVendaAbertosItem[]>();
  let incompleteLineCount = 0;
  const allOrderKeys = new Set<string>();
  let totalValorAberto = 0;

  for (const item of items) {
    const key = buildCustomerKey(item.codigo_cadastro, item.loja_cadastro);
    if (!key) {
      incompleteLineCount += 1;
      continue;
    }

    const list = groups.get(key);
    if (list) {
      list.push(item);
    } else {
      groups.set(key, [item]);
    }
  }

  const customers: CustomerSummary[] = [];
  for (const [key, lines] of groups) {
    const codigo = normalizeCadastroPart(lines[0]?.codigo_cadastro);
    const loja = normalizeCadastroPart(lines[0]?.loja_cadastro);
    const summary = summarizeGroup(key, codigo, loja, lines);
    customers.push(summary);
    totalValorAberto += summary.valorTotalAberto;
    for (const line of lines) {
      allOrderKeys.add(buildOrderKey(line.filial, line.pedido));
    }
  }

  return {
    customers,
    incompleteLineCount,
    totalPedidosAbertos: allOrderKeys.size,
    totalValorAberto,
    clientesComAtraso: customers.filter((c) => c.temAtraso).length,
  };
}
