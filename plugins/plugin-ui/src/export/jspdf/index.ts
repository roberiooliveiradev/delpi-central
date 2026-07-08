/**
 * Motor jsPDF / autoTable para exportação de apontamentos e documentos seccionados.
 * Peer opcional: `jspdf` + `jspdf-autotable`. Separado do PDF DELPI (print HTML).
 */

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
} from "./exportDocument";
