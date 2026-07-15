import { exportMatrixToXlsx, type MatrixExportTable } from "@delpi/plugin-ui/index";

import type { ScrapQueryFilters, ScrapRegistroItem } from "../types/scrap";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatQuantity,
} from "./formatters";

export const SCRAP_REGISTROS_HEADERS = [
  "Data",
  "OP",
  "PA",
  "MP",
  "Descrição",
  "UM",
  "Motivo",
  "Código motivo",
  "Centro de trabalho",
  "Colaborador",
  "Código operador",
  "Quantidade",
  "Valor",
] as const;

function registroToRow(item: ScrapRegistroItem): (string | number)[] {
  return [
    formatDatePtBr(item.dataPerda),
    item.op || "",
    item.pa || "",
    item.mp || "",
    item.descricao || "",
    item.um || "",
    item.motivo || "",
    item.motivoCodigo || "",
    item.centroTrabalho || "",
    item.nomeOperador || "",
    item.codigoOperador || "",
    formatQuantity(item.quantidade),
    formatCurrencyBrl(item.valor),
  ];
}

function buildFilename(filters: ScrapQueryFilters): string {
  const safe = (value: string) => value.replace(/[^\d-]/g, "");
  return `scrap-monitoring_${filters.filial}_${safe(filters.dataInicio)}_${safe(filters.dataFim)}`;
}

function buildExportTable(items: ScrapRegistroItem[]): MatrixExportTable {
  return {
    title: "Acompanhamento de Refugos — Registros",
    sheetName: "Refugos",
    headers: [...SCRAP_REGISTROS_HEADERS],
    rows: items.map(registroToRow),
  };
}

export async function exportRegistrosExcel(
  items: ScrapRegistroItem[],
  filters: ScrapQueryFilters,
): Promise<void> {
  exportMatrixToXlsx(buildExportTable(items), buildFilename(filters));
}
