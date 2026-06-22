import type { DrawingAnalysisExportPayload } from "../ui/utils/drawingAnalysisExport";
import {
  downloadDrawingAnalysisCsv,
  downloadDrawingAnalysisMarkdown,
  downloadDrawingAnalysisPdf,
  downloadDrawingAnalysisXlsx,
} from "../ui/utils/drawingAnalysisExport";
import { exportPresentation } from "../ui/components/presentation/export/exportUtils";
import { exportChartElementToPng } from "../ui/components/presentation/export/chartPngExport";
import { triggerFileDownload } from "./primitives";
import type {
  ChatExportRequest,
  DrawingExportFormat,
  ExportAction,
  TabularExportFormat,
} from "./types";

export function runChatExport(request: ChatExportRequest): void {
  switch (request.kind) {
    case "presentation":
      exportPresentation(request.presentation, request.format, request.options);
      return;
    case "drawing":
      runDrawingExport(request.payload, request.format, request.drawingAnalysis);
      return;
    case "chart-png":
      exportChartElementToPng(request.chartRoot, request.title);
      return;
    case "blob":
      triggerFileDownload(request.blob, request.filename);
      return;
    default: {
      const _exhaustive: never = request;
      return _exhaustive;
    }
  }
}

function runDrawingExport(
  payload: DrawingAnalysisExportPayload,
  format: DrawingExportFormat,
  drawingAnalysis?: Record<string, unknown>,
): void {
  switch (format) {
    case "pdf":
      void downloadDrawingAnalysisPdf(payload, drawingAnalysis);
      return;
    case "markdown":
      downloadDrawingAnalysisMarkdown(payload);
      return;
    case "csv":
      downloadDrawingAnalysisCsv(payload, drawingAnalysis);
      return;
    case "xlsx":
      void downloadDrawingAnalysisXlsx(payload, drawingAnalysis);
      return;
    default: {
      const _exhaustive: never = format;
      return _exhaustive;
    }
  }
}

export function resolveDrawingExportActions(
  payload: DrawingAnalysisExportPayload,
): ExportAction[] {
  const actions: ExportAction[] = [];

  if (String(payload.markdown || "").trim()) {
    actions.push(
      { format: "pdf", label: "PDF", title: "Exportar relatório (.pdf)" },
      { format: "markdown", label: "MD", title: "Baixar relatório (.md)" },
    );
  }

  const hasCsv =
    Boolean(String(payload.csv || "").trim()) ||
    (payload.tables?.length ?? 0) > 0;

  if (hasCsv) {
    actions.push({ format: "csv", label: "CSV", title: "Baixar tabelas (.csv)" });
  }

  const hasXlsx =
    (payload.tables?.length ?? 0) > 0 ||
    (payload.spreadsheetRows?.length ?? 0) > 0;

  if (hasXlsx) {
    actions.push({ format: "xlsx", label: "XLSX", title: "Baixar tabelas (.xlsx)" });
  }

  return actions;
}

export function isTabularExportFormat(format: string): format is TabularExportFormat {
  return format === "csv" || format === "xlsx" || format === "pdf";
}

export function isDrawingExportFormat(format: string): format is DrawingExportFormat {
  return format === "pdf" || format === "markdown" || format === "csv" || format === "xlsx";
}
