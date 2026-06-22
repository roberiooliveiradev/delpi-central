import type { ChatPresentation } from "../data/api/chatTypes";
import type { DrawingAnalysisExportPayload } from "../ui/utils/drawingAnalysisExport";

/** Formatos tabulares da apresentação rica (tabela, gráfico, KPI, árvore, dashboard). */
export type TabularExportFormat = "csv" | "xlsx" | "pdf";

/** Formatos do relatório de análise de desenho. */
export type DrawingExportFormat = "pdf" | "markdown" | "csv" | "xlsx";

export type ExportFormat = TabularExportFormat | DrawingExportFormat | "png";

export type ExportAction = {
  format: ExportFormat;
  label: string;
  title: string;
};

export const PRESENTATION_EXPORT_ACTIONS: ReadonlyArray<ExportAction & { format: TabularExportFormat }> = [
  { format: "csv", label: "↓ CSV", title: "Baixar CSV" },
  { format: "xlsx", label: "↓ Excel", title: "Baixar Excel" },
  { format: "pdf", label: "↓ PDF", title: "Baixar PDF" },
];

export type PresentationExportOptions = {
  tableRows?: Record<string, unknown>[];
  chartRoot?: HTMLElement | null;
};

export type ChatExportRequest =
  | {
      kind: "presentation";
      presentation: ChatPresentation;
      format: TabularExportFormat;
      options?: PresentationExportOptions;
    }
  | {
      kind: "drawing";
      payload: DrawingAnalysisExportPayload;
      format: DrawingExportFormat;
      drawingAnalysis?: Record<string, unknown>;
    }
  | {
      kind: "chart-png";
      chartRoot: HTMLElement | null;
      title: string;
    }
  | {
      kind: "blob";
      blob: Blob;
      filename: string;
    };

export type ExportColumn = { key: string; label: string };

export type TableExportPayload = {
  title: string;
  columns: ExportColumn[];
  rows: Record<string, unknown>[];
};
