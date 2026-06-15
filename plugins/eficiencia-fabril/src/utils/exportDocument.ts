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

export type ExportFieldSection = {
  title: string;
  rows: [string, string][];
};

export type ExportTableSection = {
  title: string;
  headers: string[];
  rows: string[][];
};

export type ExportDocument = {
  title: string;
  fieldSections: ExportFieldSection[];
  tableSections?: ExportTableSection[];
};

function columnWidths(headers: string[], rows: (string | number)[][]): { wch: number }[] {
  return headers.map((header, columnIndex) => {
    const maxLen = Math.max(
      header.length,
      ...rows.map((row) => String(row[columnIndex] ?? "").length)
    );
    return { wch: Math.min(maxLen + 2, 48) };
  });
}

function mapPdfRows(rows: (string | number)[][]): string[][] {
  return rows.map((row) => row.map((cell) => sanitizePdfText(cell)));
}

function mapPdfFieldRows(rows: [string, string][]): string[][] {
  return rows.map(([label, value]) => [sanitizePdfText(label), sanitizePdfText(value)]);
}

const PDF_TABLE_MARGIN = { left: 14, right: 14 };
const PDF_FIELD_LABEL_WIDTH = 52;
const PDF_FIELD_VALUE_WIDTH = 122;

const PDF_TABLE_BODY_STYLES = {
  fontSize: 8,
  cellPadding: 3,
  overflow: "linebreak" as const,
  valign: "top" as const,
};

const PDF_FIELD_COLUMN_STYLES = {
  0: { cellWidth: PDF_FIELD_LABEL_WIDTH, overflow: "linebreak" as const },
  1: { cellWidth: PDF_FIELD_VALUE_WIDTH, overflow: "linebreak" as const },
};

export async function exportTableExcel(table: ExportTable, filename: string): Promise<void> {
  const XLSX = await import("xlsx");
  const rows = table.rows.map((row) => row.map((cell) => cell ?? ""));
  const worksheet = XLSX.utils.aoa_to_sheet([table.headers, ...rows]);
  worksheet["!cols"] = columnWidths(table.headers, rows);

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sanitizeSheetName(table.sheetName ?? table.title));
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

export async function exportDocumentExcel(
  document: ExportDocument,
  filename: string
): Promise<void> {
  const XLSX = await import("xlsx");
  const workbook = XLSX.utils.book_new();

  for (const section of document.fieldSections) {
    const rows = section.rows.map(([label, value]) => [label, value]);
    const worksheet = XLSX.utils.aoa_to_sheet([["Campo", "Valor"], ...rows]);
    worksheet["!cols"] = columnWidths(["Campo", "Valor"], rows);
    XLSX.utils.book_append_sheet(workbook, worksheet, sanitizeSheetName(section.title));
  }

  for (const section of document.tableSections ?? []) {
    const worksheet = XLSX.utils.aoa_to_sheet([section.headers, ...section.rows]);
    worksheet["!cols"] = columnWidths(section.headers, section.rows);
    XLSX.utils.book_append_sheet(workbook, worksheet, sanitizeSheetName(section.title));
  }

  XLSX.writeFile(workbook, `${sanitizeFilename(filename)}.xlsx`);
}

type JsPdfWithAutoTable = import("jspdf").jsPDF & {
  lastAutoTable: { finalY: number };
};

function renderFieldSection(
  doc: JsPdfWithAutoTable,
  autoTable: typeof import("jspdf-autotable").default,
  section: ExportFieldSection,
  startY: number
): number {
  doc.setFontSize(11);
  doc.text(sanitizePdfText(section.title), PDF_TABLE_MARGIN.left, startY);
  const tableStartY = startY + 6;

  autoTable(doc, {
    head: [["Campo", "Valor"]],
    body: mapPdfFieldRows(section.rows),
    startY: tableStartY,
    margin: PDF_TABLE_MARGIN,
    tableWidth: PDF_FIELD_LABEL_WIDTH + PDF_FIELD_VALUE_WIDTH,
    styles: PDF_TABLE_BODY_STYLES,
    columnStyles: PDF_FIELD_COLUMN_STYLES,
    headStyles: { fillColor: [14, 165, 233], overflow: "linebreak" as const },
  });

  return doc.lastAutoTable.finalY + 10;
}

function renderTableSection(
  doc: JsPdfWithAutoTable,
  autoTable: typeof import("jspdf-autotable").default,
  section: ExportTableSection,
  landscape: boolean
): void {
  doc.addPage("a4", landscape ? "landscape" : "portrait");
  let startY = 18;

  doc.setFontSize(11);
  doc.text(sanitizePdfText(section.title), PDF_TABLE_MARGIN.left, startY);
  startY += 6;

  autoTable(doc, {
    head: [section.headers.map(sanitizePdfText)],
    body: mapPdfRows(section.rows),
    startY,
    margin: PDF_TABLE_MARGIN,
    styles: { ...PDF_TABLE_BODY_STYLES, fontSize: landscape ? 7 : 8 },
    headStyles: { fillColor: [14, 165, 233], overflow: "linebreak" as const },
  });
}

export async function exportDocumentPdf(
  document: ExportDocument,
  filename: string
): Promise<void> {
  const [{ jsPDF }, { default: autoTable }] = await Promise.all([
    import("jspdf"),
    import("jspdf-autotable"),
  ]);

  const doc = new jsPDF({ orientation: "portrait" }) as JsPdfWithAutoTable;
  doc.setFontSize(14);
  doc.text(sanitizePdfText(document.title), PDF_TABLE_MARGIN.left, 18);
  let startY = 26;

  for (const section of document.fieldSections) {
    if (startY > 240) {
      doc.addPage();
      startY = 18;
    }
    startY = renderFieldSection(doc, autoTable, section, startY);
  }

  const tableSections = document.tableSections ?? [];
  for (let index = 0; index < tableSections.length; index += 1) {
    renderTableSection(doc, autoTable, tableSections[index], true);
  }

  doc.save(`${sanitizeFilename(filename)}.pdf`);
}
