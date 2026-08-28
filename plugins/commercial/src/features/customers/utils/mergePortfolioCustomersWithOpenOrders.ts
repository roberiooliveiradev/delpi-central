import type { CustomerInScopeItem } from "../../../api/customersInScopeApi";
import type { CustomerSummary } from "../types/customerSummary";
import {
  buildIdentityCustomerSummary,
  mergeCustomerIdentity,
} from "./customerIdentitySummary";

/**
 * Universo = membership (in-scope); overlay = agregação de pedidos em aberto.
 */
export function mergePortfolioCustomersWithOpenOrders(
  inScope: readonly CustomerInScopeItem[],
  fromOrders: readonly CustomerSummary[],
): CustomerSummary[] {
  const ordersByKey = new Map(fromOrders.map((customer) => [customer.key, customer]));
  const merged: CustomerSummary[] = [];

  for (const item of inScope) {
    const identity = buildIdentityCustomerSummary({
      codigo: item.customer_code,
      loja: item.customer_store,
      nome: item.customer_name,
    });
    if (!identity) continue;

    const fromOrder = ordersByKey.get(identity.key);
    const base = mergeCustomerIdentity(fromOrder, identity);
    if (!base) continue;

    const openValue =
      fromOrder != null ? base.valorTotalAberto : Number(item.open_value) || 0;
    const hasOverdue = fromOrder != null ? base.temAtraso : Boolean(item.has_overdue);
    const openOrdersCount =
      fromOrder != null
        ? base.quantidadePedidosAbertos
        : item.has_open_orders || openValue > 0
          ? Math.max(1, base.quantidadePedidosAbertos)
          : 0;

    merged.push({
      ...base,
      valorTotalAberto: openValue,
      temAtraso: hasOverdue,
      quantidadePedidosAbertos: openOrdersCount,
      quantidadePedidosAtrasados:
        fromOrder != null
          ? base.quantidadePedidosAtrasados
          : hasOverdue
            ? Math.max(1, base.quantidadePedidosAtrasados)
            : 0,
    });
  }

  return merged;
}
