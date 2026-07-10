import type { ChatMessageMetadata } from "../../data/api/chatTypes";
import {
  csvCell,
  sanitizeFilename,
  sanitizeSheetName,
  triggerFileDownload,
} from "../../export/primitives";
import { chatAlert } from "./chatNativeDialogs";
import { buildExcelCsvBlob } from "./drawingAnalysisCsvEncoding";
import { validateDrawingChecklistConsistency } from "./drawingAnalysisConsistency";
import { printDrawingAnalysisReport } from "./drawingAnalysisPrint";

export type DrawingExportTable = {
  key: string;
  title: string;
  sheetName?: string;
  columns: { key: string; label: string }[];
  rows: Record<string, string>[];
  presentation?: "outline" | "table";
  outline?: string;
};

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

const DEFAULT_STATUS_LABELS: Record<string, string> = {
  ok: "OK",
  pending: "Pendente",
  error: "Erro",
  critical_error: "Erro crítico",
  incomplete: "Incompleto",
};

function resolveStatusLabels(
  exportPayload: DrawingAnalysisExportPayload,
): Record<string, string> {
  return exportPayload.statusLabels ?? DEFAULT_STATUS_LABELS;
}

function resolveExportLabels(exportPayload: DrawingAnalysisExportPayload) {
  return exportPayload.exportLabels ?? {};
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

function buildChecklistTableFromItems(
  items: DrawingCheckItem[],
  exportPayload: DrawingAnalysisExportPayload,
): DrawingExportTable {
  const statusLabels = resolveStatusLabels(exportPayload);
  const exportLabels = resolveExportLabels(exportPayload);

  return {
    key: "checklist",
    title: exportLabels.checklistTitle || "Checklist completo",
    sheetName: "Checklist",
    columns: [
      { key: "section", label: "Seção" },
      { key: "item", label: "Item" },
      { key: "status", label: "Status" },
      { key: "observation", label: "Observação" },
    ],
    rows: items.map((item) => ({
      section: String(item.section ?? "—"),
      item: String(item.item ?? "—"),
      status: statusLabels[String(item.status ?? "")] ?? String(item.status ?? "—"),
      observation: String(item.recommendation ?? "—"),
    })),
  };
}

function resolveExportTables(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): DrawingExportTable[] {
  const items = (drawingAnalysis?.items as DrawingCheckItem[] | undefined) ?? [];

  if (exportPayload.tables?.length) {
    const tables = exportPayload.tables.map((table) => ({
      ...table,
      rows: table.rows.map((row) => ({ ...row })),
    }));

    if (items.length) {
      const consistency = validateDrawingChecklistConsistency(exportPayload, drawingAnalysis);
      const checklistIndex = tables.findIndex((table) => table.key === "checklist");

      if (!consistency.ok && checklistIndex >= 0) {
        tables[checklistIndex] = buildChecklistTableFromItems(items, exportPayload);
      }
    }

    return tables;
  }

  const exportLabels = resolveExportLabels(exportPayload);
  const tables: DrawingExportTable[] = [];
  const nonConformityRows = exportPayload.spreadsheetRows ?? [];

  if (nonConformityRows.length) {
    const shortHeaders = exportLabels.spreadsheetShortHeaders;
    tables.push({
      key: "nonconformities",
      title: exportLabels.nonconformitiesTitle || "Não conformidades",
      sheetName: "Divergências",
      columns: [
        { key: "section", label: shortHeaders?.[0] || "Seção" },
        { key: "item", label: shortHeaders?.[1] || "Item" },
        { key: "status", label: shortHeaders?.[2] || "Status" },
        { key: "pdfEvidence", label: shortHeaders?.[3] || "PDF" },
        { key: "apiEvidence", label: shortHeaders?.[4] || "API" },
        { key: "recommendation", label: shortHeaders?.[5] || "Ação" },
      ],
      rows: nonConformityRows.map((row) => ({ ...row })),
    });
  }

  if (items.length) {
    tables.push(buildChecklistTableFromItems(items, exportPayload));
  }

  return tables;
}

export function downloadDrawingAnalysisMarkdown(
  exportPayload: DrawingAnalysisExportPayload,
): void {
  const markdown = String(exportPayload.markdown || "").trim();

  if (!markdown) {
    return;
  }

  triggerFileDownload(
    new Blob([markdown], {
      type: exportPayload.mimeType || "text/markdown;charset=utf-8",
    }),
    exportPayload.filename || "relatorio-desenho.md",
  );
}

function buildClientCsvContent(tables: DrawingExportTable[]): string {
  const lines: string[] = [];

  for (let index = 0; index < tables.length; index += 1) {
    const table = tables[index];

    if (index > 0) {
      lines.push("");
    }

    lines.push(table.title);
    lines.push(table.columns.map((column) => column.label).join(";"));

    for (const row of table.rows) {
      lines.push(
        table.columns.map((column) => csvCell(row[column.key])).join(";"),
      );
    }
  }

  return lines.join("\r\n");
}

export function downloadDrawingAnalysisCsv(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): void {
  const csv = String(exportPayload.csv || "").trim();
  const code = resolveProductCode(exportPayload, drawingAnalysis);
  const filename =
    exportPayload.csvFilename || `relatorio-desenho-${sanitizeFilename(code, "relatorio-desenho")}.csv`;

  if (csv) {
    triggerFileDownload(buildExcelCsvBlob(csv), filename);
    return;
  }

  const tables = resolveExportTables(exportPayload, drawingAnalysis);

  if (!tables.length) {
    return;
  }

  triggerFileDownload(buildExcelCsvBlob(buildClientCsvContent(tables)), filename);
}

export async function downloadDrawingAnalysisXlsx(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): Promise<void> {
  const tables = resolveExportTables(exportPayload, drawingAnalysis);

  if (!tables.length) {
    return;
  }

  try {
    const XLSX = await import("xlsx");
    const workbook = XLSX.utils.book_new();
    const usedSheetNames = new Set<string>();

    for (const table of tables) {
      const baseName = sanitizeSheetName(
        table.sheetName || table.title || table.key,
        "Planilha",
      );
      let sheetName = baseName;
      let suffix = 2;

      while (usedSheetNames.has(sheetName)) {
        const trimmed = baseName.slice(0, Math.max(1, 28 - String(suffix).length));
        sheetName = `${trimmed}_${suffix}`;
        suffix += 1;
      }

      usedSheetNames.add(sheetName);

      const header = table.columns.map((column) => column.label);
      const data = table.rows.map((row) =>
        table.columns.map((column) => row[column.key] ?? ""),
      );
      const worksheet = XLSX.utils.aoa_to_sheet([header, ...data]);
      XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
    }

    const code = resolveProductCode(exportPayload, drawingAnalysis);
    const filename =
      exportPayload.xlsxFilename || `relatorio-desenho-${sanitizeFilename(code, "relatorio-desenho")}.xlsx`;
    XLSX.writeFile(workbook, filename);
  } catch {
    chatAlert("Não foi possível exportar XLSX. Tente o CSV ou Markdown.");
  }
}

export function downloadDrawingAnalysisPdf(
  exportPayload: DrawingAnalysisExportPayload,
  drawingAnalysis?: Record<string, unknown>,
): void {
  const tables = resolveExportTables(exportPayload, drawingAnalysis);
  const payload =
    tables.length > 0
      ? { ...exportPayload, tables }
      : exportPayload;

  if (!payload.tables?.length && !String(payload.markdown || "").trim()) {
    return;
  }

  const opened = printDrawingAnalysisReport(payload, drawingAnalysis);

  if (!opened) {
    chatAlert(
      "Não foi possível abrir a impressão do PDF. Verifique se o navegador não bloqueou pop-ups.",
    );
  }
}

/** @deprecated Use downloadDrawingAnalysisMarkdown */
export function downloadDrawingAnalysisExport(
  exportPayload: DrawingAnalysisExportPayload,
): void {
  downloadDrawingAnalysisMarkdown(exportPayload);
}
