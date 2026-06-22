/**
 * Módulo centralizado de exportação do chat (CSV, Excel, PDF, PNG, Markdown).
 * Ponto único para UI e dispatch — apresentação rica, relatório de desenho e blobs.
 */

export {
  runChatExport,
  resolveDrawingExportActions,
  isTabularExportFormat,
  isDrawingExportFormat,
} from "./dispatch";

export {
  triggerFileDownload,
  csvCell,
  csvRow,
  buildUtf8CsvBlob,
  sanitizeFilename,
  sanitizeSheetName,
} from "./primitives";

export {
  ChatExportButtons,
  ChatPresentationExportButtons,
  ChatDrawingExportButtons,
} from "./ChatExportButtons";
export type { ChatExportButtonsProps } from "./ChatExportButtons";

export type {
  TabularExportFormat,
  DrawingExportFormat,
  ExportFormat,
  ExportAction,
  PresentationExportOptions,
  ChatExportRequest,
  ExportColumn,
  TableExportPayload,
} from "./types";

export { PRESENTATION_EXPORT_ACTIONS } from "./types";

export {
  exportPresentation,
  buildChartExportPayload,
  buildKpiExportPayload,
  buildTableExportPayload,
  exportPayloadToCsv,
  exportPayloadToXlsx,
  exportPayloadToPdf,
} from "../ui/components/presentation/export/exportUtils";

export {
  exportChartElementToPng,
  rasterizeChartElement,
  resolveChartExportTarget,
} from "../ui/components/presentation/export/chartPngExport";

export { presentationToCanvasPayload } from "../ui/components/presentation/export/chartCanvasMarkdown";
export { buildDashboardCsv } from "../ui/components/presentation/export/dashboardExportCsv";

export {
  downloadDrawingAnalysisCsv,
  downloadDrawingAnalysisMarkdown,
  downloadDrawingAnalysisPdf,
  downloadDrawingAnalysisXlsx,
} from "../ui/utils/drawingAnalysisExport";
export type {
  DrawingAnalysisExportPayload,
  DrawingExportTable,
} from "../ui/utils/drawingAnalysisExport";

export {
  buildDelpiDocumentHtml,
  exportTablePayloadToPdf,
  exportTablePayloadsToPdf,
  exportChartPayloadToPdf,
  printDelpiDocumentHtml,
  printDelpiDocumentSpec,
  resolveDelpiLogoUrl,
} from "./pdf";
export type { DelpiDocumentSpec } from "./pdf";

export { parseContentDispositionFilename, triggerBlobDownload } from "../utils/downloadBlob";
