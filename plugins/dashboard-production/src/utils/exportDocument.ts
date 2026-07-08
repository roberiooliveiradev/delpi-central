/**
 * Reexporta o motor jsPDF / matrix Excel de `@delpi/plugin-ui`.
 * Builders de domínio (OEE, OTD, apontamentos) permanecem locais.
 */
export {
  sanitizeFilename,
  sanitizeSheetName,
  sanitizePdfText,
  exportTableExcel,
  exportTablePdf,
  exportDocumentExcel,
  exportDocumentPdf,
  type ExportTable,
  type ExportFieldSection,
  type ExportTableSection,
  type ExportDocument,
} from "@delpi/plugin-ui";
