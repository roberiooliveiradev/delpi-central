import type { CustomerSummary } from "../types/customerSummary";

export type BillingTrendDirection = NonNullable<CustomerSummary["billingTrend"]>;

export { BILLING_TREND_HELP } from "../../../content/helpTooltips";

export function billingTrendSymbol(trend: BillingTrendDirection | null | undefined): string {
  if (trend === "up") return "↑";
  if (trend === "down") return "↓";
  if (trend === "stable") return "→";
  return "";
}

export function formatBillingTrendPct(pct: number | null | undefined): string {
  if (pct === null || pct === undefined || !Number.isFinite(pct)) return "";
  const rounded = Math.round(pct * 10) / 10;
  const sign = rounded > 0 ? "+" : "";
  return `${sign}${rounded.toLocaleString("pt-BR", {
    maximumFractionDigits: 1,
    minimumFractionDigits: Number.isInteger(rounded) ? 0 : 1,
  })}%`;
}

export function billingTrendTitle(
  trend: BillingTrendDirection | null | undefined,
  pct: number | null | undefined,
): string {
  const base = "Comparação: últimos 6 meses com os 6 meses anteriores";
  if (!trend || trend === "insufficient") {
    return `${base}. Sem vendas suficientes para comparar.`;
  }
  const label =
    trend === "up" ? "alta" : trend === "down" ? "queda" : "estável";
  const pctLabel = formatBillingTrendPct(pct);
  return pctLabel ? `${base} (${label}, ${pctLabel}).` : `${base} (${label}).`;
}
