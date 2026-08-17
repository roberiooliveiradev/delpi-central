import type { DisplayFormatSpec } from "./types";

export type LegacyChartValueFormat =
  | "auto"
  | "number"
  | "currency"
  | "currency4"
  | "percent"
  | "compact";

export type LegacyCategoryLabelFormat = "raw" | "autoDate" | "day" | "month" | "year";

export type LegacyTableValueFormat = "auto" | "number" | "currency" | "percent";

export type LegacyKpiValueFormat = "number" | "percent" | "compact" | "raw" | "currency";

export type LegacyCanvasNumberFormat = "plain" | "integer" | "decimal" | "percent" | "currency";

export type LegacyTextProjectionFormat =
  | "number"
  | "percent"
  | "currency"
  | "compact"
  | "raw"
  | "date";

/** Leitura: spec explícito ganha; senão deriva do enum legado. */
export function resolveDisplayFormatSpec(
  spec: DisplayFormatSpec | null | undefined,
  fallback: DisplayFormatSpec,
): DisplayFormatSpec {
  if (spec?.category) return spec;
  return fallback;
}

export function specFromChartValueFormat(
  format?: LegacyChartValueFormat | null,
  decimalPlaces?: number | null,
): DisplayFormatSpec {
  switch (format) {
    case "number":
      return typeof decimalPlaces === "number"
        ? { category: "number", decimalPlaces }
        : { category: "number" };
    case "currency":
      return { category: "currency", presetId: "currency-brl", currency: "BRL", decimalPlaces: decimalPlaces ?? 2 };
    case "currency4":
      return { category: "currency", presetId: "currency-brl-4", currency: "BRL", decimalPlaces: decimalPlaces ?? 4 };
    case "percent":
      return { category: "percent", presetId: "percent", decimalPlaces: decimalPlaces ?? 1 };
    case "compact":
      return { category: "number", presetId: "number-compact", decimalPlaces: decimalPlaces ?? 1 };
    default:
      return {
        category: "general",
        presetId: "general",
        decimalPlaces: decimalPlaces ?? null,
      };
  }
}

