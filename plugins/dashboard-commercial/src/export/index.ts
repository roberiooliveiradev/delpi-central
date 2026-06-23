/**
 * Exportação centralizada do Dashboard Comercial (CSV, Excel, PDF).
 * Padrão alinhado ao módulo `src/export/` do minha-delpi-chat.
 */

export { runCommercialExport } from "./dispatch";

export {
  triggerFileDownload,
  csvCell,
  buildUtf8CsvBlob,
  sanitizeFilename,
  sanitizeSheetName,
} from "./primitives";

export {
  exportPayloadToCsv,
  exportPayloadToXlsx,
  exportPayloadToPdf,
  exportPayloadsToXlsx,
  exportPayloadsToCsv,
  exportPayloadsToPdf,
  exportTableFormat,
} from "./exportUtils";

export {
  buildTableExportPayloadFromColumns,
  buildDashboardKpisPayload,
  buildRolSeriesPayload,
  buildFunnelPayload,
  buildProposalsPayload,
  buildProductsPayload,
  buildHistoryPayload,
  buildDetailSummaryPayload,
  buildDashboardExportSheets,
  buildDetailExportSheets,
  buildProductStructuresPayload,
} from "./commercialExportBuilders";

export { CommercialExportButtons } from "./CommercialExportButtons";
export type { CommercialExportButtonsProps } from "./CommercialExportButtons";

export type {
  TabularExportFormat,
  ExportAction,
  ExportColumn,
  TableExportPayload,
  DashboardKpiExportRow,
  DashboardExportContext,
  DetailExportContext,
  CommercialExportRequest,
} from "./types";

export { TABULAR_EXPORT_ACTIONS } from "./types";

export {
  buildDelpiDocumentHtml,
  exportChartPayloadToPdf,
  exportTablePayloadToPdf,
  exportTablePayloadsToPdf,
  printDelpiDocumentSpec,
  resolveDelpiLogoUrl,
} from "./pdf";

export {
  exportChartElementToPng,
  rasterizeChartElement,
  resolveChartExportTarget,
  resolveExportContainer,
} from "./chartPngExport";

export type { DelpiDocumentSpec } from "./pdf";
