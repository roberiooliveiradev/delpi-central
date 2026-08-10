/** Filtro visual: ocultar sáb./dom. em séries diárias (não vai na query api-delpi). */

export const EXCLUDE_WEEKENDS_PARAM = "excludeWeekends";

const DAILY_GRANULARITY = new Set(["day", "daily", "dia"]);

export function isTruthyParam(value: unknown): boolean {
  if (value === true || value === 1) return true;
  const text = String(value ?? "")
    .trim()
    .toLowerCase();
  return text === "true" || text === "1" || text === "yes" || text === "on" || text === "sim";
}

export function isDailyGranularityValue(value: unknown): boolean {
  const raw = String(value ?? "")
    .trim()
    .toLowerCase();
  return DAILY_GRANULARITY.has(raw);
}

type GranularityField = {
  enum?: unknown[];
  default?: unknown;
};

export function routeSupportsDailyGranularity(
  schema: { granularity?: GranularityField } | null | undefined,
  fixedQueryParams?: Record<string, unknown> | null,
): boolean {
  const field = schema?.granularity;
  if (field) {
    const enumVals = Array.isArray(field.enum) ? field.enum : [];
    if (enumVals.length === 0) return true;
    return enumVals.some((item) => isDailyGranularityValue(item));
  }
  const fixed = fixedQueryParams?.granularity;
  return fixed != null && String(fixed).trim() !== "" && isDailyGranularityValue(fixed);
}

export function resolveEffectiveGranularity(
  schema: { granularity?: GranularityField } | null | undefined,
  values?: Record<string, unknown> | null,
  fixedQueryParams?: Record<string, unknown> | null,
): unknown {
  const fromValues = values?.granularity;
  if (fromValues != null && String(fromValues).trim() !== "") return fromValues;
  const field = schema?.granularity;
  if (field?.default != null && String(field.default).trim() !== "") return field.default;
  const enumVals = Array.isArray(field?.enum) ? field.enum : [];
  if (enumVals.length === 1) return enumVals[0];
  const fixed = fixedQueryParams?.granularity;
  if (fixed != null && String(fixed).trim() !== "") return fixed;
  return undefined;
}

/** Granularidade efetiva é dia — ou rota diária fixa (campo ausente + filtro já no schema). */
export function isEffectiveDailyGranularity(
  schema: ({ granularity?: GranularityField } & Record<string, unknown>) | null | undefined,
  values?: Record<string, unknown> | null,
  fixedQueryParams?: Record<string, unknown> | null,
): boolean {
  const effective = resolveEffectiveGranularity(schema, values, fixedQueryParams);
  if (effective != null && String(effective).trim() !== "") {
    return isDailyGranularityValue(effective);
  }
  if (schema?.granularity) return false;
  return Boolean(schema && EXCLUDE_WEEKENDS_PARAM in schema);
}

export function shouldApplyExcludeWeekends(
  params: Record<string, unknown> | null | undefined,
): boolean {
  if (!isTruthyParam(params?.[EXCLUDE_WEEKENDS_PARAM])) return false;
  const gran = params?.granularity;
  if (gran != null && String(gran).trim() !== "") {
    return isDailyGranularityValue(gran);
  }
  return true;
}

/** YYYY-MM-DD ou DD/MM/AA(AA) — calendário local, sem deslocar fuso. */
export function parseCategoryPointDate(label: unknown): Date | null {
  const text = String(label ?? "").trim();
  if (!text) return null;
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(text);
  if (iso) {
    const date = new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]));
    return Number.isNaN(date.getTime()) ? null : date;
  }
  const br = /^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/.exec(text);
  if (br) {
    let year = Number(br[3]);
    if (year < 100) year += year >= 70 ? 1900 : 2000;
    const date = new Date(year, Number(br[2]) - 1, Number(br[1]));
    return Number.isNaN(date.getTime()) ? null : date;
  }
  return null;
}

export function isWeekendDate(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

export function filterSeriesPointsExcludingWeekends<T extends { label?: unknown }>(
  points: readonly T[] | undefined | null,
): T[] {
  if (!points?.length) return [];
  return points.filter((point) => {
    const date = parseCategoryPointDate(point.label);
    if (!date) return true;
    return !isWeekendDate(date);
  });
}

type ChartLike = {
  points?: Array<{ label?: unknown; value?: unknown; size?: unknown }>;
  series?: Array<{
    name: string;
    field?: string;
    color?: string;
    plotOn?: "primary" | "secondary";
    points: Array<{ label?: unknown; value?: unknown; size?: unknown }>;
  }>;
  chartType?: "line" | "bar";
};

export function applyExcludeWeekendsToChart<T extends ChartLike>(chart: T | undefined): T | undefined {
  if (!chart) return chart;
  const series = chart.series?.map((item) => ({
    ...item,
    points: filterSeriesPointsExcludingWeekends(item.points),
  }));
  const points = series?.[0]?.points ?? filterSeriesPointsExcludingWeekends(chart.points);
  return { ...chart, points, ...(series ? { series } : {}) };
}

export function mergeChartViewFilterParams(
  layers: Array<Record<string, unknown> | null | undefined>,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const layer of layers) {
    if (!layer || typeof layer !== "object") continue;
    if (Object.prototype.hasOwnProperty.call(layer, EXCLUDE_WEEKENDS_PARAM)) {
      out[EXCLUDE_WEEKENDS_PARAM] = layer[EXCLUDE_WEEKENDS_PARAM];
    }
    if (Object.prototype.hasOwnProperty.call(layer, "granularity")) {
      const gran = layer.granularity;
      if (gran !== undefined && gran !== null && String(gran).trim() !== "") {
        out.granularity = gran;
      }
    }
  }
  return out;
}

export function lookupLinkedDataSourceParams(
  blocks:
    | ReadonlyArray<{
        id?: string;
        dataBinding?: { params?: Record<string, unknown> };
      }>
    | undefined,
  dataSourceId: string | undefined,
): Record<string, unknown> | undefined {
  const id = dataSourceId?.trim();
  if (!id || !blocks?.length) return undefined;
  const source = blocks.find((block) => block.id === id);
  const params = source?.dataBinding?.params;
  return params && typeof params === "object" ? params : undefined;
}

/** Omite params só de apresentação — não disparam refetch nem vão na query. */
export function omitVisualOnlyDataParams<T>(params: T): T {
  if (!params || typeof params !== "object" || Array.isArray(params)) return params;
  if (!Object.prototype.hasOwnProperty.call(params, EXCLUDE_WEEKENDS_PARAM)) return params;
  const next = { ...(params as Record<string, unknown>) };
  delete next[EXCLUDE_WEEKENDS_PARAM];
  return next as T;
}
