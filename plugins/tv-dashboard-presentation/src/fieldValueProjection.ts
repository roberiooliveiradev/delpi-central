/**
 * Fluxo centralizado: extrair valores de campo do `resolved` → agregar ou listar → formatar.
 * Texto dinâmico, KPI projection e gráficos devem consumir daqui (não reimplementar).
 *
 * Sem imports de viewProjection/comunicadoTypes (evita ciclo ESM).
 */
import { parseKpiNumericValue } from "@delpi/plugin-ui/index";

export type ViewAggregation = "first" | "sum" | "avg" | "min" | "max" | "count" | "list";

/**
 * Parse numérico para agregação — não usa o strip agressivo de `parseKpiNumericValue`
 * (ex.: "01/07/26" → 10726 → "10.726" na UI).
 */
export function parseProjectionNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  // Datas, meses e códigos alfanuméricos não são agregáveis.
  if (/[a-zA-Z]/.test(trimmed)) return null;
  if (/[/]/.test(trimmed)) return null;
  if (/^\d{4}-\d{2}-\d{2}/.test(trimmed)) return null;
  return parseKpiNumericValue(trimmed);
}

/** Agregações escalares (KPI/gráfico). */
export const VIEW_AGGREGATION_OPTIONS: Array<{ value: ViewAggregation; label: string }> = [
  { value: "first", label: "Primeiro valor" },
  { value: "sum", label: "Soma" },
  { value: "avg", label: "Média" },
  { value: "min", label: "Mínimo" },
  { value: "max", label: "Máximo" },
  { value: "count", label: "Contagem de linhas" },
];

/** Agregações do campo dinâmico de texto (inclui lista). */
export const TEXT_FIELD_AGGREGATION_OPTIONS: Array<{ value: ViewAggregation; label: string }> = [
  { value: "list", label: "Lista (sem agregar)" },
  ...VIEW_AGGREGATION_OPTIONS,
];

/** Separador padrão da agregação `list` (quebra de linha; CSS `pre-wrap` no bloco). */
export const FIELD_LIST_JOIN = "\n";

/** Shape mínimo do resolved — evita import de comunicadoTypes (ciclo ESM). */
export type ProjectionResolvedLike = {
  kpi?: { value?: unknown; label?: string } | null;
  kpiMetrics?: Array<{ field?: string; value?: unknown; label?: string }> | null;
  table?: {
    columns?: Array<{ key?: string; label?: string }> | null;
    rows?: Array<Record<string, unknown>> | null;
  } | null;
};

export function columnValuesFromRows(
  rows: Array<Record<string, unknown>>,
  field: string,
): unknown[] {
  return rows.map((row) => row[field]);
}

export function isCampoValorDumpTable(
  columns: Array<{ key?: string }> | undefined | null,
): boolean {
  if (!columns?.length) return false;
  const keys = new Set(columns.map((col) => String(col.key || "").trim()));
  return keys.size === 2 && keys.has("campo") && keys.has("valor");
}

function kpiScalarForField(resolved: ProjectionResolvedLike | undefined, field: string): unknown {
  if (!resolved || !field.trim()) return undefined;
  const trimmed = field.trim();
  for (const metric of resolved.kpiMetrics ?? []) {
    if (metric.field === trimmed) return metric.value;
  }
  if (resolved.kpi && (trimmed === "value" || trimmed === resolved.kpi.label)) {
    return resolved.kpi.value;
  }
  return undefined;
}

function campoValorLookup(resolved: ProjectionResolvedLike | undefined, field: string): unknown {
  const rows = resolved?.table?.rows;
  if (!rows?.length || !isCampoValorDumpTable(resolved?.table?.columns)) return undefined;
  const trimmed = field.trim();
  for (const row of rows) {
    if (String(row.campo ?? "").trim() === trimmed) return row.valor;
  }
  return undefined;
}

/**
 * Extrai todos os valores do campo para agregação/lista.
 * Série tabular (OEE/OTD…) tem prioridade sobre o escalar KPI (último ponto),
 * exceto dump campo/valor de SI — aí o KPI/lookup por nome do campo manda.
 */
