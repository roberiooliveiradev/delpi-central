/**
 * Motor de exportação tabular compartilhado (CSV, Excel, PDF DELPI print).
 *
 * Catálogo: docs/export-catalog.md
 * `xlsx` é carregado sob demanda — o plugin consumidor deve declarar a dependência.
 */

export type {
  TabularExportFormat,
  ExportAction,
  ExportColumn,
  TableExportPayload,
} from "./types";

export { TABULAR_EXPORT_ACTIONS } from "./types";

export {
  triggerBlobDownload,
  triggerFileDownload,
  csvCell,
  buildUtf8CsvBlob,
  sanitizeFilename,
  sanitizeSheetName,
} from "./primitives";

export { exportAlert, configureExportAlert, type ExportAlertFn } from "./exportAlert";

export {
  exportPayloadToCsv,
  exportPayloadToXlsx,
  exportPayloadToPdf,
  exportPayloadsToCsv,
  exportPayloadsToXlsx,
  exportPayloadsToPdf,
  exportTableFormat,
  type ExportPdfOptions,
  type ExportXlsxOptions,
} from "./exportUtils";

export {
  buildDelpiDocumentStyles,
  buildDelpiBrandBarHtml,
  buildDelpiDocumentHtml,
  buildDelpiDocumentTableSection,
  buildDefaultExportSummaryLines,
  escapeDelpiDocumentHtml,
  resolveDelpiLogoUrl,
  printDelpiDocumentHtml,
  printScopedWindow,
  exportChartPayloadToPdf,
  exportTablePayloadToPdf,
  exportTablePayloadsToPdf,
  printDelpiDocumentSpec,
  type ScopedWindowPrintOptions,
} from "./pdf";

export type {
  DelpiDocumentBadgeTone,
  DelpiDocumentColumn,
  DelpiDocumentImageSection,
  DelpiDocumentSpec,
  DelpiDocumentSummaryLine,
  DelpiDocumentTable,
} from "./pdf";

export {
  TabularExportButtons,
  DocumentExportActions,
  ExcelExportButton,
  createDashboardTabularExportButtons,
  documentExportActionsBemClasses,
  type TabularExportButtonsProps,
  type DocumentExportActionsProps,
  type ExcelExportButtonProps,
} from "./ExportButtons";

export {
  tableExportPayloadFromMatrix,
  tableExportPayloadsFromMatrix,
  exportMatrixToXlsx,
  exportMatrixToCsv,
  exportMatrixTableFormat,
  exportMatrixesToXlsx,
  exportMatrixesToCsv,
  stripExportFilenameExtension,
  type MatrixExportTable,
} from "./matrixAdapter";

export { runTabularExport, type TabularExportRequest } from "./runTabularExport";

export {
  sanitizePdfText,
  exportTableExcel,
  exportTablePdf,
  exportDocumentExcel,
  exportDocumentPdf,
  type ExportTable,
  type ExportFieldSection,
  type ExportTableSection,
  type ExportDocument,
} from "./jspdf";

export {
  prepareSvgCloneForRasterExport,
  rasterizeSvgElement,
  exportSvgElementToPng,
  type RasterSvgOptions,
  type ExportSvgPngOptions,
} from "./chartPngExport";
