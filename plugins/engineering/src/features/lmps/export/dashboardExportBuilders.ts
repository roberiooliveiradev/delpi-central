import type {
  DashboardExportContext,
  DashboardKpiExportRow,
  TableExportPayload,
} from "./types";

export function buildDashboardKpisPayload(
  rows: DashboardKpiExportRow[],
): TableExportPayload {
  return {
    title: "Indicadores",
    columns: [
      { key: "indicador", label: "Indicador" },
      { key: "valor", label: "Valor" },
      { key: "contexto", label: "Contexto" },
    ],
    rows,
  };
}

export function buildDashboardExportContext(
  base: Pick<DashboardExportContext, "documentTitle" | "periodLabel" | "scopeLabel">,
  kpiRows: DashboardKpiExportRow[],
  extraSheets: TableExportPayload[] = [],
): DashboardExportContext {
  const sheets = [buildDashboardKpisPayload(kpiRows), ...extraSheets].filter(
    (sheet) => sheet.columns.length > 0 && sheet.rows.length >= 0,
  );

  return {
    ...base,
    sheets,
  };
}
