import type { ProductionOeeAppointmentItem } from "../types/production";
import { formatProductionQuantity } from "./format";
import { formatOeeAppointmentStatusLabel } from "./oeeAppointmentStatus";
import { downloadCsv } from "./csv";
import { exportTableExcel, exportTablePdf, type ExportTable } from "./exportDocument";
import { formatOperationalUnitCode } from "../utils/operationalUnitLabels";

export const OEE_APPOINTMENTS_HEADERS = [
  "Data",
  "Início",
  "Fim",
  "Qtd. apontada",
  "Unidade",
  "OP",
  "Descrição produto",
  "CT",
  "Operador",
  "Eficiência (%)",
  "Status",
] as const;

function displayStatus(item: ProductionOeeAppointmentItem): string {
  return formatOeeAppointmentStatusLabel(item);
}

export function oeeAppointmentToRow(item: ProductionOeeAppointmentItem): (string | number)[] {
  return [
    item.production_date ?? "",
    item.start_time ?? "",
    item.end_time ?? "",
    formatProductionQuantity(item.produced_qty, item.unit),
    formatOperationalUnitCode(item.branch, ""),
    item.production_order ?? "",
    item.product_description ?? "",
    item.work_center ?? "",
    item.operator_code ?? "",
    item.oee_pct != null ? String(item.oee_pct) : "",
    displayStatus(item),
  ];
}

function buildExportTable(
  title: string,
  appointments: ProductionOeeAppointmentItem[]
): ExportTable {
  return {
    title,
    sheetName: "Apontamentos",
    headers: [...OEE_APPOINTMENTS_HEADERS],
    rows: appointments.map(oeeAppointmentToRow),
  };
}

export function downloadOeeAppointmentsCsv(
  filename: string,
  appointments: ProductionOeeAppointmentItem[]
): void {
  downloadCsv(
    filename,
    [...OEE_APPOINTMENTS_HEADERS],
    appointments.map((row) => oeeAppointmentToRow(row).map(String))
  );
}

export async function exportOeeAppointmentsExcel(
  filename: string,
  appointments: ProductionOeeAppointmentItem[]
): Promise<void> {
  await exportTableExcel(buildExportTable("OEE — Apontamentos", appointments), filename);
}

export async function exportOeeAppointmentsPdf(
  filename: string,
  appointments: ProductionOeeAppointmentItem[]
): Promise<void> {
  await exportTablePdf(buildExportTable("OEE — Apontamentos", appointments), filename);
}
