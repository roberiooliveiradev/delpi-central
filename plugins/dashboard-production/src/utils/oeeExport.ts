import { formatOeeAppointmentStatusLabel } from "./oeeAppointmentStatus";
import type { ProductionOeeAppointmentItem } from "../types/production";
import { downloadCsv } from "./csv";

function displayStatus(item: ProductionOeeAppointmentItem): string {
  return formatOeeAppointmentStatusLabel(item);
}

export function downloadOeeAppointmentsCsv(
  filename: string,
  appointments: ProductionOeeAppointmentItem[]
): void {
  downloadCsv(
    filename,
    [
      "Data",
      "Início",
      "Fim",
      "Qtd. apontada",
      "Filial",
      "OP",
      "Descrição produto",
      "CT",
      "Operador",
      "Eficiência (%)",
      "Status",
    ],
    appointments.map((row) => [
      row.production_date ?? "",
      row.start_time ?? "",
      row.end_time ?? "",
      row.produced_qty != null ? String(row.produced_qty) : "",
      row.branch ?? "",
      row.production_order ?? "",
      row.product_description ?? "",
      row.work_center ?? "",
      row.operator_code ?? "",
      row.oee_pct != null ? String(row.oee_pct) : "",
      displayStatus(row),
    ])
  );
}
