import type { KpiComparisonTone } from "./kpiComparisonTone";

export type MonthComparisonDirection = "higher_is_better" | "lower_is_better";

export type MonthComparison = {
  deltaAmount: number;
  /** `null` quando a base é zero/ausente — variação percentual não faz sentido. */
  deltaPct: number | null;
  tone: KpiComparisonTone | undefined;
};

/** Despesa é `lower_is_better`: subir contra o mês anterior é sinal negativo. */
export function resolveMonthComparison(
  current: number | null | undefined,
  previous: number | null | undefined,
  direction: MonthComparisonDirection = "lower_is_better",
): MonthComparison | null {
  if (current == null || previous == null) return null;
  if (!Number.isFinite(current) || !Number.isFinite(previous)) return null;

  const deltaAmount = current - previous;
  const deltaPct = previous === 0 ? null : (deltaAmount / Math.abs(previous)) * 100;

  let tone: KpiComparisonTone | undefined;
  if (deltaAmount !== 0) {
    const improved = direction === "lower_is_better" ? deltaAmount < 0 : deltaAmount > 0;
    tone = improved ? "positive" : "negative";
  }

  return { deltaAmount, deltaPct, tone };
}
