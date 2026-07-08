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

/** Normaliza texto para jsPDF (fonte padrão não renderiza bem alguns Unicode). */
export function sanitizePdfText(value: string | number | null | undefined): string {
  if (value == null) return "";

  return String(value)
    .replace(/\u2212/g, "-")
    .replace(/[\u2013\u2014]/g, "-")
    .replace(/\u2192/g, "->")
    .replace(/\u00d7/g, "x")
    .replace(/\u2026/g, "...")
    .replace(/\u00a0/g, " ")
    .normalize("NFC")
    .trim();
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

function mapPdfRows(rows: (string | number)[][]): string[][] {
  return rows.map((row) => row.map((cell) => sanitizePdfText(cell)));
}

const PDF_TABLE_MARGIN = { left: 14, right: 14 };

const PDF_TABLE_BODY_STYLES = {
  fontSize: 8,
  cellPadding: 3,
  overflow: "linebreak" as const,
  valign: "top" as const,
};

function escapeCsvCell(value: string | number): string {
  const text = String(value ?? "");
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function exportTableCsv(table: ExportTable, filename: string): void {
  const lines = [
    table.headers.map(escapeCsvCell).join(","),
    ...table.rows.map((row) => row.map((cell) => escapeCsvCell(cell ?? "")).join(",")),
  ];
  const blob = new Blob(["\uFEFF" + lines.join("\r\n")], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${sanitizeFilename(filename)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function exportTableExcel(table: ExportTable, filename: string): Promise<void> {
  const XLSX = await import("xlsx");
  const rows = table.rows.map((row) => row.map((cell) => cell ?? ""));
  const worksheet = XLSX.utils.aoa_to_sheet([table.headers, ...rows]);
  worksheet["!cols"] = columnWidths(table.headers, rows);

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(
    workbook,
    worksheet,
    sanitizeSheetName(table.sheetName ?? table.title),
  );
  XLSX.writeFile(workbook, `${sanitizeFilename(filename)}.xlsx`);
}

export async function exportTablePdf(table: ExportTable, filename: string): Promise<void> {
  const [{ jsPDF }, { default: autoTable }] = await Promise.all([
    import("jspdf"),
    import("jspdf-autotable"),
  ]);

  const doc = new jsPDF({ orientation: "landscape" });
  doc.setFontSize(14);
  doc.text(sanitizePdfText(table.title), PDF_TABLE_MARGIN.left, 18);

  autoTable(doc, {
    head: [table.headers.map(sanitizePdfText)],
    body: mapPdfRows(table.rows),
    startY: 24,
    margin: PDF_TABLE_MARGIN,
    styles: PDF_TABLE_BODY_STYLES,
    headStyles: { fillColor: [14, 165, 233], overflow: "linebreak" as const },
  });

  doc.save(`${sanitizeFilename(filename)}.pdf`);
}
