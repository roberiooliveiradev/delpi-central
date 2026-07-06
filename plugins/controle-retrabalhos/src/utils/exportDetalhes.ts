import type { RetrabalhoDetalheItem, RetrabalhoQueryFilters } from "../types/retrabalho";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatHours,
  joinMotivoObservacao,
} from "./formatters";
import { exportTableExcel, type ExportTable } from "./exportDocument";

export const RETRABALHO_DETALHES_HEADERS = [
  "Data",
  "Recurso",
  "Operador",
  "Horas",
  "Custo",
  "Motivo / obs.",
] as const;

function detalheToRow(item: RetrabalhoDetalheItem): (string | number)[] {
  return [
    formatDatePtBr(item.dataReferencia),
    item.recurso || "",
    item.nomeOperador || "",
    formatHours(item.tempoHoras),
    formatCurrencyBrl(item.valorParada),
    joinMotivoObservacao(item.motivo, item.observacao),
  ];
}

function buildFilename(filters: RetrabalhoQueryFilters): string {
  const safe = (value: string) => value.replace(/[^\d-]/g, "");
  return `controle-retrabalhos_${filters.filial}_${safe(filters.dataInicio)}_${safe(filters.dataFim)}`;
}

function buildExportTable(items: RetrabalhoDetalheItem[]): ExportTable {
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
  await exportTableExcel(buildExportTable(items), buildFilename(filters));
}
