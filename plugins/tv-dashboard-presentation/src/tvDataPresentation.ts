import type {
  ComunicadoDataBlock,
  ComunicadoDataDisplayMode,
  ComunicadoDataResolved,
} from "./comunicadoTypes";

export type TvDataTableColumn = {
  key: string;
  label: string;
};

export function resolveEffectiveDisplayMode(block: ComunicadoDataBlock): ComunicadoDataDisplayMode {
  const bindingMode = block.dataBinding.displayMode;
  if (bindingMode && bindingMode !== "auto") {
    return bindingMode;
  }

  if (block.type === "data_chart") return "line_chart";
  if (block.type === "data_table") return "table";
  if (block.type === "data_kpi") return "kpi";

  const resolved = block.resolved;
  if (resolved?.chart?.points?.length) return "line_chart";
  if (resolved?.table?.rows?.length) return "table";
  return "kpi";
}

function metaFieldsToColumns(meta: Record<string, unknown> | undefined): TvDataTableColumn[] {
  const fields = meta?.fields;
  if (!Array.isArray(fields)) return [];
  const columns: TvDataTableColumn[] = [];
  for (const field of fields) {
    if (!field || typeof field !== "object") continue;
    const record = field as Record<string, unknown>;
    const key = String(record.key ?? record.name ?? "").trim();
    if (!key) continue;
    columns.push({
      key,
      label: String(record.label ?? record.title ?? key),
    });
  }
  return columns;
}

export function resolveTableColumns(
  resolved: ComunicadoDataResolved | undefined,
  rows: Array<Record<string, unknown>>,
): TvDataTableColumn[] {
  const explicit = resolved?.table?.columns;
  if (Array.isArray(explicit) && explicit.length > 0) {
    return explicit
      .map((column) => ({
        key: String(column.key ?? "").trim(),
        label: String(column.label ?? column.key ?? ""),
      }))
      .filter((column) => column.key);
  }

  const fromMeta = metaFieldsToColumns(resolved?.meta);
  if (fromMeta.length > 0) {
    return fromMeta;
  }

  const firstRow = rows[0];
  if (!firstRow) return [];
  return Object.keys(firstRow).map((key) => ({ key, label: key }));
}

export function resolveChartType(
  displayMode: ComunicadoDataDisplayMode,
  resolved: ComunicadoDataResolved | undefined,
): "line" | "bar" {
  if (displayMode === "bar_chart") return "bar";
  if (displayMode === "line_chart") return "line";
  return resolved?.chart?.chartType === "bar" ? "bar" : "line";
}
