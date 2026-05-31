import type { ChatMessageMetadata } from "../../data/api/chatTypes";

export type DrawingAnalysisExportPayload = NonNullable<
  ChatMessageMetadata["drawingAnalysisExport"]
>;

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function downloadDrawingAnalysisMarkdown(
  exportPayload: DrawingAnalysisExportPayload,
): void {
  const markdown = String(exportPayload.markdown || "").trim();

  if (!markdown) {
    return;
  }

  triggerDownload(
    new Blob([markdown], {
      type: exportPayload.mimeType || "text/markdown;charset=utf-8",
    }),
    exportPayload.filename || "relatorio-desenho.md",
  );
}

export function downloadDrawingAnalysisCsv(
  exportPayload: DrawingAnalysisExportPayload,
): void {
  const csv = String(exportPayload.csv || "").trim();

  if (!csv) {
    return;
  }

  triggerDownload(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
    exportPayload.csvFilename || "nao-conformidades.csv",
  );
}

export async function downloadDrawingAnalysisXlsx(
  exportPayload: DrawingAnalysisExportPayload,
): Promise<void> {
  const rows = exportPayload.spreadsheetRows ?? [];

  if (!rows.length) {
    return;
  }

  try {
    const XLSX = await import("xlsx");
    const headers = [
      "Seção",
      "Item",
      "Status",
      "Evidência PDF",
      "Evidência API",
      "Recomendação",
    ];
    const data = rows.map((row) => [
      row.section,
      row.item,
      row.status,
      row.pdfEvidence,
      row.apiEvidence,
      row.recommendation,
    ]);
    const worksheet = XLSX.utils.aoa_to_sheet([headers, ...data]);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Não conformidades");
    const code =
      exportPayload.csvFilename?.replace(/^nao-conformidades-/, "").replace(/\.csv$/, "") ||
      "desenho";
    XLSX.writeFile(workbook, `nao-conformidades-${code}.xlsx`);
  } catch {
    window.alert("Não foi possível exportar XLSX. Tente o CSV ou Markdown.");
  }
}

/** @deprecated Use downloadDrawingAnalysisMarkdown */
export function downloadDrawingAnalysisExport(
  exportPayload: DrawingAnalysisExportPayload,
): void {
  downloadDrawingAnalysisMarkdown(exportPayload);
}
