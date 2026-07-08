import {
  exportPayloadToCsv,
  exportPayloadToXlsx,
  exportPayloadsToCsv,
  exportPayloadsToXlsx,
  exportTableFormat,
  type ExportPdfOptions,
} from "./exportUtils";
import { sanitizeFilename } from "./primitives";
import type { ExportColumn, TableExportPayload, TabularExportFormat } from "./types";

/** Remove extensão conhecida quando o caller passa `nome.csv` / `nome.xlsx`. */
export function stripExportFilenameExtension(name: string): string {
  return name.replace(/\.(csv|xlsx|xls|pdf|png)$/i, "");
}

function resolveExportBasename(filename: string | undefined, fallbackTitle: string): string {
  const raw = filename?.trim() || fallbackTitle;
  return sanitizeFilename(stripExportFilenameExtension(raw));
}

/** Tabela no formato matrix (headers + rows) usado por `exportDocument` / OEE. */
export type MatrixExportTable = {
  title: string;
  sheetName?: string;
  headers: string[];
  rows: (string | number)[][];
};

/**
 * Converte `ExportTable` (headers/rows) → `TableExportPayload` (columns/rows Record).
 * Permite reutilizar `exportTableFormat` / multi-sheet XLSX do motor shared.
 */
export function tableExportPayloadFromMatrix(table: MatrixExportTable): TableExportPayload {
  const columns: ExportColumn[] = table.headers.map((label, index) => ({
    key: `c${index}`,
    label,
  }));

  const rows = table.rows.map((row) => {
    const record: Record<string, unknown> = {};
    columns.forEach((column, index) => {
      record[column.key] = row[index] ?? "";
    });
    return record;
  });

  return {
    title: table.sheetName?.trim() || table.title,
    columns,
    rows,
  };
}

export function tableExportPayloadsFromMatrix(
  tables: readonly MatrixExportTable[],
): TableExportPayload[] {
  return tables.map(tableExportPayloadFromMatrix);
}

/**
 * Excel a partir de matrix — filename opcional (com ou sem extensão).
 * Sheet name = título da tabela; arquivo usa `filename` quando informado.
 */
export function exportMatrixToXlsx(table: MatrixExportTable, filename?: string): void {
  const payload = tableExportPayloadFromMatrix(table);
  exportPayloadToXlsx(payload, {
    filename: filename?.trim()
      ? resolveExportBasename(filename, payload.title)
      : undefined,
  });
}

export function exportMatrixToCsv(table: MatrixExportTable, filename?: string): void {
  const payload = tableExportPayloadFromMatrix(table);
  const titled = {
    ...payload,
    title: resolveExportBasename(filename, payload.title),
  };
  exportPayloadToCsv(titled);
}

export function exportMatrixTableFormat(
  table: MatrixExportTable,
  format: TabularExportFormat,
  options?: ExportPdfOptions & { filename?: string },
): void {
  const payload = tableExportPayloadFromMatrix(table);
  if (format === "xlsx") {
    exportPayloadToXlsx(payload, {
      filename: options?.filename?.trim()
        ? resolveExportBasename(options.filename, payload.title)
        : undefined,
    });
    return;
  }
  if (format === "csv") {
    exportMatrixToCsv(table, options?.filename);
    return;
  }
  exportTableFormat(payload, format, options);
}

export function exportMatrixesToXlsx(title: string, tables: readonly MatrixExportTable[]): void {
  exportPayloadsToXlsx(title, tableExportPayloadsFromMatrix(tables));
}

export function exportMatrixesToCsv(title: string, tables: readonly MatrixExportTable[]): void {
  exportPayloadsToCsv(title, tableExportPayloadsFromMatrix(tables));
}
