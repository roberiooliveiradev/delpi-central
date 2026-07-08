/**
 * Reexporta motor tabular + jsPDF de `@delpi/plugin-ui`.
 * CSV canônico usa `;` (paridade Excel / demais plugins).
 */
export {
  sanitizeFilename,
  sanitizeSheetName,
  sanitizePdfText,
  exportTableExcel,
  exportTablePdf,
  type ExportTable,
} from "@delpi/plugin-ui";

import { exportMatrixToCsv, type ExportTable } from "@delpi/plugin-ui";

export function exportTableCsv(table: ExportTable, filename: string): void {
  exportMatrixToCsv(table, filename);
}
