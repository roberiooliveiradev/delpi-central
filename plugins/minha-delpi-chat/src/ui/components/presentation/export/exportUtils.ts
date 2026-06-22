import type { ChatPresentation } from "../../../../data/api/chatTypes";
import {
  buildUtf8CsvBlob,
  csvCell,
  sanitizeFilename,
  sanitizeSheetName,
  triggerFileDownload,
} from "../../../../export/primitives";
import type { ExportColumn, TableExportPayload } from "../../../../export/types";
import { chatAlert } from "../../../utils/chatNativeDialogs";
import { formatChartColumnLabel } from "../pipeline/chartAxisSelection";
import {
  exportChartPayloadToPdf,
  exportTablePayloadToPdf,
  exportTablePayloadsToPdf,
} from "../../../../export/pdf/tablePdfExport";
import { rasterizeChartElement } from "./chartPngExport";
import { buildDashboardCsv } from "./dashboardExportCsv";
import { exportTreeToCsv, treePresentationToTable } from "../pipeline/treePresentationUtils";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;
type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;
type TreePresentation = Extract<ChatPresentation, { type: "tree" }>;
type KpiPresentation = Extract<ChatPresentation, { type: "kpi" }>;
type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;

export type { ExportColumn, TableExportPayload };
export { sanitizeFilename, sanitizeSheetName } from "../../../../export/primitives";

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

  const header = payload.columns.map((column) => column.label).join(";");
  const body = payload.rows
    .map((row) =>
      payload.columns.map((column) => csvCell(row[column.key])).join(";"),
    )
    .join("\n");

  triggerFileDownload(
    buildUtf8CsvBlob(`${header}\n${body}`),
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
  exportTablePayloadToPdf(payload);
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
    exportChartPayloadToPdf(title, payload, dataUrl);
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
  triggerFileDownload(
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
  exportTablePayloadsToPdf(presentation.title || "dashboard", sheets);
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
