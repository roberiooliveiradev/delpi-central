import { copy } from "../content/copy";
import type { DemandLine } from "../types";
import { demandStatusBadge } from "./demandStatus";
import { formatIsoDate } from "./formatIsoDate";

const HEADERS = [
  copy.demand.columns.due,
  copy.demand.columns.customer,
  copy.demand.columns.order,
  copy.demand.detail.customerOrder,
  copy.demand.columns.product,
  copy.demand.detail.ordered,
  copy.demand.detail.delivered,
  copy.demand.columns.open,
  copy.demand.detail.stock,
  copy.demand.detail.uncovered,
  copy.demand.columns.status,
];

/** Excel pt-BR lê `;` como separador e vírgula como decimal. */
const SEPARATOR = ";";

function cell(value: string | number | null | undefined): string {
  const text = value == null ? "" : String(value);
  const escaped = text.replace(/"/g, '""');
  return /[";\n]/.test(escaped) ? `"${escaped}"` : escaped;
}

function quantity(value: number): string {
  return value.toFixed(3).replace(".", ",");
}

export function buildDemandCsv(lines: readonly DemandLine[]): string {
  const rows = lines.map((line) =>
    [
      line.due_date ? formatIsoDate(line.due_date) : "",
      line.customer_name,
      `${line.sales_order}/${line.line_item}`,
      line.customer_order,
      line.product_code,
      quantity(line.ordered_quantity),
      quantity(line.delivered_quantity),
      quantity(line.open_quantity),
      quantity(line.allocated_stock),
      quantity(line.uncovered_quantity),
      demandStatusBadge(line.status).label,
    ]
      .map(cell)
      .join(SEPARATOR),
  );
  return [HEADERS.map(cell).join(SEPARATOR), ...rows].join("\r\n");
}

export function downloadDemandCsv(lines: readonly DemandLine[], fileName: string): void {
  if (typeof document === "undefined") return;
  // BOM para o Excel reconhecer o acento como UTF-8.
  const blob = new Blob([`\uFEFF${buildDemandCsv(lines)}`], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}
