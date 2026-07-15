import { exportMatrixToXlsx, type MatrixExportTable } from "@delpi/plugin-ui/index";

import type { ScrapQueryFilters, ScrapRegistroItem } from "../types/scrap";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatQuantity,
} from "./formatters";

/** Coluna da grade → campo(s) no Excel (mesmas keys do DataTable). */
export const SCRAP_REGISTROS_EXPORT_FIELDS = [
  { key: "data", header: "Data", value: (item: ScrapRegistroItem) => formatDatePtBr(item.dataPerda) },
  { key: "op", header: "OP", value: (item: ScrapRegistroItem) => item.op || "" },
  { key: "pa", header: "PA", value: (item: ScrapRegistroItem) => item.pa || "" },
  { key: "mp", header: "MP", value: (item: ScrapRegistroItem) => item.mp || "" },
  {
    key: "descricao",
    header: "Descrição",
    value: (item: ScrapRegistroItem) => item.descricao || "",
  },
  { key: "descricao", header: "UM", value: (item: ScrapRegistroItem) => item.um || "" },
  { key: "motivo", header: "Motivo", value: (item: ScrapRegistroItem) => item.motivo || "" },
  {
    key: "motivo",
    header: "Código motivo",
    value: (item: ScrapRegistroItem) => item.motivoCodigo || "",
  },
  {
    key: "ct",
    header: "Centro de trabalho",
    value: (item: ScrapRegistroItem) => item.centroTrabalho || "",
  },
  {
    key: "colaborador",
    header: "Colaborador",
    value: (item: ScrapRegistroItem) => item.nomeOperador || "",
  },
  {
    key: "colaborador",
    header: "Código operador",
    value: (item: ScrapRegistroItem) => item.codigoOperador || "",
  },
  {
    key: "qtd",
    header: "Quantidade",
    value: (item: ScrapRegistroItem) => formatQuantity(item.quantidade),
  },
  { key: "valor", header: "Valor", value: (item: ScrapRegistroItem) => formatCurrencyBrl(item.valor) },
] as const;

/** @deprecated Use SCRAP_REGISTROS_EXPORT_FIELDS — mantido para compatibilidade de testes. */
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

function buildFilename(filters: ScrapQueryFilters): string {
  const safe = (value: string) => value.replace(/[^\d-]/g, "");
  return `scrap-monitoring_${filters.filial}_${safe(filters.dataInicio)}_${safe(filters.dataFim)}`;
}

function resolveExportFields(visibleColumnKeys?: readonly string[]) {
  if (!visibleColumnKeys || visibleColumnKeys.length === 0) {
    return [...SCRAP_REGISTROS_EXPORT_FIELDS];
  }
  const visible = new Set(visibleColumnKeys);
  return SCRAP_REGISTROS_EXPORT_FIELDS.filter((field) => visible.has(field.key));
}

function buildExportTable(
  items: ScrapRegistroItem[],
  visibleColumnKeys?: readonly string[],
): MatrixExportTable {
  const fields = resolveExportFields(visibleColumnKeys);
  return {
    title: "Acompanhamento de Refugos — Registros",
    sheetName: "Refugos",
    headers: fields.map((field) => field.header),
    rows: items.map((item) => fields.map((field) => field.value(item))),
  };
}

export async function exportRegistrosExcel(
  items: ScrapRegistroItem[],
  filters: ScrapQueryFilters,
  visibleColumnKeys?: readonly string[],
): Promise<void> {
  exportMatrixToXlsx(buildExportTable(items, visibleColumnKeys), buildFilename(filters));
}
