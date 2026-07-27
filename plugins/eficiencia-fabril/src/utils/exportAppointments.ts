import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import {
  APPOINTMENT_TABLE_COLUMNS,
  appointmentExportValue,
  type AppointmentTableColumn,
} from "./appointmentsTableColumns";
import type { AppointmentsSortColumn } from "./appointmentsTableSort";
import { exportTableExcel, exportTablePdf, type ExportTable } from "./exportDocument";

function resolveExportColumns(
  columnIds?: readonly AppointmentsSortColumn[]
): AppointmentTableColumn[] {
  if (!columnIds || columnIds.length === 0) {
    return APPOINTMENT_TABLE_COLUMNS;
  }
  const selected = new Set(columnIds);
  const columns = APPOINTMENT_TABLE_COLUMNS.filter((column) => selected.has(column.key));
  return columns.length > 0 ? columns : APPOINTMENT_TABLE_COLUMNS;
}

export function efAppointmentToRow(
  item: EficienciaFabrilItem,
  columnIds?: readonly AppointmentsSortColumn[]
): (string | number)[] {
  return resolveExportColumns(columnIds).map((column) =>
    appointmentExportValue(item, column.key)
  );
}

function buildFilename(dateStart: string, dateEnd: string, extension: "xlsx" | "pdf"): string {
  const safe = (value: string) => value.replace(/[^\d-]/g, "");
  return `eficiencia-fabril-apontamentos_${safe(dateStart)}_${safe(dateEnd)}.${extension}`;
}

function buildExportTable(
  items: EficienciaFabrilItem[],
  columnIds?: readonly AppointmentsSortColumn[]
): ExportTable {
  const columns = resolveExportColumns(columnIds);
  return {
    title: "Eficiência Fabril — Apontamentos",
    sheetName: "Apontamentos",
    headers: columns.map((column) => column.exportHeader),
    rows: items.map((item) => efAppointmentToRow(item, columnIds)),
  };
}

export async function exportAppointmentsExcel(
  items: EficienciaFabrilItem[],
  dateStart: string,
  dateEnd: string,
  columnIds?: readonly AppointmentsSortColumn[]
): Promise<void> {
  await exportTableExcel(
    buildExportTable(items, columnIds),
    buildFilename(dateStart, dateEnd, "xlsx")
  );
}

export async function exportAppointmentsPdf(
  items: EficienciaFabrilItem[],
  dateStart: string,
  dateEnd: string,
  columnIds?: readonly AppointmentsSortColumn[]
): Promise<void> {
  await exportTablePdf(
    buildExportTable(items, columnIds),
    buildFilename(dateStart, dateEnd, "pdf")
  );
}
