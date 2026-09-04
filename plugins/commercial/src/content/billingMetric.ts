/** Métrica da série/mix de faturamento — value (R$) ou quantity (qtd fornecida). */

export type PortfolioBillingMetric = "value" | "quantity";

export const DEFAULT_PORTFOLIO_BILLING_METRIC: PortfolioBillingMetric = "value";

export const BILLING_METRIC_CONTENT = {
  value: {
    shortLabel: "R$",
    label: "Valor",
    hint: "Série e mix em reais (bruto ou líquido conforme a Natureza).",
  },
  quantity: {
    shortLabel: "Qtd",
    label: "Quantidade",
    hint: "Série e mix em quantidade fornecida (D2_QUANT; líquido desconta devoluções). UMs mistas não são convertidas.",
  },
} as const;

export function normalizePortfolioBillingMetric(
  value: string | null | undefined,
): PortfolioBillingMetric {
  const raw = (value || "").trim().toLowerCase();
  return raw === "quantity" ? "quantity" : DEFAULT_PORTFOLIO_BILLING_METRIC;
}

export function billingMetricShortLabel(metric: PortfolioBillingMetric): string {
  return BILLING_METRIC_CONTENT[metric].shortLabel;
}
