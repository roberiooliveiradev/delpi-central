import type { ProductionOtdOrderItem } from "../types/production";
import { downloadCsv } from "./csv";

function statusLabel(status: string): string {
  if (status === "on_time") return "No prazo";
  if (status === "late") return "Atrasado";
  return status;
}

export function downloadOtdOrdersCsv(
  filename: string,
  orders: ProductionOtdOrderItem[]
): void {
  downloadCsv(
    filename,
    [
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
    ],
    orders.map((row) => [
      row.branch ?? "",
      row.production_order ?? "",
      row.order_number ?? "",
      row.order_item ?? "",
      row.product_code ?? "",
      row.product_description ?? "",
      row.due_date ?? "",
      row.finish_date ?? "",
      String(row.days_diff ?? ""),
      statusLabel(row.status),
    ])
  );
}
