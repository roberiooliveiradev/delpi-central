import type { RetrabalhoDetalheItem, RetrabalhoQueryFilters } from "../types/retrabalho";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatHours,
  formatMotivoLabel,
  formatObservacao,
} from "./formatters";
import { exportMatrixToXlsx, type MatrixExportTable } from "@delpi/plugin-ui/index";

export const RETRABALHO_DETALHES_HEADERS = [
  "Data",
  "Recurso",
  "Operador",
  "Horas",
  "Custo",
  "Motivo",
  "Observação",
] as const;

function detalheToRow(item: RetrabalhoDetalheItem): (string | number)[] {
  return [
    formatDatePtBr(item.dataReferencia),
    item.recurso || "",
    item.nomeOperador || "",
    formatHours(item.tempoHoras),
    formatCurrencyBrl(item.valorParada),
    formatMotivoLabel(item.motivo, item.motivoDescricao ?? item.stop_reason_description),
    (item.observacao ?? "").trim(),
  ];
}

function buildFilename(filters: RetrabalhoQueryFilters): string {
  const safe = (value: string) => value.replace(/[^\d-]/g, "");
  return `controle-retrabalhos_${filters.branch}_${safe(filters.start_date)}_${safe(filters.end_date)}`;
}

function buildExportTable(items: RetrabalhoDetalheItem[]): MatrixExportTable {
  return {
    title: "Controle de Retrabalhos — Detalhes",
    sheetName: "Detalhes",
    headers: [...RETRABALHO_DETALHES_HEADERS],
    rows: items.map(detalheToRow),
  };
}

export async function exportDetalhesExcel(
  items: RetrabalhoDetalheItem[],
  filters: RetrabalhoQueryFilters,
): Promise<void> {
  exportMatrixToXlsx(buildExportTable(items), buildFilename(filters));
}
