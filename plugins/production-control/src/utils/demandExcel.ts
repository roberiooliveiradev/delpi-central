import { copy } from "../content/copy";
import type { DemandLine } from "../types";
import { demandStatusBadge } from "./demandStatus";
import { formatIsoDate } from "./formatIsoDate";

export type DemandExcelColumn = { key: string; label: string };

export type DemandExcelPayload = {
  title: string;
  columns: DemandExcelColumn[];
  rows: Record<string, string | number>[];
};

/** Monta a planilha da Demanda (sem I/O) — inclui data de emissão do pedido. */
export function buildDemandExcelPayload(lines: readonly DemandLine[]): DemandExcelPayload {
  const detail = copy.demand.detail;
  const columns = copy.demand.columns;
  return {
    title: copy.demand.exportSheetTitle,
    columns: [
      { key: "due", label: columns.due },
      { key: "issued", label: detail.dispatch },
      { key: "customer", label: columns.customer },
      { key: "order", label: columns.order },
      { key: "customerOrder", label: detail.customerOrder },
      { key: "product", label: columns.product },
      { key: "ordered", label: detail.ordered },
      { key: "delivered", label: detail.delivered },
      { key: "open", label: columns.open },
      { key: "stock", label: detail.stock },
      { key: "uncovered", label: detail.uncovered },
      { key: "status", label: columns.status },
    ],
    rows: lines.map((line) => ({
      due: line.due_date ? formatIsoDate(line.due_date) : "",
      issued: line.dispatch_date ? formatIsoDate(line.dispatch_date) : "",
      customer: line.customer_name || "",
      order: `${line.sales_order}/${line.line_item}`,
      customerOrder: line.customer_order || "",
      product: line.product_code || "",
      ordered: line.ordered_quantity,
      delivered: line.delivered_quantity,
      open: line.open_quantity,
      stock: line.allocated_stock,
      uncovered: line.uncovered_quantity,
      status: demandStatusBadge(line.status).label,
    })),
  };
}

function sanitizeFileBase(name: string): string {
  return name.replace(/\.xlsx$/i, "").replace(/[\\/:*?"<>|]+/g, "_").trim() || "demanda";
}

export async function downloadDemandExcel(
  lines: readonly DemandLine[],
  fileName: string,
): Promise<void> {
  if (typeof document === "undefined") return;
  const payload = buildDemandExcelPayload(lines);
  if (!payload.columns.length || payload.rows.length === 0) {
    window.alert(copy.demand.exportEmpty);
    return;
  }

  const XLSX = await import("xlsx");
  const headers = payload.columns.map((column) => column.label);
  const data = payload.rows.map((row) =>
    payload.columns.map((column) => row[column.key] ?? ""),
  );
  const worksheet = XLSX.utils.aoa_to_sheet([headers, ...data]);
  worksheet["!cols"] = payload.columns.map((column) => {
    const maxLen = Math.max(
      column.label.length,
      ...payload.rows.map((row) => String(row[column.key] ?? "").length),
    );
    return { wch: Math.min(maxLen + 2, 50) };
  });
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, payload.title.slice(0, 31));
  XLSX.writeFile(workbook, `${sanitizeFileBase(fileName)}.xlsx`);
}
