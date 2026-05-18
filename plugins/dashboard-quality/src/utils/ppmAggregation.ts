import type { PpmItem } from "../types/ppm";
import { monthKeyToLabel, protheusDateToMonthKey } from "./dates";

export type PpmChartPoint = {
  periodo: string;
  sortKey: string;
  devolvido: number;
  registros: number;
};

export function aggregatePpmByMonth(items: PpmItem[]): PpmChartPoint[] {
  const buckets = new Map<
    string,
    { sortKey: string; devolvido: number; registros: number }
  >();

  for (const item of items) {
    const monthKey = protheusDateToMonthKey(item.registered_date);
    if (!monthKey) continue;

    const current = buckets.get(monthKey) ?? {
      sortKey: monthKey,
      devolvido: 0,
      registros: 0,
    };

    current.devolvido += item.returned_quantity_un ?? 0;
    current.registros += 1;
    buckets.set(monthKey, current);
  }

  return [...buckets.values()]
    .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
    .map((bucket) => ({
      periodo: monthKeyToLabel(bucket.sortKey),
      sortKey: bucket.sortKey,
      devolvido: Number(bucket.devolvido.toFixed(2)),
      registros: bucket.registros,
    }));
}
