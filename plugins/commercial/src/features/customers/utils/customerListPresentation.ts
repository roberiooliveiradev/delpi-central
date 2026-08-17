import type {
  CustomerCommercialStatus,
  CustomerSummary,
} from "../types/customerSummary";

export function resolveCustomerStatus(
  customer: Pick<
    CustomerSummary,
    "temAtraso" | "temPedidoParcial" | "quantidadePedidosAbertos"
  >,
): CustomerCommercialStatus {
  if (customer.temAtraso) return "atencao";
  if (customer.quantidadePedidosAbertos <= 0) return "inativo";
  if (customer.temPedidoParcial) return "atencao";
  return "ativo";
}

export function resolveCustomerNextAction(
  customer: Pick<
    CustomerSummary,
    "temAtraso" | "temPedidoParcial" | "proximaEntrega" | "quantidadePedidosAbertos"
  >,
): string {
  if (customer.temAtraso) return "Tratar atraso";
  if (customer.temPedidoParcial) return "Acompanhar parcial";
  if (customer.proximaEntrega) return "Acompanhar entrega";
  if (customer.quantidadePedidosAbertos > 0) return "Ver pedidos em aberto";
  return "Revisar carteira";
}

export function statusLabel(status: CustomerCommercialStatus): string {
  if (status === "atencao") return "Atenção";
  if (status === "inativo") return "Inativo";
  return "Ativo";
}
