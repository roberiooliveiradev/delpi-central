import type { ChatMessageMetadata } from "../../data/api/chatTypes";

export type DrawingAnalysisExportPayload = NonNullable<
  ChatMessageMetadata["drawingAnalysisExport"]
>;

type DrawingCheckItem = {
  section?: string;
  item?: string;
  status?: string;
  pdfEvidence?: string;
  apiEvidence?: string;
  recommendation?: string;
};

const STATUS_LABELS: Record<string, string> = {
  ok: "OK",
  pending: "Pendente",
  error: "Erro",
  critical_error: "Erro crítico",
  incomplete: "Incompleto",
};

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function sanitizeFilename(name: string): string {
  return (
    name
      .replace(/[^a-zA-Z0-9À-ÿ\s_-]/g, "")
      .replace(/\s+/g, "_")
      .slice(0, 60) || "relatorio-desenho"
  );
}

function resolveProductCode(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): string {
  const fromAnalysis = drawingAnalysis?.productCode;

  if (fromAnalysis != null && String(fromAnalysis).trim()) {
    return String(fromAnalysis).trim();
  }

  const match = exportPayload.filename?.match(/relatorio-desenho-([a-zA-Z0-9]+)-/);

  return match?.[1] ?? "desenho";
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

export async function downloadDrawingAnalysisPdf(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): Promise<void> {
  const markdown = String(exportPayload.markdown || "").trim();

  if (!markdown && !drawingAnalysis) {
    return;
  }

  try {
    const [{ jsPDF }, { autoTable }] = await Promise.all([
      import("jspdf"),
      import("jspdf-autotable"),
    ]);

    const code = resolveProductCode(exportPayload, drawingAnalysis);
    const overall = String(drawingAnalysis?.overallLabel ?? "—");
    const critical = drawingAnalysis?.criticalErrors;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

    doc.setFontSize(14);
    doc.text("Relatório de Análise de Desenho DELPI", 14, 16);
    doc.setFontSize(10);
    doc.text(`Produto: ${code}`, 14, 24);
    doc.text(`Status: ${overall}`, 14, 30);

    if (critical != null) {
      doc.text(`Erros críticos: ${String(critical)}`, 14, 36);
    }

    let startY = 44;

    const nonConformityRows = exportPayload.spreadsheetRows ?? [];

    if (nonConformityRows.length) {
      doc.setFontSize(11);
      doc.text("Não conformidades", 14, startY);
      startY += 4;

      autoTable(doc, {
        head: [["Seção", "Item", "Status", "PDF", "API", "Ação"]],
        body: nonConformityRows.map((row) => [
          row.section,
          row.item,
          row.status,
          row.pdfEvidence,
          row.apiEvidence,
          row.recommendation,
        ]),
        startY,
        styles: { fontSize: 7, cellPadding: 1.5 },
        headStyles: { fillColor: [14, 165, 233] },
        margin: { left: 14, right: 14 },
      });

      startY = (doc as { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? startY;
      startY += 10;
    }

    const items = (drawingAnalysis?.items as DrawingCheckItem[] | undefined) ?? [];

    if (items.length) {
      if (startY > 250) {
        doc.addPage();
        startY = 16;
      }

      doc.setFontSize(11);
      doc.text("Checklist completo", 14, startY);
      startY += 4;

      autoTable(doc, {
        head: [["Seção", "Item", "Status", "Observação"]],
        body: items.map((item) => [
          String(item.section ?? "—"),
          String(item.item ?? "—"),
          STATUS_LABELS[String(item.status ?? "")] ?? String(item.status ?? "—"),
          String(item.recommendation ?? "—"),
        ]),
        startY,
        styles: { fontSize: 7, cellPadding: 1.5 },
        headStyles: { fillColor: [71, 85, 105] },
        margin: { left: 14, right: 14 },
      });
    } else if (!nonConformityRows.length && markdown) {
      const lines = markdown.split("\n").slice(0, 80);

      doc.setFontSize(9);

      for (const line of lines) {
        if (startY > 280) {
          doc.addPage();
          startY = 16;
        }

        doc.text(line.slice(0, 95), 14, startY);
        startY += 5;
      }
    }

    const filename =
      exportPayload.pdfFilename ||
      `relatorio-desenho-${sanitizeFilename(code)}.pdf`;

    doc.save(filename);
  } catch (error) {
    console.error("[downloadDrawingAnalysisPdf]", error);
    window.alert("Não foi possível exportar PDF. Tente Markdown ou CSV.");
  }
}

/** @deprecated Use downloadDrawingAnalysisMarkdown */
export function downloadDrawingAnalysisExport(
  exportPayload: DrawingAnalysisExportPayload,
): void {
  downloadDrawingAnalysisMarkdown(exportPayload);
}
