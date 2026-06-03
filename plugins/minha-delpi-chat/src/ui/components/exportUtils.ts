import type { ChatPresentation } from "../../data/api/chatTypes";
import { chatAlert } from "../utils/chatNativeDialogs";
import { exportChartElementToPng } from "./chartPngExport";
import { treePresentationToTable } from "./treePresentationUtils";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;
type TreePresentation = Extract<ChatPresentation, { type: "tree" }>;

export function exportToXlsx(presentation: TablePresentation) {
  void import("xlsx")
    .then((XLSX) => {
      const headers = presentation.columns.map((c) => c.label);
      const data = presentation.rows.map((row) =>
        presentation.columns.map((c) => row[c.key] ?? ""),
      );

      const ws = XLSX.utils.aoa_to_sheet([headers, ...data]);

      const colWidths = presentation.columns.map((col) => {
        const maxLen = Math.max(
          col.label.length,
          ...presentation.rows.map((r) => String(r[col.key] ?? "").length),
        );
        return { wch: Math.min(maxLen + 2, 50) };
      });
      ws["!cols"] = colWidths;

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(
        wb,
        ws,
        sanitizeSheetName(presentation.title || "Dados"),
      );
      XLSX.writeFile(wb, `${sanitizeFilename(presentation.title || "dados")}.xlsx`);
    })
    .catch((error) => {
      console.error("[exportToXlsx]", error);
      chatAlert("Não foi possível exportar XLSX. Tente novamente.");
    });
}

export function exportToPdf(presentation: TablePresentation) {
  void Promise.all([import("jspdf"), import("jspdf-autotable")])
    .then(([{ jsPDF }, { autoTable }]) => {
      const doc = new jsPDF({ orientation: "landscape" });

      doc.setFontSize(14);
      doc.text(presentation.title || "Dados", 14, 18);

      const headers = presentation.columns.map((c) => c.label);
      const body = presentation.rows.map((row) =>
        presentation.columns.map((c) => String(row[c.key] ?? "")),
      );

      autoTable(doc, {
        head: [headers],
        body,
        startY: 24,
        styles: { fontSize: 8 },
        headStyles: { fillColor: [14, 165, 233] },
      });

      doc.save(`${sanitizeFilename(presentation.title || "dados")}.pdf`);
    })
    .catch((error) => {
      console.error("[exportToPdf]", error);
      chatAlert("Não foi possível exportar PDF. Tente novamente.");
    });
}

export function exportChartToPng(chartRef: HTMLDivElement | null, title: string) {
  exportChartElementToPng(chartRef, title);
}

export function exportTreeToXlsx(presentation: TreePresentation) {
  exportToXlsx(treePresentationToTable(presentation));
}

export function exportTreeToPdf(presentation: TreePresentation) {
  exportToPdf(treePresentationToTable(presentation));
}

/** Nome de aba Excel: sem \\ / ? * [ ] : e máx. 31 caracteres. */
export function sanitizeSheetName(name: string): string {
  const cleaned = name
    .replace(/[\\/?*[\]:]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const base = cleaned || "Dados";

  return base.length <= 31 ? base : `${base.slice(0, 28).trimEnd()}...`;
}

export function sanitizeFilename(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9À-ÿ\s_-]/g, "")
    .replace(/\s+/g, "_")
    .slice(0, 60);
}
