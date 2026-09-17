/** Métrica da série/mix de faturamento — value (R$), quantity (qtd) ou both. */

import { formatDisplayQuantity } from "../utils/displayQuantity";
import { formatCurrency, formatQuantity } from "../utils/format";

export type PortfolioBillingMetric = "value" | "quantity" | "both";

export const DEFAULT_PORTFOLIO_BILLING_METRIC: PortfolioBillingMetric = "value";

export const PORTFOLIO_BILLING_METRICS = ["value", "quantity", "both"] as const;

export const BILLING_METRIC_CONTENT = {
  value: {
    shortLabel: "R$",
    label: "Valor",
    hint: "Série e mix em reais (bruto ou líquido conforme a Natureza).",
  },
  quantity: {
    shortLabel: "Qtd",
    label: "Quantidade",
    hint: "Série e mix em quantidade fornecida (D2_QUANT; líquido desconta devoluções), com a UM da nota. UMs mistas não são convertidas.",
  },
  both: {
    shortLabel: "Ambos",
    label: "Valor e quantidade",
    hint: "Mostra R$ no eixo Y esquerdo e quantidade (com UM) no eixo Y direito, no mesmo tipo de gráfico (colunas/linhas/área). Ano anterior também compara a quantidade. As duas métricas entram nas colunas do mix.",
  },
} as const;

export function normalizePortfolioBillingMetric(
  value: string | null | undefined,
): PortfolioBillingMetric {
  const raw = (value || "").trim().toLowerCase();
  if (raw === "quantity" || raw === "both") return raw;
  return DEFAULT_PORTFOLIO_BILLING_METRIC;
}

export function includesValueMetric(metric: PortfolioBillingMetric): boolean {
  return metric === "value" || metric === "both";
}

export function includesQuantityMetric(metric: PortfolioBillingMetric): boolean {
  return metric === "quantity" || metric === "both";
}

/** Métrica enviada à API de série (value | quantity). */
export function apiBillingMetric(
  metric: PortfolioBillingMetric,
): "value" | "quantity" {
  return metric === "quantity" ? "quantity" : "value";
}

export function billingMetricShortLabel(metric: PortfolioBillingMetric): string {
  return BILLING_METRIC_CONTENT[metric].shortLabel;
}

/** UM homogênea da nota, ou «mistas» quando o recorte mistura UMs. */
export function billingQuantityUnitLabel(
  unit?: string | null,
  mixed?: boolean,
): string | null {
  if (mixed) return "mistas";
  const um = (unit || "").trim();
  return um || null;
}

/** Quantidade com UM da nota (catálogo; sem conversão MI→PC). */
export function formatQuantityWithUnit(
  value: number,
  unit?: string | null,
  mixed?: boolean,
): string {
  if (!Number.isFinite(value)) return "—";
  if (mixed) return `${formatQuantity(value)} mistas`;
  return formatDisplayQuantity(value, unit);
}

export function quantitySeriesName(
  unit?: string | null,
  mixed?: boolean,
): string {
  const label = billingQuantityUnitLabel(unit, mixed);
  return label ? `Quantidade fornecida (${label})` : "Quantidade fornecida";
}

/** Eixo/tooltip de charts: R$ abreviado ou quantidade com 3 casas e UM. */
export function formatChartMetricValue(
  value: number,
  metric: PortfolioBillingMetric,
  unit?: string | null,
): string {
  if (!Number.isFinite(value)) return "—";
  if (metric === "quantity") {
    return formatQuantityWithUnit(value, unit);
  }
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toLocaleString("pt-BR", {
      maximumFractionDigits: 1,
    })} mi`;
  }
  if (abs >= 1_000) {
    return `R$ ${(value / 1_000).toLocaleString("pt-BR", {
      maximumFractionDigits: 0,
    })} mil`;
  }
  return formatCurrency(value);
}

export function formatMetricTotal(
  value: number,
  metric: PortfolioBillingMetric,
  unit?: string | null,
  mixed?: boolean,
): string {
  if (metric === "quantity") return formatQuantityWithUnit(value, unit, mixed);
  return formatCurrency(value);
}
