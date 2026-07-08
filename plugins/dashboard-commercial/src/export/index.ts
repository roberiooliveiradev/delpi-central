/**
 * Exportação do Dashboard Comercial (CSV, Excel, PDF).
 * Motor tabular/PDF DELPI: `@delpi/plugin-ui` (ver plugin-ui/docs/export-catalog.md).
 * Builders e botões de domínio permanecem neste módulo.
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

export type { DelpiDocumentSpec } from "./pdf";
