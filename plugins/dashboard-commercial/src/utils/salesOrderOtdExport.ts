import type { SalesOrderOtdLineItem } from "../types/commercial";
import { COMMERCIAL_OTD_SERIES_LABELS } from "../constants/commercialOtdIndicators";
import type { SalesOrderOtdSeriesPoint } from "../hooks/useCommercialSalesOrderOtdSeries";
import { exportTableFormat, type TableExportPayload } from "../export/exportUtils";
import { formatDisplayDate } from "./dates";
import { formatOperationalUnitCode } from "./operationalUnitLabels";

export const SALES_ORDER_OTD_HEADERS = [
  "Unidade",
  "Pedido",
  "Linha",
  "Produto",
  "Descrição",
  "Cliente",
  "Nome cliente",
  "Qtd. vendida",
  "Qtd. entregue",
  "Entrega prometida",
  "Faturamento",
  "Dias",
  "Status",
] as const;

function statusLabel(status: string): string {
  if (status === "on_time") return "No prazo";
  if (status === "late") return "Atrasado";
  return status;
}

function buildLinesExportPayload(
  lines: SalesOrderOtdLineItem[],
  filename: string
): TableExportPayload {
  return {
    title: filename,
    columns: SALES_ORDER_OTD_HEADERS.map((label, index) => ({
      key: `col_${index}`,
      label,
    })),
    rows: lines.map((row) => ({
      col_0: formatOperationalUnitCode(row.branch, ""),
      col_1: row.order_number ?? "",
      col_2: row.line_item ?? "",
      col_3: row.product_code ?? "",
      col_4: row.product_description ?? "",
      col_5: row.customer_code ?? "",
      col_6: row.customer_name ?? "",
      col_7: row.qty_sold ?? "",
      col_8: row.qty_delivered ?? "",
      col_9: formatDisplayDate(row.promised_date),
      col_10: formatDisplayDate(row.invoice_date),
      col_11: row.days_diff ?? "",
      col_12: statusLabel(row.status),
    })),
  };
}

export function buildSalesOrderOtdSeriesPayload(
  points: SalesOrderOtdSeriesPoint[]
): TableExportPayload {
  return {
    title: "Evolução OTD pedidos de venda",
    columns: [
      { key: "periodo", label: "Período" },
      { key: "otdFilial01", label: COMMERCIAL_OTD_SERIES_LABELS.filial01 },
      { key: "otdFilial02", label: COMMERCIAL_OTD_SERIES_LABELS.filial02 },
    ],
    rows: points.map((point) => ({
      periodo: point.periodo,
      otdFilial01: point.otdFilial01 ?? "",
      otdFilial02: point.otdFilial02 ?? "",
    })),
  };
}

export async function exportSalesOrderOtdLinesExcel(
  filename: string,
  lines: SalesOrderOtdLineItem[]
): Promise<void> {
  exportTableFormat(buildLinesExportPayload(lines, filename), "xlsx");
}

export async function exportSalesOrderOtdLinesPdf(
  filename: string,
  lines: SalesOrderOtdLineItem[]
): Promise<void> {
  exportTableFormat(buildLinesExportPayload(lines, filename), "pdf");
}

export function downloadSalesOrderOtdSeriesCsv(
  _filename: string,
  points: SalesOrderOtdSeriesPoint[]
): void {
  exportTableFormat(buildSalesOrderOtdSeriesPayload(points), "csv");
}
