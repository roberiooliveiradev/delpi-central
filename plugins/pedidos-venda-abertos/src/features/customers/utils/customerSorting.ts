import { compareDeliveryDates } from "../../../utils/dates.ts";
import type {
  CustomerListSortDirection,
  CustomerListSortKey,
  CustomerSummary,
} from "../types/customerSummary.ts";

/**
 * Ordenação determinística da fila de atenção (não muta o array).
 * 1) tem atraso
 * 2) maior atraso (dias) DESC
 * 3) qtd pedidos atrasados DESC
 * 4) valor em aberto DESC
 * 5) nome ASC
 */
export function sortCustomersByAttention(
  customers: readonly CustomerSummary[],
): CustomerSummary[] {
  return [...customers].sort(compareAttention);
}

export function compareAttention(a: CustomerSummary, b: CustomerSummary): number {
  if (a.temAtraso !== b.temAtraso) {
    return a.temAtraso ? -1 : 1;
  }
  if (a.maiorAtrasoDias !== b.maiorAtrasoDias) {
    return b.maiorAtrasoDias - a.maiorAtrasoDias;
  }
  if (a.quantidadePedidosAtrasados !== b.quantidadePedidosAtrasados) {
    return b.quantidadePedidosAtrasados - a.quantidadePedidosAtrasados;
  }
  if (a.valorTotalAberto !== b.valorTotalAberto) {
    return b.valorTotalAberto - a.valorTotalAberto;
  }
  const byName = a.nome.localeCompare(b.nome, "pt-BR", { sensitivity: "base" });
  if (byName !== 0) return byName;
  return a.key.localeCompare(b.key);
}

export function sortCustomers(
  customers: readonly CustomerSummary[],
  key: CustomerListSortKey,
  direction: CustomerListSortDirection,
): CustomerSummary[] {
  if (key === "attention") {
    return sortCustomersByAttention(customers);
  }

  const factor = direction === "asc" ? 1 : -1;
  return [...customers].sort((a, b) => {
    let cmp = 0;
    switch (key) {
      case "nome":
        cmp = a.nome.localeCompare(b.nome, "pt-BR", { sensitivity: "base" });
        break;
      case "quantidadePedidosAtrasados":
        cmp = a.quantidadePedidosAtrasados - b.quantidadePedidosAtrasados;
        break;
      case "maiorAtrasoDias":
        cmp = a.maiorAtrasoDias - b.maiorAtrasoDias;
        break;
      case "valorTotalAberto":
        cmp = a.valorTotalAberto - b.valorTotalAberto;
        break;
      case "quantidadePedidosAbertos":
        cmp = a.quantidadePedidosAbertos - b.quantidadePedidosAbertos;
        break;
      case "proximaEntrega":
        cmp = compareDeliveryDates(a.proximaEntrega, b.proximaEntrega);
        break;
      case "billed12m":
        cmp = (a.billed12m ?? 0) - (b.billed12m ?? 0);
        break;
      case "lastPurchaseDate":
        cmp = compareDeliveryDates(a.lastPurchaseDate ?? null, b.lastPurchaseDate ?? null);
        break;
      case "city": {
        const cityA = `${a.city ?? ""} ${a.state ?? ""}`.trim();
        const cityB = `${b.city ?? ""} ${b.state ?? ""}`.trim();
        cmp = cityA.localeCompare(cityB, "pt-BR", { sensitivity: "base" });
        break;
      }
      case "sellerName":
        cmp = (a.sellerName ?? "").localeCompare(b.sellerName ?? "", "pt-BR", {
          sensitivity: "base",
        });
        break;
      case "billingTrend": {
        const rank = (trend: CustomerSummary["billingTrend"]): number => {
          if (trend === "up") return 3;
          if (trend === "stable") return 2;
          if (trend === "down") return 1;
          return 0;
        };
        cmp = rank(a.billingTrend) - rank(b.billingTrend);
        if (cmp === 0) {
          cmp = (a.billingTrendPct ?? Number.NEGATIVE_INFINITY) -
            (b.billingTrendPct ?? Number.NEGATIVE_INFINITY);
        }
        break;
      }
      default:
        cmp = 0;
    }
    if (cmp !== 0) return cmp * factor;
    return compareAttention(a, b);
  });
}

export const ATTENTION_LIST_LIMIT = 5;