export function extractProjectionFieldValues(
  resolved: ProjectionResolvedLike | undefined,
  field: string,
): unknown[] {
  if (!resolved || !field.trim()) return [];
  const trimmed = field.trim();
  const rows = resolved.table?.rows ?? [];
  const dump = isCampoValorDumpTable(resolved.table?.columns);

  if (rows.length > 0 && !dump) {
    const fromRows = columnValuesFromRows(rows, trimmed).filter(
      (value) => value != null && value !== "",
    );
    if (fromRows.length > 0) return fromRows;
  }

  const fromKpi = kpiScalarForField(resolved, trimmed);
  if (fromKpi != null && fromKpi !== "") return [fromKpi];

  if (dump) {
    const fromDump = campoValorLookup(resolved, trimmed);
    if (fromDump != null && fromDump !== "") return [fromDump];
  }

  const firstRow = rows[0];
  if (firstRow && typeof firstRow === "object" && trimmed in firstRow) {
    const value = firstRow[trimmed];
    if (value != null && value !== "") return [value];
  }
  return [];
}

/** Valor único (primeiro / KPI) — compatível com defaults e labels. */
export function extractProjectionFieldRawValue(
  resolved: ProjectionResolvedLike | undefined,
  field: string,
): unknown {
  const values = extractProjectionFieldValues(resolved, field);
  return values.length > 0 ? values[0] : undefined;
}

export function isNumericAggregation(aggregation: ViewAggregation | undefined): boolean {
  return aggregation === "sum" || aggregation === "avg" || aggregation === "min" || aggregation === "max";
}

/**
 * Agrega valores com parse numérico canônico (`parseKpiNumericValue`).
 * `list` não agrega — retorna null (o caller junta a lista).
 */
export function aggregateProjectionValues(
  values: unknown[],
  aggregation: ViewAggregation = "first",
): number | null {
  if (aggregation === "list") return null;
  if (aggregation === "count") return values.length;

  const nums = values
    .map((value) => parseProjectionNumber(value))
    .filter((item): item is number => item != null);
  if (nums.length === 0) {
    if (aggregation === "first" && values.length > 0) {
      return parseProjectionNumber(values[0]);
    }
    return null;
  }

  switch (aggregation) {
    case "sum":
      return nums.reduce((acc, item) => acc + item, 0);
    case "avg":
      return nums.reduce((acc, item) => acc + item, 0) / nums.length;
    case "min":
      return Math.min(...nums);
    case "max":
      return Math.max(...nums);
    case "first":
    default:
      return nums[0] ?? null;
  }
}

export type ProjectedFieldResolution = {
  kind: "scalar" | "list" | "empty";
  values: unknown[];
  scalar?: unknown;
};

export function resolveProjectedField(
  resolved: ProjectionResolvedLike | undefined,
  field: string,
  aggregation: ViewAggregation = "first",
): ProjectedFieldResolution {
  const values = extractProjectionFieldValues(resolved, field);
  if (values.length === 0) return { kind: "empty", values: [] };

  if (aggregation === "list") {
    return { kind: "list", values };
  }

  if (aggregation === "count") {
    return { kind: "scalar", values, scalar: values.length };
  }

  if (isNumericAggregation(aggregation)) {
    const aggregated = aggregateProjectionValues(values, aggregation);
    if (aggregated != null) return { kind: "scalar", values, scalar: aggregated };
    return { kind: "empty", values };
  }

  const aggregated = aggregateProjectionValues(values, "first");
  if (aggregated != null) return { kind: "scalar", values, scalar: aggregated };
  return { kind: "scalar", values, scalar: values[0] };
}

export function suggestPreferredProjectionField(
  resolved: ProjectionResolvedLike | undefined,
  fields: Array<{ field: string; label: string }>,
): string | undefined {
  if (!fields.length) return undefined;

  let bestSeries: string | undefined;
  let bestNumeric: string | undefined;
  let bestPopulated: string | undefined;

  for (const option of fields) {
    const values = extractProjectionFieldValues(resolved, option.field);
    if (values.length === 0) continue;
    if (!bestPopulated) bestPopulated = option.field;
    const numericValues = values.filter((value) => parseProjectionNumber(value) != null);
    if (numericValues.length === 0) continue;
    if (!bestNumeric) bestNumeric = option.field;
    if (numericValues.length > 1 && !bestSeries) bestSeries = option.field;
  }

  return bestSeries ?? bestNumeric ?? bestPopulated ?? fields[0]?.field;
}

export function suggestDefaultAggregationForField(
  resolved: ProjectionResolvedLike | undefined,
  field: string,
): ViewAggregation {
  const values = extractProjectionFieldValues(resolved, field);
  const numericCount = values.filter((value) => parseProjectionNumber(value) != null).length;
  if (numericCount > 1) return "avg";
  return "first";
}
