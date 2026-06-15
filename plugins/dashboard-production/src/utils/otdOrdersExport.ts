import type { ProductionOtdOrderItem } from "../types/production";
import { formatDisplayDate } from "./dates";
import { downloadCsv } from "./csv";
import { exportTableExcel, exportTablePdf, type ExportTable } from "./exportDocument";

export const OTD_ORDERS_HEADERS = [
  "Filial",
  "OP",
  "Nº OP",
  "Item",
  "Produto",
  "Descrição",
  "Data prevista",
  "Data finalização",
  "Dias",
  "Status",
] as const;

function statusLabel(status: string): string {
  if (status === "on_time") return "No prazo";
  if (status === "late") return "Atrasado";
  return status;
}

export function otdOrderToRow(row: ProductionOtdOrderItem): (string | number)[] {
  return [
    row.branch ?? "",
    row.production_order ?? "",
    row.order_number ?? "",
    row.order_item ?? "",
    row.product_code ?? "",
    row.product_description ?? "",
    formatDisplayDate(row.due_date),
    formatDisplayDate(row.finish_date),
    row.days_diff ?? "",
    statusLabel(row.status),
  ];
}

function buildExportTable(title: string, orders: ProductionOtdOrderItem[]): ExportTable {
  return {
    title,
    sheetName: "Ordens",
    headers: [...OTD_ORDERS_HEADERS],
    rows: orders.map(otdOrderToRow),
  };
}

export function downloadOtdOrdersCsv(filename: string, orders: ProductionOtdOrderItem[]): void {
  downloadCsv(
    filename,
    [...OTD_ORDERS_HEADERS],
    orders.map((row) => otdOrderToRow(row).map(String))
  );
}

export async function exportOtdOrdersExcel(
  filename: string,
  orders: ProductionOtdOrderItem[]
): Promise<void> {
  await exportTableExcel(buildExportTable("OTD — Ordens de produção", orders), filename);
}

export async function exportOtdOrdersPdf(
  filename: string,
  orders: ProductionOtdOrderItem[]
): Promise<void> {
  await exportTablePdf(buildExportTable("OTD — Ordens de produção", orders), filename);
}