export function specFromCategoryLabelFormat(
  format?: LegacyCategoryLabelFormat | null,
): DisplayFormatSpec {
  switch (format) {
    case "day":
      return { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" };
    case "month":
      return { category: "date", presetId: "date-month" };
    case "year":
      return { category: "date", presetId: "date-year" };
    case "autoDate":
      return { category: "date", presetId: "date-auto" };
    default:
      return { category: "text", presetId: "text" };
  }
}

export function specFromTableValueFormat(format?: LegacyTableValueFormat | null): DisplayFormatSpec {
  return specFromChartValueFormat(
    format === "auto" ? "auto" : format === "number" ? "number" : format === "currency" ? "currency" : format === "percent" ? "percent" : "auto",
  );
}

export function specFromKpiValueFormat(
  format?: LegacyKpiValueFormat | null,
  decimalPlaces?: number | null,
): DisplayFormatSpec {
  if (format === "raw") return { category: "text", presetId: "text" };
  return specFromChartValueFormat(
    format === "compact" ? "compact" : format === "percent" ? "percent" : format === "currency" ? "currency" : "number",
    decimalPlaces,
  );
}

export function specFromCanvasNumberFormat(format?: LegacyCanvasNumberFormat | null): DisplayFormatSpec {
  switch (format) {
    case "integer":
      return { category: "number", presetId: "number-0", decimalPlaces: 0 };
    case "percent":
      return { category: "percent", presetId: "percent", decimalPlaces: 1 };
    case "currency":
      return { category: "currency", presetId: "currency-brl", currency: "BRL", decimalPlaces: 2 };
    case "plain":
      return { category: "text", presetId: "text" };
    case "decimal":
    default:
      /* Histórico: max 2 casas, sem zeros à direita (12,5 ≠ 12,50). */
      return { category: "number" };
  }
}

export function specFromTextProjectionFormat(
  format?: LegacyTextProjectionFormat | null,
  decimalPlaces?: number | null,
): DisplayFormatSpec {
  if (format === "date") return { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" };
  if (format === "raw" || format == null) return { category: "text", presetId: "text" };
  return specFromKpiValueFormat(format, decimalPlaces);
}

/** Gravação: spec → espelho legado (nunca o contrário). */
export function chartValueFormatFromSpec(spec: DisplayFormatSpec): {
  valueFormat: LegacyChartValueFormat;
  decimalPlaces: number | null;
} {
  if (spec.category === "percent") {
    return { valueFormat: "percent", decimalPlaces: spec.decimalPlaces ?? 1 };
  }
  if (spec.category === "currency" || spec.category === "accounting") {
    if (spec.presetId === "currency-brl-4" || spec.decimalPlaces === 4) {
      return { valueFormat: "currency4", decimalPlaces: spec.decimalPlaces ?? 4 };
    }
    return { valueFormat: "currency", decimalPlaces: spec.decimalPlaces ?? 2 };
  }
  if (spec.presetId === "number-compact") {
    return { valueFormat: "compact", decimalPlaces: spec.decimalPlaces ?? 1 };
  }
  if (spec.category === "number") {
    return { valueFormat: "number", decimalPlaces: spec.decimalPlaces ?? 2 };
  }
  if (spec.category === "general") {
    return { valueFormat: "auto", decimalPlaces: spec.decimalPlaces ?? null };
  }
  return { valueFormat: "auto", decimalPlaces: spec.decimalPlaces ?? null };
}

export function categoryLabelFormatFromSpec(spec: DisplayFormatSpec): LegacyCategoryLabelFormat {
  if (spec.category === "text" || spec.presetId === "text") return "raw";
  if (spec.presetId === "date-auto") return "autoDate";
  if (spec.presetId === "date-month") return "month";
  if (spec.presetId === "date-year") return "year";
  if (spec.category === "date") return "day";
  return "raw";
}

export function tableValueFormatFromSpec(spec: DisplayFormatSpec): LegacyTableValueFormat {
  const { valueFormat } = chartValueFormatFromSpec(spec);
  if (valueFormat === "currency" || valueFormat === "currency4") return "currency";
  if (valueFormat === "percent") return "percent";
  if (valueFormat === "number" || valueFormat === "compact") return "number";
  return "auto";
}

export function kpiValueFormatFromSpec(spec: DisplayFormatSpec): LegacyKpiValueFormat {
  if (spec.category === "text") return "raw";
  const { valueFormat } = chartValueFormatFromSpec(spec);
  if (valueFormat === "currency4") return "currency";
  if (valueFormat === "auto") return "number";
  return valueFormat;
}

export function canvasNumberFormatFromSpec(spec: DisplayFormatSpec): LegacyCanvasNumberFormat {
  if (spec.category === "text") return "plain";
  if (spec.category === "percent") return "percent";
  if (spec.category === "currency" || spec.category === "accounting") return "currency";
  if (spec.presetId === "number-0" || spec.decimalPlaces === 0) return "integer";
  return "decimal";
}

export function textProjectionFormatFromSpec(spec: DisplayFormatSpec): {
  format: LegacyTextProjectionFormat;
  decimalPlaces?: number;
} {
  if (spec.category === "date" || spec.category === "time") {
    return { format: "date" };
  }
  if (spec.category === "text") {
    return { format: "raw" };
  }
  if (spec.category === "general") {
    return {
      format: "raw",
      ...(typeof spec.decimalPlaces === "number" ? { decimalPlaces: spec.decimalPlaces } : {}),
    };
  }
  const kpi = kpiValueFormatFromSpec(spec);
  const out: { format: LegacyTextProjectionFormat; decimalPlaces?: number } = {
    format: kpi === "raw" ? "raw" : kpi,
  };
  if (typeof spec.decimalPlaces === "number") out.decimalPlaces = spec.decimalPlaces;
  return out;
}
