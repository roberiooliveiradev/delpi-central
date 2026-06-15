import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { formatEficienciaFabrilAppointmentStatusLabel } from "./appointmentStatus";
import { formatDisplayDate } from "./dates";
import { exportTableExcel, exportTablePdf, type ExportTable } from "./exportDocument";
import { formatProductionQuantity } from "./format";

export const EF_APPOINTMENTS_HEADERS = [
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
  "Resultado MOD",
  "Status",
] as const;

function displayStatus(item: EficienciaFabrilItem): string {
  return formatEficienciaFabrilAppointmentStatusLabel(item);
}

export function efAppointmentToRow(item: EficienciaFabrilItem): (string | number)[] {
  return [
    formatDisplayDate(item.data_producao),
    item.hora_inicio ?? "",
    item.hora_final ?? "",
    formatProductionQuantity(item.qtd_apontada, item.unidade),
    item.filial ?? "",
    item.op ?? "",
    item.descricao_produto?.trim() || item.produto || "",
    item.centro_trabalho ?? "",
    item.nome_operador ?? item.login_operador ?? "",
    item.eficiencia_percentual ?? "",
    item.resultado_mod ?? "",
    displayStatus(item),
  ];
}

function buildFilename(dateStart: string, dateEnd: string, extension: "xlsx" | "pdf"): string {
  const safe = (value: string) => value.replace(/[^\d-]/g, "");
  return `eficiencia-fabril-apontamentos_${safe(dateStart)}_${safe(dateEnd)}.${extension}`;
}

function buildExportTable(items: EficienciaFabrilItem[]): ExportTable {
  return {
    title: "Eficiência Fabril — Apontamentos",
    sheetName: "Apontamentos",
    headers: [...EF_APPOINTMENTS_HEADERS],
    rows: items.map(efAppointmentToRow),
  };
}

export async function exportAppointmentsExcel(
  items: EficienciaFabrilItem[],
  dateStart: string,
  dateEnd: string
): Promise<void> {
  await exportTableExcel(buildExportTable(items), buildFilename(dateStart, dateEnd, "xlsx"));
}

export async function exportAppointmentsPdf(
  items: EficienciaFabrilItem[],
  dateStart: string,
  dateEnd: string
): Promise<void> {
  await exportTablePdf(buildExportTable(items), buildFilename(dateStart, dateEnd, "pdf"));
}
