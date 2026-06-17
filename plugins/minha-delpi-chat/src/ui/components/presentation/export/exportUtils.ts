import type { ChatPresentation } from "../../../../data/api/chatTypes";
import { chatAlert } from "../../../utils/chatNativeDialogs";
import { formatChartColumnLabel } from "../pipeline/chartAxisSelection";
import { rasterizeChartElement } from "./chartPngExport";
import { buildDashboardCsv } from "./dashboardExportCsv";
import { exportTreeToCsv, treePresentationToTable } from "../pipeline/treePresentationUtils";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;
type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;
type TreePresentation = Extract<ChatPresentation, { type: "tree" }>;
type KpiPresentation = Extract<ChatPresentation, { type: "kpi" }>;
type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;

export type ExportColumn = { key: string; label: string };

export type TableExportPayload = {
  title: string;
  columns: ExportColumn[];
  rows: Record<string, unknown>[];
};

function csvCell(value: unknown): string {
  if (value == null) {
    return "";
  }

  const text = String(value);

  if (text.includes(";") || text.includes('"') || text.includes("\n")) {
    return `"${text.replace(/"/g, '""')}"`;
  }

  return text;
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
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

export function buildTableExportPayload(
  presentation: TablePresentation,
  rows?: Record<string, unknown>[],
): TableExportPayload {
  const columns = (presentation.columns ?? []).map((column) => ({
    key: column.key,
    label: column.label,
  }));
  const effectiveRows = rows ?? presentation.rows ?? [];

  return {
    title: presentation.title || "dados",
    columns,
    rows: effectiveRows,
  };
}

export function buildChartExportPayload(
  presentation: ChartPresentation,
): TableExportPayload {
  const data = Array.isArray(presentation.data) ? presentation.data : [];
  const fieldLabels = presentation.config?.fieldLabels ?? {};

  if (!data.length) {
    return {
      title: presentation.title || "grafico",
      columns: [],
      rows: [],
    };
  }

  const keys = Object.keys(data[0] ?? {}).filter(
    (key) => key && !key.startsWith("_"),
  );

  return {
    title: presentation.title || "grafico",
    columns: keys.map((key) => ({
      key,
      label: formatChartColumnLabel(key, fieldLabels),
    })),
    rows: data,
  };
}

export function buildKpiExportPayload(
  presentation: KpiPresentation,
): TableExportPayload {
  return {
    title: presentation.title || "indicadores",
    columns: [
      { key: "label", label: "Indicador" },
      { key: "value", label: "Valor" },
      { key: "unit", label: "Unidade" },
      { key: "delta", label: "Variação" },
      { key: "trend", label: "Tendência" },
    ],
    rows: (presentation.cards ?? []).map((card) => ({
      label: card.label,
      value: card.value,
      unit: card.unit ?? "",
      delta: card.delta ?? "",
      trend: card.trend ?? "",
    })),
  };
}

function buildDashboardExportSheets(
  presentation: DashboardPresentation,
): TableExportPayload[] {
  const sheets: TableExportPayload[] = [];

  for (const panel of presentation.panels ?? []) {
    const panelTitle = panel.title || panel.id || "Painel";
    const inner = panel.presentation;

    if (inner.type === "table") {
      sheets.push({
        title: panelTitle,
        columns: inner.columns.map((column) => ({
          key: column.key,
          label: column.label,
        })),
        rows: inner.rows ?? [],
      });
      continue;
    }

    if (inner.type === "chart") {
      sheets.push(buildChartExportPayload({ ...inner, title: panelTitle }));
      continue;
    }

    if (inner.type === "kpi") {
      sheets.push(buildKpiExportPayload({ ...inner, title: panelTitle }));
    }
  }

  return sheets;
}

export function exportPayloadToCsv(payload: TableExportPayload): void {
  if (!payload.columns.length) {
    chatAlert("Não há dados para exportar em CSV.");
    return;
  }

  const BOM = "\uFEFF";
  const header = payload.columns.map((column) => column.label).join(";");
  const body = payload.rows
    .map((row) =>
      payload.columns.map((column) => csvCell(row[column.key])).join(";"),
    )
    .join("\n");

  triggerDownload(
    new Blob([`${BOM}${header}\n${body}`], { type: "text/csv;charset=utf-8" }),
    `${sanitizeFilename(payload.title)}.csv`,
  );
}

export function exportPayloadToXlsx(payload: TableExportPayload): void {
  if (!payload.columns.length) {
    chatAlert("Não há dados para exportar em Excel.");
    return;
  }

  void import("xlsx")
    .then((XLSX) => {
      const headers = payload.columns.map((column) => column.label);
      const data = payload.rows.map((row) =>
        payload.columns.map((column) => row[column.key] ?? ""),
      );

      const ws = XLSX.utils.aoa_to_sheet([headers, ...data]);
      ws["!cols"] = payload.columns.map((column) => {
        const maxLen = Math.max(
          column.label.length,
          ...payload.rows.map((row) => String(row[column.key] ?? "").length),
        );

        return { wch: Math.min(maxLen + 2, 50) };
      });

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(
        wb,
        ws,
        sanitizeSheetName(payload.title || "Dados"),
      );
      XLSX.writeFile(wb, `${sanitizeFilename(payload.title || "dados")}.xlsx`);
    })
    .catch((error) => {
      console.error("[exportPayloadToXlsx]", error);
      chatAlert("Não foi possível exportar Excel. Tente novamente.");
    });
}

export function exportPayloadToPdf(payload: TableExportPayload): void {
  if (!payload.columns.length) {
    chatAlert("Não há dados para exportar em PDF.");
    return;
  }

  void Promise.all([import("jspdf"), import("jspdf-autotable")])
    .then(([{ jsPDF }, { autoTable }]) => {
      const doc = new jsPDF({ orientation: "landscape" });

      doc.setFontSize(14);
      doc.text(payload.title || "Dados", 14, 18);

      autoTable(doc, {
        head: [payload.columns.map((column) => column.label)],
        body: payload.rows.map((row) =>
          payload.columns.map((column) => String(row[column.key] ?? "")),
        ),
        startY: 24,
        styles: { fontSize: 8 },
        headStyles: { fillColor: [14, 165, 233] },
      });

      doc.save(`${sanitizeFilename(payload.title || "dados")}.pdf`);
    })
    .catch((error) => {
      console.error("[exportPayloadToPdf]", error);
      chatAlert("Não foi possível exportar PDF. Tente novamente.");
    });
}

export function exportToXlsx(presentation: TablePresentation) {
  exportPayloadToXlsx(buildTableExportPayload(presentation));
}

export function exportToPdf(presentation: TablePresentation) {
  exportPayloadToPdf(buildTableExportPayload(presentation));
}

export function exportTablePresentationToCsv(
  presentation: TablePresentation,
  rows?: Record<string, unknown>[],
) {
  exportPayloadToCsv(buildTableExportPayload(presentation, rows));
}

export function exportTablePresentationToXlsx(
  presentation: TablePresentation,
  rows?: Record<string, unknown>[],
) {
  exportPayloadToXlsx(buildTableExportPayload(presentation, rows));
}

export function exportTablePresentationToPdf(
  presentation: TablePresentation,
  rows?: Record<string, unknown>[],
) {
  exportPayloadToPdf(buildTableExportPayload(presentation, rows));
}

export function exportChartPresentationToCsv(presentation: ChartPresentation) {
  exportPayloadToCsv(buildChartExportPayload(presentation));
}

export function exportChartPresentationToXlsx(presentation: ChartPresentation) {
  exportPayloadToXlsx(buildChartExportPayload(presentation));
}

export function exportChartPresentationToPdf(
  presentation: ChartPresentation,
  chartRoot?: HTMLElement | null,
) {
  const payload = buildChartExportPayload(presentation);
  const title = presentation.title || "grafico";

  void rasterizeChartElement(chartRoot ?? null).then((dataUrl) => {
    if (dataUrl) {
      void import("jspdf")
        .then(({ jsPDF }) => {
          const img = new Image();

          img.onload = () => {
            const doc = new jsPDF({ orientation: "landscape" });
            const pageWidth = doc.internal.pageSize.getWidth();
            const margin = 14;
            const maxWidth = pageWidth - margin * 2;
            const ratio = img.height / img.width || 0.5;
            const imageWidth = maxWidth;
            const imageHeight = imageWidth * ratio;

            doc.setFontSize(14);
            doc.text(title, margin, 18);
            doc.addImage(dataUrl, "PNG", margin, 24, imageWidth, imageHeight);
            doc.save(`${sanitizeFilename(title)}.pdf`);
          };

          img.onerror = () => {
            exportPayloadToPdf(payload);
          };

          img.src = dataUrl;
        })
        .catch((error) => {
          console.error("[exportChartPresentationToPdf]", error);
          chatAlert("Não foi possível exportar PDF. Tente novamente.");
        });
      return;
    }

    exportPayloadToPdf(payload);
  });
}

export function exportChartToPng(chartRef: HTMLDivElement | null, title: string) {
  void import("./chartPngExport").then(({ exportChartElementToPng }) => {
    exportChartElementToPng(chartRef, title);
  });
}

export function exportTreeToXlsx(presentation: TreePresentation) {
  exportToXlsx(treePresentationToTable(presentation));
}

export function exportTreeToPdf(presentation: TreePresentation) {
  exportToPdf(treePresentationToTable(presentation));
}

export function exportTreePresentationToCsv(presentation: TreePresentation) {
  exportTreeToCsv(presentation);
}

export function exportKpiPresentationToCsv(presentation: KpiPresentation) {
  exportPayloadToCsv(buildKpiExportPayload(presentation));
}

export function exportKpiPresentationToXlsx(presentation: KpiPresentation) {
  exportPayloadToXlsx(buildKpiExportPayload(presentation));
}

export function exportKpiPresentationToPdf(presentation: KpiPresentation) {
  exportPayloadToPdf(buildKpiExportPayload(presentation));
}

export function exportDashboardToCsv(presentation: DashboardPresentation) {
  const csv = buildDashboardCsv(presentation);
  triggerDownload(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
    `${sanitizeFilename(presentation.title || "dashboard")}.csv`,
  );
}

export function exportDashboardToXlsx(presentation: DashboardPresentation) {
  const sheets = buildDashboardExportSheets(presentation);

  if (!sheets.length) {
    chatAlert("Não há dados para exportar em Excel.");
    return;
  }

  void import("xlsx")
    .then((XLSX) => {
      const wb = XLSX.utils.book_new();
      const usedNames = new Set<string>();

      for (const sheet of sheets) {
        if (!sheet.columns.length) {
          continue;
        }

        let sheetName = sanitizeSheetName(sheet.title);
        let suffix = 2;

        while (usedNames.has(sheetName)) {
          sheetName = sanitizeSheetName(`${sheet.title} ${suffix}`);
          suffix += 1;
        }

        usedNames.add(sheetName);

        const headers = sheet.columns.map((column) => column.label);
        const data = sheet.rows.map((row) =>
          sheet.columns.map((column) => row[column.key] ?? ""),
        );
        const ws = XLSX.utils.aoa_to_sheet([headers, ...data]);
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
      }

      if (!wb.SheetNames.length) {
        chatAlert("Não há dados para exportar em Excel.");
        return;
      }

      XLSX.writeFile(
        wb,
        `${sanitizeFilename(presentation.title || "dashboard")}.xlsx`,
      );
    })
    .catch((error) => {
      console.error("[exportDashboardToXlsx]", error);
      chatAlert("Não foi possível exportar Excel. Tente novamente.");
    });
}

export function exportDashboardToPdf(presentation: DashboardPresentation) {
  const sheets = buildDashboardExportSheets(presentation);

  if (!sheets.length) {
    chatAlert("Não há dados para exportar em PDF.");
    return;
  }

      void Promise.all([import("jspdf"), import("jspdf-autotable")])
    .then(([{ jsPDF }, { autoTable }]) => {
      const doc = new jsPDF({ orientation: "landscape" });
      let cursorY = 18;

      doc.setFontSize(14);
      doc.text(presentation.title || "Dashboard", 14, cursorY);
      cursorY += 10;

      for (const sheet of sheets) {
        if (!sheet.columns.length) {
          continue;
        }

        if (cursorY > doc.internal.pageSize.getHeight() - 30) {
          doc.addPage();
          cursorY = 18;
        }

        doc.setFontSize(11);
        doc.text(sheet.title, 14, cursorY);
        cursorY += 4;

        autoTable(doc, {
          head: [sheet.columns.map((column) => column.label)],
          body: sheet.rows.map((row) =>
            sheet.columns.map((column) => String(row[column.key] ?? "")),
          ),
          startY: cursorY + 2,
          styles: { fontSize: 8 },
          headStyles: { fillColor: [14, 165, 233] },
        });

        const finalY = (
          doc as unknown as { lastAutoTable?: { finalY?: number } }
        ).lastAutoTable?.finalY;

        cursorY = typeof finalY === "number" ? finalY + 12 : cursorY + 24;
      }

      doc.save(`${sanitizeFilename(presentation.title || "dashboard")}.pdf`);
    })
    .catch((error) => {
      console.error("[exportDashboardToPdf]", error);
      chatAlert("Não foi possível exportar PDF. Tente novamente.");
    });
}

export function exportPresentation(
  presentation: ChatPresentation,
  format: "csv" | "xlsx" | "pdf",
  options?: {
    tableRows?: Record<string, unknown>[];
    chartRoot?: HTMLElement | null;
  },
): void {
  switch (presentation.type) {
    case "table":
      if (format === "csv") {
        exportTablePresentationToCsv(presentation, options?.tableRows);
      } else if (format === "xlsx") {
        exportTablePresentationToXlsx(presentation, options?.tableRows);
      } else {
        exportTablePresentationToPdf(presentation, options?.tableRows);
      }
      return;
    case "chart":
      if (format === "csv") {
        exportChartPresentationToCsv(presentation);
      } else if (format === "xlsx") {
        exportChartPresentationToXlsx(presentation);
      } else {
        exportChartPresentationToPdf(presentation, options?.chartRoot);
      }
      return;
    case "tree":
      if (format === "csv") {
        exportTreePresentationToCsv(presentation);
      } else if (format === "xlsx") {
        exportTreeToXlsx(presentation);
      } else {
        exportTreeToPdf(presentation);
      }
      return;
    case "kpi":
      if (format === "csv") {
        exportKpiPresentationToCsv(presentation);
      } else if (format === "xlsx") {
        exportKpiPresentationToXlsx(presentation);
      } else {
        exportKpiPresentationToPdf(presentation);
      }
      return;
    case "dashboard":
      if (format === "csv") {
        exportDashboardToCsv(presentation);
      } else if (format === "xlsx") {
        exportDashboardToXlsx(presentation);
      } else {
        exportDashboardToPdf(presentation);
      }
      return;
    default:
      chatAlert("Este tipo de visualização ainda não suporta exportação.");
  }
}
