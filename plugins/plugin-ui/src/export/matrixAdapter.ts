import type { ExportColumn, TableExportPayload } from "./types";

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
