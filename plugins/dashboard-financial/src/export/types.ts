export type TabularExportFormat = "csv" | "xlsx" | "pdf";

export type ExportAction = {
  format: TabularExportFormat;
  label: string;
  title: string;
};

export const TABULAR_EXPORT_ACTIONS: ReadonlyArray<ExportAction> = [
  { format: "csv", label: "CSV", title: "Baixar CSV" },
  { format: "xlsx", label: "Excel", title: "Baixar Excel" },
  { format: "pdf", label: "PDF", title: "Baixar PDF" },
];

export type ExportColumn = { key: string; label: string };

export type TableExportPayload = {
  title: string;
  columns: ExportColumn[];
  rows: Record<string, unknown>[];
};

export type DashboardKpiExportRow = {
  indicador: string;
  valor: string;
  contexto: string;
};

export type DashboardExportContext = {
  documentTitle: string;
  periodLabel: string;
  scopeLabel: string;
  sheets: TableExportPayload[];
};

export type FinancialExportRequest =
  | {
      kind: "table";
      payload: TableExportPayload;
      format: TabularExportFormat;
    }
  | {
      kind: "dashboard";
      context: DashboardExportContext;
      format: TabularExportFormat;
    };
