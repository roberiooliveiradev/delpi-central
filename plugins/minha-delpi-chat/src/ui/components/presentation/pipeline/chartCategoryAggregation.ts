const PERCENT_HINTS = ["percent", "pct", "eficiencia", "efficiency", "taxa", "yield", "rate"];
const SUM_HINTS = [
  "count",
  "qtd",
  "quantidade",
  "qty",
  "hours",
  "horas",
  "mod",
  "resultado",
  "lucro",
  "prejuizo",
  "apont",
  "profit",
  "loss",
];
const WEIGHT_KEYS = [
  "tempo_real_horas",
  "real_hours",
  "planned_hours",
  "tempo_previsto_horas",
];

export function shouldAggregateChartByCategory(
  data: Record<string, unknown>[],
  categoryKey: string,
): boolean {
  if (!categoryKey || data.length < 2) {
    return false;
  }

  const labels = data.map((row) => String(row[categoryKey] ?? "").trim());

  return new Set(labels).size < labels.length;
}

export function aggregateChartRowsByCategory(
  data: Record<string, unknown>[],
  categoryKey: string,
  valueKeys: string[],
): Record<string, unknown>[] {
  if (!shouldAggregateChartByCategory(data, categoryKey)) {
    return data;
  }

  const grouped = new Map<string, Record<string, unknown>[]>();

  for (const row of data) {
    const label = String(row[categoryKey] ?? "").trim();
    const bucket = grouped.get(label) ?? [];

    bucket.push(row);
    grouped.set(label, bucket);
  }

  return [...grouped.entries()]
    .sort(([left], [right]) => compareCategoryLabel(left, right))
    .map(([label, rows]) => {
      const aggregated: Record<string, unknown> = { [categoryKey]: label };

      for (const key of valueKeys) {
        if (key === categoryKey) {
          continue;
        }

        aggregated[key] = aggregateMetric(rows, key);
      }

      return aggregated;
    });
}

function aggregateMetric(rows: Record<string, unknown>[], key: string): number {
  const values = rows
    .map((row) => Number(row[key]))
    .filter((value) => Number.isFinite(value));

  if (!values.length) {
    return 0;
  }

  const lowered = key.toLowerCase();

  if (PERCENT_HINTS.some((token) => lowered.includes(token))) {
    const weightKey = WEIGHT_KEYS.find((candidate) => candidate in (rows[0] ?? {}));

    if (weightKey) {
      const totalWeight = rows.reduce((sum, row) => {
        const weight = Number(row[weightKey]);

        return Number.isFinite(weight) ? sum + weight : sum;
      }, 0);

      if (totalWeight > 0) {
        const weighted = rows.reduce((sum, row) => {
          const value = Number(row[key]);
          const weight = Number(row[weightKey]);

          if (!Number.isFinite(value) || !Number.isFinite(weight)) {
            return sum;
          }

          return sum + value * weight;
        }, 0);

        return round(weighted / totalWeight);
      }
    }

    return round(values.reduce((sum, value) => sum + value, 0) / values.length);
  }

  if (SUM_HINTS.some((token) => lowered.includes(token))) {
    return round(values.reduce((sum, value) => sum + value, 0));
  }

  return round(values.reduce((sum, value) => sum + value, 0) / values.length);
}

function compareCategoryLabel(left: string, right: string): number {
  const leftNumeric = /^\d+$/.test(left);
  const rightNumeric = /^\d+$/.test(right);

  if (leftNumeric && rightNumeric) {
    return Number(left) - Number(right);
  }

  return left.localeCompare(right, "pt-BR", { numeric: true });
}

function round(value: number): number {
  return Math.round(value * 10000) / 10000;
}
