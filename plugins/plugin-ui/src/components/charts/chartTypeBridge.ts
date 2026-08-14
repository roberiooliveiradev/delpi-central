import type { PersistedChartType } from "../../hooks/usePersistedChartPreferences";
import type { DelpiChartType } from "./chartCatalogTypes";

/**
 * Bridge between MultiTypeSeriesChart preferences (`column`) and the
 * PowerPoint-style catalog (`bar` = Colunas).
 */
export function persistedChartTypeToDelpi(type: PersistedChartType): DelpiChartType {
  if (type === "column") return "bar";
  return type as DelpiChartType;
}

/**
 * Maps a catalog selection back into an allowed persisted type.
 * `bar` (Colunas) → `column` when the family uses `column`, else `bar`.
 */
export function delpiChartTypeToPersisted(
  type: DelpiChartType,
  allowed: readonly PersistedChartType[],
): PersistedChartType | null {
  if (type === "bar") {
    if (allowed.includes("column")) return "column";
    if (allowed.includes("bar")) return "bar";
    return null;
  }
  if ((allowed as readonly string[]).includes(type)) {
    return type as PersistedChartType;
  }
  return null;
}

export function persistedChartTypesToDelpi(
  types: readonly PersistedChartType[],
): DelpiChartType[] {
  const out: DelpiChartType[] = [];
  const seen = new Set<DelpiChartType>();
  for (const type of types) {
    const delpi = persistedChartTypeToDelpi(type);
    if (seen.has(delpi)) continue;
    seen.add(delpi);
    out.push(delpi);
  }
  return out;
}
