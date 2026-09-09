import {
  resolveFieldLabel,
  type FieldLabels,
} from "./presentationFieldLabels";

export type ChartAxisHints = {
  preferY?: string[];
  preferX?: string[];
};

export type ChartAxisConfig = {
  xAxis?: string;
  yAxis?: string | string[];
  numericColumns?: string[];
  categoryColumns?: string[];
  bindingProvenance?: string;
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

export function formatChartColumnLabel(
  key: string,
  fieldLabels?: FieldLabels | null,
): string {
  return resolveFieldLabel(key, fieldLabels);
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

function firstConfiguredY(config?: ChartAxisConfig): string | null {
  if (!config) {
    return null;
  }

  if (Array.isArray(config.yAxis)) {
    const first = String(config.yAxis[0] || "").trim();
    return first || null;
  }

  const token = String(config.yAxis || "").trim();
  return token || null;
}

export function isCompiledChartBinding(config?: ChartAxisConfig): boolean {
  return String(config?.bindingProvenance || "")
    .trim()
    .toUpperCase() === "COMPILED";
}

/**
 * API owns default axes when bindingProvenance=COMPILED.
 * MFE heuristics are fallback only for incomplete local/legacy configs.
 */
export function inferDefaultChartAxes(
  data: Record<string, unknown>[],
  chartType: string,
  config?: ChartAxisConfig,
  hints: ChartAxisHints = {},
): { xKey: string; yKey: string; numericColumns: string[]; categoryColumns: string[] } {
  const numericColumns =
    config?.numericColumns?.length ? config.numericColumns : listNumericColumns(data);
  const categoryColumns =
    config?.categoryColumns?.length
      ? config.categoryColumns
      : listCategoryColumns(data, numericColumns);

  const configuredY = firstConfiguredY(config);
  const configuredX = String(config?.xAxis || "").trim() || null;
  const dataKeys = new Set(Object.keys(data[0] ?? {}));

  if (isCompiledChartBinding(config)) {
    const xKey =
      (configuredX && dataKeys.has(configuredX) ? configuredX : null) ||
      categoryColumns[0] ||
      numericColumns[0] ||
      Object.keys(data[0] ?? {})[0] ||
      "name";
    const yKey =
      (configuredY && dataKeys.has(configuredY) ? configuredY : null) ||
      numericColumns.find((key) => key !== xKey) ||
      numericColumns[0] ||
      "value";

    return { xKey, yKey, numericColumns, categoryColumns };
  }

  const yPriorities = [...(hints.preferY ?? []), ...Y_PRIORITY];
  const xPriorities = [...(hints.preferX ?? []), ...X_SCATTER_PRIORITY];

  const scoredY = pickBestKey(numericColumns, yPriorities, Y_DEPRIORITY);
  const yKey = scoredY || configuredY || numericColumns[0] || "value";

  const token = chartType.trim().toLowerCase();

  if (token === "scatter" && numericColumns.length >= 2) {
    const xCandidates = numericColumns.filter((key) => key !== yKey);
    const scoredX = pickBestKey(xCandidates, xPriorities, [...Y_DEPRIORITY, yKey]);
    const xKey =
      scoredX ||
      (configuredX && numericColumns.includes(configuredX) ? configuredX : null) ||
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
    (configuredX && categoryColumns.includes(configuredX) ? configuredX : null) ||
    categoryColumns[0] ||
    configuredX ||
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
