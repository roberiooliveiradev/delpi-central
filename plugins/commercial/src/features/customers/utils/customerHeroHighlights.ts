import { formatDisplayDate } from "../../../utils/dates";
import { formatCurrency } from "../../../utils/format";
import type { CustomerSummary } from "../types/customerSummary";
import {
  billingTrendSymbol,
  formatBillingTrendPct,
} from "./billingTrendPresentation";

export type CustomerHeroHighlight = {
  id: string;
  label: string;
  value: string;
};

export function buildCustomerHeroHighlights(
  customer: Pick<
    CustomerSummary,
    | "billed12m"
    | "billingTrend"
    | "billingTrendPct"
    | "valorTotalAberto"
    | "quantidadePedidosAbertos"
    | "proximaEntrega"
    | "nextAction"
  >,
): {
  highlights: CustomerHeroHighlight[];
  nextAction: string | null;
} {
  const trendSymbol = billingTrendSymbol(customer.billingTrend);
  const trendPct = formatBillingTrendPct(customer.billingTrendPct);
  const billed =
    customer.billed12m == null
      ? "—"
      : [formatCurrency(customer.billed12m), trendSymbol, trendPct]
          .filter(Boolean)
          .join(" ");

  return {
    highlights: [
      { id: "billed12m", label: "Fat. 12 meses", value: billed },
      {
        id: "open-value",
        label: "Valor em aberto",
        value: formatCurrency(customer.valorTotalAberto),
      },
      {
        id: "open-orders",
        label: "Pedidos em aberto",
        value: customer.quantidadePedidosAbertos.toLocaleString("pt-BR"),
      },
      {
        id: "next-delivery",
        label: "Próxima entrega",
        value: formatDisplayDate(customer.proximaEntrega),
      },
    ],
    nextAction: customer.nextAction?.trim() || null,
  };
}
