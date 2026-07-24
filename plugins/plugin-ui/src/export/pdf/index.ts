export type {
  DelpiDocumentBadgeTone,
  DelpiDocumentColumn,
  DelpiDocumentImageSection,
  DelpiDocumentSpec,
  DelpiDocumentSummaryLine,
  DelpiDocumentTable,
} from "./types";

export { buildDelpiDocumentStyles, buildDelpiBrandBarHtml } from "./delpiDocumentStyles";

export {
  buildDelpiDocumentHtml,
  buildDelpiDocumentTableSection,
  buildDefaultExportSummaryLines,
  escapeDelpiDocumentHtml,
  resolveDelpiLogoUrl,
} from "./delpiDocumentHtml";

export { printDelpiDocumentHtml } from "./delpiDocumentPrint";
export { printScopedWindow, type ScopedWindowPrintOptions } from "./printOnce";

export {
  exportChartPayloadToPdf,
  exportTablePayloadToPdf,
  exportTablePayloadsToPdf,
  printDelpiDocumentSpec,
} from "./tablePdfExport";
