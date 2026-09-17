import type { CustomerBillingSeriesPoint } from "../../../api/customerBillingSeriesApi";
import { mergeSeriesWithPriorYear } from "../../analytics/utils/periodShift";

export const PRIOR_VALUE_KEYS = ["value_prior", "value_prior_2", "value_prior_3"] as const;
export const PRIOR_QUANTITY_KEYS = [
  "quantity_prior",
  "quantity_prior_2",
  "quantity_prior_3",
] as const;

export type BillingSeriesOverlayPoint = CustomerBillingSeriesPoint & {
  value_prior?: number | null;
  value_prior_2?: number | null;
  value_prior_3?: number | null;
  quantity?: number | null;
  quantity_prior?: number | null;
  quantity_prior_2?: number | null;
  quantity_prior_3?: number | null;
};

/**
 * Combina série corrente com overlay de quantidade (Ambos) e YoY de valor/quantidade.
 * Priors alinham por índice de bucket (mesmo recorte deslocado N anos).
 */
export function mergeBillingSeriesOverlays(args: {
  current: readonly CustomerBillingSeriesPoint[];
  quantityPoints?: readonly CustomerBillingSeriesPoint[] | null;
  priorValueSeries?: ReadonlyArray<readonly CustomerBillingSeriesPoint[] | null | undefined>;
  priorQuantitySeries?: ReadonlyArray<readonly CustomerBillingSeriesPoint[] | null | undefined>;
}): BillingSeriesOverlayPoint[] {
  let next: BillingSeriesOverlayPoint[] = args.current.map((point) => ({ ...point }));
  (args.priorValueSeries ?? []).forEach((priorPoints, index) => {
    const key = PRIOR_VALUE_KEYS[index];
    if (!key) return;
    next = mergeSeriesWithPriorYear(next, priorPoints ?? [], (point) => ({
      [key]: point?.value ?? null,
    }));
  });
  const quantityPoints = args.quantityPoints;
  if (quantityPoints) {
    const qtyByMonth = new Map(
      quantityPoints.map((point) => [point.month, Number(point.value) || 0]),
    );
    next = next.map((point) => ({
      ...point,
      quantity: qtyByMonth.get(point.month) ?? 0,
    }));
  }
  (args.priorQuantitySeries ?? []).forEach((priorPoints, index) => {
    const key = PRIOR_QUANTITY_KEYS[index];
    if (!key) return;
    next = mergeSeriesWithPriorYear(next, priorPoints ?? [], (point) => ({
      [key]: point?.value ?? null,
    }));
  });
  if (quantityPoints) {
    const seen = new Set(next.map((point) => point.month));
    for (const point of quantityPoints) {
      if (seen.has(point.month)) continue;
      next.push({ ...point, value: 0, quantity: Number(point.value) || 0 });
    }
    next.sort((a, b) => {
      const byDate = a.date_start.localeCompare(b.date_start);
      return byDate || a.month.localeCompare(b.month);
    });
  }
  return next;
}
