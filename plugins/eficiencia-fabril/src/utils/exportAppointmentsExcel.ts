import { formatEficienciaFabrilAppointmentStatusLabel } from "./appointmentStatus";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { formatDisplayDate } from "./dates";

const HEADERS = [
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

function itemToRow(item: EficienciaFabrilItem): (string | number)[] {
  return [
    formatDisplayDate(item.data_producao),
    item.hora_inicio ?? "",
    item.hora_final ?? "",
    item.qtd_apontada ?? "",
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

function buildFilename(dateStart: string, dateEnd: string): string {
  const safe = (value: string) => value.replace(/[^\d-]/g, "");
  return `eficiencia-fabril-apontamentos_${safe(dateStart)}_${safe(dateEnd)}.xlsx`;
}

export async function exportAppointmentsExcel(
  items: EficienciaFabrilItem[],
  dateStart: string,
  dateEnd: string
): Promise<void> {
  const XLSX = await import("xlsx");

  const rows = items.map(itemToRow);
  const worksheet = XLSX.utils.aoa_to_sheet([HEADERS.slice(), ...rows]);

  worksheet["!cols"] = HEADERS.map((header, columnIndex) => {
    const maxLen = Math.max(
      header.length,
      ...rows.map((row) => String(row[columnIndex] ?? "").length)
    );
    return { wch: Math.min(maxLen + 2, 40) };
  });

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Apontamentos");
  XLSX.writeFile(workbook, buildFilename(dateStart, dateEnd));
}
