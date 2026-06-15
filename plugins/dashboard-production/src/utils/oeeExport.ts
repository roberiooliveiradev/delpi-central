import type { ProductionOeeAppointmentItem } from "../types/production";
import { downloadCsv } from "./csv";

function statusLabel(status: string): string {
  if (status === "valid") return "Válido";
  if (status === "outlier") return "Fora da faixa";
  return status;
}

export function downloadOeeAppointmentsCsv(
  filename: string,
  appointments: ProductionOeeAppointmentItem[]
): void {
  downloadCsv(
    filename,
    [
      "Filial",
      "OP",
      "Produto",
      "Descrição",
      "Tipo",
      "Centro de trabalho",
      "Operação",
      "Recurso",
      "Nome recurso",
      "Data produção",
      "OEE (%)",
      "Qtd produzida",
      "Status",
    ],
    appointments.map((row) => [
      row.branch ?? "",
      row.production_order ?? "",
      row.product_code ?? "",
      row.product_description ?? "",
      row.product_type ?? "",
      row.work_center ?? "",
      row.operation ?? "",
      row.resource_code ?? "",
      row.resource_name ?? "",
      row.production_date ?? "",
      row.oee_pct != null ? String(row.oee_pct) : "",
      row.produced_qty != null ? String(row.produced_qty) : "",
      statusLabel(row.status),
    ])
  );
}
