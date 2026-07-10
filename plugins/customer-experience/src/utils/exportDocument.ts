/**
 * Reexporta motor tabular + jsPDF de `@delpi/plugin-ui`.
 * CSV canônico usa `;` (paridade Excel / demais plugins).
 */
import {
  sanitizeFilename,
  sanitizeSheetName,
  sanitizePdfText,
  exportTableExcel,
  exportTablePdf,
  exportMatrixToCsv,
  type ExportTable,
} from "@delpi/plugin-ui/index";

export {
  sanitizeFilename,
  sanitizeSheetName,
  sanitizePdfText,
  exportTableExcel,
  exportTablePdf,
  type ExportTable,
};

export function exportTableCsv(table: ExportTable, filename: string): void {
  exportMatrixToCsv(table, filename);
}
