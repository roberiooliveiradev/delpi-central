export type ChartAxisHints = {
  preferY?: string[];
  preferX?: string[];
};

const Y_PRIORITY = [
  "eficiencia",
  "eficiência",
  "efficiency",
  "percentual",
  "percent",
  "pct",
  "yield",
  "taxa",
];

const Y_DEPRIORITY = ["tempo", "hora", "previsto", "real", "duration"];

const X_SCATTER_PRIORITY = ["qtd", "quantidade", "qty", "quantity", "apontad"];

const X_CATEGORY_PRIORITY = [
  "operador",
  "nome",
  "produto",
  "cliente",
  "fornecedor",
  "filial",
  "centro",
];

export function listNumericColumns(data: Record<string, unknown>[]): string[] {
  const sample = data[0];

  if (!sample) {
    return [];
  }

  return Object.keys(sample).filter(
    (key) => typeof sample[key] === "number" && Number.isFinite(Number(sample[key])),
  );
}

export function listCategoryColumns(
  data: Record<string, unknown>[],
  numericColumns: string[],
): string[] {
  const sample = data[0];
  const blocked = new Set(numericColumns);

  if (!sample) {
    return [];
  }

  return Object.keys(sample).filter((key) => {
    if (blocked.has(key)) {
      return false;
    }

    return typeof sample[key] === "string" && String(sample[key]).trim().length > 0;
  });
}

export function formatChartColumnLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim();
}

function scoreKey(
  key: string,
  priorities: string[],
  depriorities: string[],
): number {
  const lowered = key.toLowerCase();
  let score = 0;

  for (const [index, token] of priorities.entries()) {
    if (lowered.includes(token)) {
      score += 100 - index;
    }
  }

  for (const token of depriorities) {
    if (lowered.includes(token)) {
      score -= 40;
    }
  }

  return score;
}

export function inferDefaultChartAxes(
  data: Record<string, unknown>[],
  chartType: string,
  config?: {
    xAxis?: string;
    yAxis?: string | string[];
    numericColumns?: string[];
    categoryColumns?: string[];
  },
  hints: ChartAxisHints = {},
): { xKey: string; yKey: string; numericColumns: string[]; categoryColumns: string[] } {
  const numericColumns =
    config?.numericColumns?.length ? config.numericColumns : listNumericColumns(data);
  const categoryColumns =
    config?.categoryColumns?.length
      ? config.categoryColumns
      : listCategoryColumns(data, numericColumns);

  const yPriorities = [...(hints.preferY ?? []), ...Y_PRIORITY];
  const xPriorities = [...(hints.preferX ?? []), ...X_SCATTER_PRIORITY];

  const configuredY = Array.isArray(config?.yAxis) ? config.yAxis[0] : config?.yAxis;
  const scoredY = pickBestKey(numericColumns, yPriorities, Y_DEPRIORITY);
  const yKey = scoredY || configuredY || numericColumns[0] || "value";

  const token = chartType.trim().toLowerCase();

  if (token === "scatter" && numericColumns.length >= 2) {
    const xCandidates = numericColumns.filter((key) => key !== yKey);
    const scoredX = pickBestKey(xCandidates, xPriorities, [...Y_DEPRIORITY, yKey]);
    const xKey =
      scoredX ||
      (config?.xAxis && numericColumns.includes(config.xAxis) ? config.xAxis : null) ||
      xCandidates[0] ||
      yKey;

    return { xKey, yKey, numericColumns, categoryColumns };
  }

  const scoredCategory = pickBestKey(
    categoryColumns,
    [...(hints.preferX ?? []), ...X_CATEGORY_PRIORITY],
    [],
  );
  const xKey =
    scoredCategory ||
    (config?.xAxis && categoryColumns.includes(config.xAxis) ? config.xAxis : null) ||
    categoryColumns[0] ||
    config?.xAxis ||
    Object.keys(data[0] ?? {})[0] ||
    "name";

  return { xKey, yKey, numericColumns, categoryColumns };
}

function pickBestKey(keys: string[], priorities: string[], depriorities: string[]): string | null {
  if (!keys.length) {
    return null;
  }

  return [...keys].sort(
    (left, right) =>
      scoreKey(right, priorities, depriorities) - scoreKey(left, priorities, depriorities),
  )[0];
}

export function isNumericAxisChartType(chartType: string): boolean {
  return chartType === "scatter";
}
