/**
 * Contrato tabular compartilhado para exportação CSV / Excel / PDF (DELPI print).
 * Builders de domínio e UI de botões permanecem nos plugins.
 */

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
