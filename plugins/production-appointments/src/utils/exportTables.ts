import { exportMatrixToXlsx, type MatrixExportTable } from "@delpi/plugin-ui/index";

import type {
  AppointmentRow,
  AppointmentsQueryFilters,
  ByOpRow,
  WorkCenterSummaryRow,
} from "../types/appointments";
import {
  formatAppointmentDateTime,
  formatInteger,
  formatOperatorLabel,
  formatProtheusDate,
  formatQuantity,
  formatResourceLabel,
} from "./formatters";

function safeDate(value: string): string {
  return value.replace(/[^\d-]/g, "");
}

function buildFilename(prefix: string, filters: AppointmentsQueryFilters): string {
  return `${prefix}_${filters.branch}_${safeDate(filters.dateStart)}_${safeDate(filters.dateEnd)}`;
}

function isInspection(value: number | boolean | undefined): boolean {
  return value === true || value === 1;
}

export async function exportWorkCentersExcel(
  items: WorkCenterSummaryRow[],
  filters: AppointmentsQueryFilters,
): Promise<void> {
  const table: MatrixExportTable = {
    title: "Apontamento de Produção — Resumo por CT",
    sheetName: "Por CT",
    headers: [
      "CT",
      "Nome",
      "Inspeção final",
      "Apontamentos",
      "Produzida",
      "Perdida",
      "OPs",
    ],
    rows: items.map((row) => [
      row.work_center,
      row.work_center_name || "",
      isInspection(row.is_final_inspection) ? "Sim" : "Não",
      formatInteger(row.appointment_count),
      formatQuantity(row.qty_produced),
      formatQuantity(row.qty_lost),
      formatInteger(row.op_count),
    ]),
  };
  exportMatrixToXlsx(table, buildFilename("apontamentos-por-ct", filters));
}

export async function exportAppointmentsExcel(
  items: AppointmentRow[],
  filters: AppointmentsQueryFilters,
): Promise<void> {
  const table: MatrixExportTable = {
    title: "Apontamento de Produção — Apontamentos",
    sheetName: "Apontamentos",
    headers: [
      "Data/Hora",
      "Operador",
      "Operação",
      "Recurso",
      "OP",
      "Produto",
      "Tipo",
      "CT",
      "Nome CT",
      "Produzida",
      "Perdida",
    ],
    rows: items.map((row) => [
      formatAppointmentDateTime(row),
      formatOperatorLabel(row),
      row.operation || "",
      formatResourceLabel(row),
      row.production_order,
      row.product,
      row.product_type || "",
      row.work_center,
      row.work_center_name || "",
      formatQuantity(row.qty_produced),
      formatQuantity(row.qty_lost),
    ]),
  };
  exportMatrixToXlsx(table, buildFilename("apontamentos-lista", filters));
}

export async function exportByOpExcel(
  items: ByOpRow[],
  filters: AppointmentsQueryFilters,
): Promise<void> {
  const table: MatrixExportTable = {
    title: "Apontamento de Produção — Por OP",
    sheetName: "Por OP",
    headers: [
      "OP",
      "Produto",
      "Tipo",
      "Apontamentos",
      "CTs",
      "Produzida",
      "Perdida",
      "Primeira data",
      "Última data",
    ],
    rows: items.map((row) => [
      row.production_order,
      row.product,
      row.product_type || "",
      formatInteger(row.appointment_count),
      formatInteger(row.work_center_count),
      formatQuantity(row.qty_produced),
      formatQuantity(row.qty_lost),
      formatProtheusDate(row.first_date),
      formatProtheusDate(row.last_date),
    ]),
  };
  exportMatrixToXlsx(table, buildFilename("apontamentos-por-op", filters));
}
