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
  doc.text(table.title, 14, 18);

  autoTable(doc, {
    head: [table.headers],
    body: table.rows.map((row) => row.map((cell) => String(cell ?? ""))),
    startY: 24,
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: [14, 165, 233] },
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
  doc.text(document.title, 14, 18);
  let startY = 26;

  for (const section of document.fieldSections) {
    if (startY > 250) {
      doc.addPage();
      startY = 18;
    }

    doc.setFontSize(11);
    doc.text(section.title, 14, startY);
    startY += 6;

    autoTable(doc, {
      head: [["Campo", "Valor"]],
      body: section.rows,
      startY,
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [14, 165, 233] },
    });
    startY = doc.lastAutoTable.finalY + 10;
  }

  for (const section of document.tableSections ?? []) {
    if (startY > 220) {
      doc.addPage();
      startY = 18;
    }

    doc.setFontSize(11);
    doc.text(section.title, 14, startY);
    startY += 6;

    autoTable(doc, {
      head: [section.headers],
      body: section.rows,
      startY,
      styles: { fontSize: 7, cellPadding: 2 },
      headStyles: { fillColor: [14, 165, 233] },
    });
    startY = doc.lastAutoTable.finalY + 10;
  }

  doc.save(`${sanitizeFilename(filename)}.pdf`);
}
