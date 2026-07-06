export function sanitizeFilename(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9À-ÿ\s_-]/g, "")
    .replace(/\s+/g, "_")
    .slice(0, 60);
}

export function sanitizeSheetName(name: string): string {
  const cleaned = name
    .replace(/[\\/?*[\]:]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const base = cleaned || "Dados";
  return base.length <= 31 ? base : `${base.slice(0, 28).trimEnd()}...`;
}

export type ExportTable = {
  title: string;
  sheetName?: string;
  headers: string[];
  rows: (string | number)[][];
};

function columnWidths(headers: string[], rows: (string | number)[][]): { wch: number }[] {
  return headers.map((header, columnIndex) => {
    const maxLen = Math.max(
      header.length,
      ...rows.map((row) => String(row[columnIndex] ?? "").length),
    );
    return { wch: Math.min(maxLen + 2, 48) };
  });
}

export async function exportTableExcel(table: ExportTable, filename: string): Promise<void> {
  const XLSX = await import("xlsx");
  const rows = table.rows.map((row) => row.map((cell) => cell ?? ""));
  const worksheet = XLSX.utils.aoa_to_sheet([table.headers, ...rows]);
  worksheet["!cols"] = columnWidths(table.headers, rows);

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sanitizeSheetName(table.sheetName ?? table.title));
  XLSX.writeFile(workbook, `${sanitizeFilename(filename)}.xlsx`);
}
