import { copy } from "../content/copy";
import type { PpcBranch, ProductionOrderLine } from "../types";
import { formatIsoDate } from "./formatIsoDate";

export type ProductionOrdersExcelColumn = { key: string; label: string };

export type ProductionOrdersExcelPayload = {
  title: string;
  columns: ProductionOrdersExcelColumn[];
  rows: Record<string, string | number>[];
};

const THIN_BORDER = {
  style: "thin" as const,
  color: { argb: "FF000000" },
};

const ALL_BORDERS = {
  top: THIN_BORDER,
  left: THIN_BORDER,
  bottom: THIN_BORDER,
  right: THIN_BORDER,
};

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatProductionOrdersExportDate(issuedAt: Date = new Date()): string {
  return `${pad2(issuedAt.getDate())}-${pad2(issuedAt.getMonth() + 1)}-${issuedAt.getFullYear()}`;
}

export function buildProductionOrdersExportFileName(
  branch: PpcBranch | string,
  issuedAt: Date = new Date(),
): string {
  const texts = copy.reports.productionOrders;
  const label = branch === "02" ? texts.exportTitleBranch02 : texts.exportTitleBranch01;
  return `${label} - ${formatProductionOrdersExportDate(issuedAt)}`;
}

export function buildProductionOrdersExcelPayload(
  lines: readonly ProductionOrderLine[],
  branch: PpcBranch | string = "01",
  options: { includeFinishDate?: boolean } = {},
): ProductionOrdersExcelPayload {
  const texts = copy.reports.productionOrders;
  const title = branch === "02" ? texts.exportTitleBranch02 : texts.exportTitleBranch01;
  const columns: ProductionOrdersExcelColumn[] = [
    { key: "production_order", label: texts.columns.op },
    { key: "product_code", label: texts.columns.product },
    { key: "issue_date", label: texts.columns.issueDate },
    { key: "planned_start_date", label: texts.columns.startDate },
    { key: "due_date", label: texts.columns.dueDate },
    ...(options.includeFinishDate
      ? [{ key: "finish_date", label: texts.columns.finishDate }]
      : []),
    { key: "planned_qty", label: texts.columns.quantity },
    { key: "pending_qty", label: texts.columns.balance },
    { key: "observation", label: texts.columns.observation },
  ];
  return {
    title,
    columns,
    rows: lines.map((line) => ({
      production_order: line.production_order || "",
      product_code: line.product_code || "",
      issue_date: formatIsoDate(line.issue_date),
      planned_start_date: formatIsoDate(line.planned_start_date),
      due_date: formatIsoDate(line.due_date),
      ...(options.includeFinishDate ? { finish_date: formatIsoDate(line.finish_date) } : {}),
      planned_qty: Number(line.planned_qty || 0),
      pending_qty: Number(line.pending_qty || 0),
      observation: line.observation || "",
    })),
  };
}

function sanitizeFileBase(name: string): string {
  return name.replace(/\.xlsx$/i, "").replace(/[\\/:*?"<>|]+/g, "_").trim() || "ops";
}

function triggerXlsxDownload(buffer: ArrayBuffer, fileName: string): void {
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${sanitizeFileBase(fileName)}.xlsx`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function downloadProductionOrdersExcel(
  lines: readonly ProductionOrderLine[],
  branch: PpcBranch | string,
  options: { includeFinishDate?: boolean; issuedAt?: Date } = {},
): Promise<void> {
  if (typeof document === "undefined") return;
  const issuedAt = options.issuedAt ?? new Date();
  const payload = buildProductionOrdersExcelPayload(lines, branch, {
    includeFinishDate: options.includeFinishDate,
  });
  if (!payload.columns.length || payload.rows.length === 0) {
    window.alert(copy.reports.productionOrders.exportEmpty);
    return;
  }

  const ExcelJSImport = await import("exceljs");
  const ExcelJS = ExcelJSImport.default ?? ExcelJSImport;
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet(payload.title.slice(0, 31));

  sheet.columns = payload.columns.map((column) => {
    const maxLen = Math.max(
      column.label.length,
      ...payload.rows.map((row) => String(row[column.key] ?? "").length),
    );
    return { width: Math.min(maxLen + 2, 50) };
  });

  const headerRow = sheet.getRow(1);
  payload.columns.forEach((column, index) => {
    const cell = headerRow.getCell(index + 1);
    cell.value = column.label;
    cell.border = ALL_BORDERS;
    cell.font = { bold: true };
  });
  headerRow.commit();

  payload.rows.forEach((row, rowOffset) => {
    const worksheetRow = sheet.getRow(rowOffset + 2);
    payload.columns.forEach((column, index) => {
      const cell = worksheetRow.getCell(index + 1);
      cell.value = row[column.key] ?? "";
      cell.border = ALL_BORDERS;
    });
    worksheetRow.commit();
  });

  const buffer = await workbook.xlsx.writeBuffer();
  triggerXlsxDownload(
    buffer instanceof ArrayBuffer ? buffer : new Uint8Array(buffer).buffer,
    buildProductionOrdersExportFileName(branch, issuedAt),
  );
}
