export type DualAxisSeriesHint = {
  dataKey: string;
  name: string;
  axis?: "primary" | "secondary";
  plotAs?: "bar" | "line";
};

export const DUAL_Y_AXIS_RIGHT_WIDTH = 88;
export const DUAL_Y_AXIS_RIGHT_MARGIN = 96;

/** Série no eixo Y direito: `axis: secondary` ou dataKey listado pelo host. */
export function isSecondaryYSeries(
  entry: DualAxisSeriesHint,
  secondaryDataKeys?: ReadonlyArray<string> | null,
): boolean {
  if (entry.axis === "secondary") return true;
  return Boolean(secondaryDataKeys?.includes(entry.dataKey));
}

export function hasSecondaryYAxis(
  series: ReadonlyArray<DualAxisSeriesHint>,
  secondaryDataKeys?: ReadonlyArray<string> | null,
): boolean {
  if (secondaryDataKeys && secondaryDataKeys.length > 0) return true;
  return series.some((entry) => isSecondaryYSeries(entry, secondaryDataKeys));
}

export function dualYAxisMargin(hasSecondary: boolean, right?: number): { right?: number } {
  if (!hasSecondary) return {};
  return { right: Math.max(right ?? 0, DUAL_Y_AXIS_RIGHT_MARGIN) };
}

function readDataKey(value: unknown): string {
  if (typeof value === "string" && value) return value;
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return "";
}

/**
 * Recharts 2/3: o 3º argumento do formatter pode omitir `dataKey`.
 * Resolve a série por dataKey (item ou payload) e, se faltar, pelo nome da legenda.
 */
export function resolveTooltipSeries<T extends DualAxisSeriesHint>(
  series: ReadonlyArray<T>,
  name: unknown,
  item: unknown,
): T | undefined {
  const seriesByKey = new Map(series.map((entry) => [entry.dataKey, entry]));
  const seriesByName = new Map(series.map((entry) => [entry.name, entry]));
  const record = item && typeof item === "object" ? (item as Record<string, unknown>) : null;
  const nested =
    record?.payload && typeof record.payload === "object"
      ? (record.payload as Record<string, unknown>)
      : null;
  const dataKey = readDataKey(record?.dataKey) || readDataKey(nested?.dataKey);
  if (dataKey && seriesByKey.has(dataKey)) return seriesByKey.get(dataKey);
  const label = String(name ?? "");
  if (label && seriesByName.has(label)) return seriesByName.get(label);
  return undefined;
}
