export type ExcelColumn = { key: string; label: string };

export type ExcelPayload = {
  title: string;
  columns: ExcelColumn[];
  rows: Record<string, string | number>[];
};

function sanitizeFileBase(name: string): string {
  return name.replace(/\.xlsx$/i, "").replace(/[\\/:*?"<>|]+/g, "_").trim() || "export";
}

export async function downloadExcel(payload: ExcelPayload, fileName: string): Promise<void> {
  if (typeof document === "undefined") return;
  if (!payload.columns.length || payload.rows.length === 0) return;

  const XLSX = await import("xlsx");
  const headers = payload.columns.map((column) => column.label);
  const data = payload.rows.map((row) =>
    payload.columns.map((column) => row[column.key] ?? ""),
  );
  const worksheet = XLSX.utils.aoa_to_sheet([headers, ...data]);
  worksheet["!cols"] = payload.columns.map((column) => {
    const maxLen = Math.max(
      column.label.length,
      ...payload.rows.map((row) => String(row[column.key] ?? "").length),
    );
    return { wch: Math.min(maxLen + 2, 50) };
  });
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, payload.title.slice(0, 31));
  XLSX.writeFile(workbook, `${sanitizeFileBase(fileName)}.xlsx`);
}
