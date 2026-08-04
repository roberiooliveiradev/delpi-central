import { formatDisplayDate } from "../../../utils/dates.ts";
import type { CustomerSummary } from "../types/customerSummary.ts";

/**
 * Situação comercial textual, determinística e objetiva (sem score / IA).
 */
export function buildCommercialStatusLines(customer: CustomerSummary): string[] {
  const lines: string[] = [];

  if (customer.temAtraso) {
    lines.push("Cliente com pedidos atrasados");
  } else {
    lines.push("Cliente sem pedidos atrasados");
  }

  if (customer.temPedidoParcial) {
    lines.push("Possui pedidos parcialmente atendidos");
  }

  if (customer.proximaEntrega) {
    lines.push(`Próxima entrega em ${formatDisplayDate(customer.proximaEntrega)}`);
  } else {
    lines.push("Sem próxima entrega futura identificada");
  }

  return lines;
}
