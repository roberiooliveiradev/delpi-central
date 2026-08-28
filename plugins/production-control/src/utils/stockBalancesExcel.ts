import { copy } from "../content/copy";
import type { PpcBranch, StockBalanceLine } from "../types";

/** Conversão de UM no Excel de saldos (qtde TOTVS → unidade de emissão × 1000). */
export const STOCK_BALANCES_EXCEL_QUANTITY_FACTOR = 1000;

export type StockBalancesExcelColumn = { key: string; label: string };

export type StockBalancesExcelPayload = {
  title: string;
  columns: StockBalancesExcelColumn[];
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

/** Data de emissão no padrão do arquivo: DD-MM-AAAA. */
export function formatStockBalancesExportDate(issuedAt: Date = new Date()): string {
  return `${pad2(issuedAt.getDate())}-${pad2(issuedAt.getMonth() + 1)}-${issuedAt.getFullYear()}`;
}

/**
 * Nome do arquivo: filial 01 → «ESTOQUE MATRIZ - DD-MM-AAAA»;
 * filial 02 → «SALDO FILIAL - DD-MM-AAAA».
 */
export function buildStockBalancesExportFileName(
  branch: PpcBranch | string,
  issuedAt: Date = new Date(),
): string {
  const texts = copy.reports.stockBalances;
  const label = branch === "02" ? texts.exportTitleBranch02 : texts.exportTitleBranch01;
  return `${label} - ${formatStockBalancesExportDate(issuedAt)}`;
}

/** Monta a planilha — só código + quantidade × 1000. */
export function buildStockBalancesExcelPayload(
  lines: readonly StockBalanceLine[],
  branch: PpcBranch | string = "01",
): StockBalancesExcelPayload {
  const texts = copy.reports.stockBalances;
  const title = branch === "02" ? texts.exportTitleBranch02 : texts.exportTitleBranch01;
  return {
    title,
    columns: [
      { key: "product_code", label: texts.exportColumns.product },
      { key: "quantity", label: texts.exportColumns.quantity },
    ],
    rows: lines.map((line) => ({
      product_code: line.product_code || "",
      quantity: Number(line.quantity || 0) * STOCK_BALANCES_EXCEL_QUANTITY_FACTOR,
    })),
  };
}

function sanitizeFileBase(name: string): string {
  return (
    name.replace(/\.xlsx$/i, "").replace(/[\\/:*?"<>|]+/g, "_").trim() || "estoque"
  );
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

export async function downloadStockBalancesExcel(
  lines: readonly StockBalanceLine[],
  branch: PpcBranch | string,
  issuedAt: Date = new Date(),
): Promise<void> {
  if (typeof document === "undefined") return;
  const payload = buildStockBalancesExcelPayload(lines, branch);
  if (!payload.columns.length || payload.rows.length === 0) {
    window.alert(copy.reports.stockBalances.exportEmpty);
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
    buildStockBalancesExportFileName(branch, issuedAt),
  );
}
