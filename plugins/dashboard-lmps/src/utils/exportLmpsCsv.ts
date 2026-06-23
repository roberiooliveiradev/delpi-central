import type { LmpDashboardItem } from "../types/lmp";
import { downloadCsv } from "./csv";
import {
  formatCycleIndex,
  formatDashboardRevision,
} from "./lmpListingDisplay";

function formatApiDate(value?: string | null): string {
  if (!value || value.length !== 8) return "";
  return `${value.slice(6, 8)}/${value.slice(4, 6)}/${value.slice(0, 4)}`;
}

function formatListingKind(kind?: string | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "";
}

const EXPORT_HEADERS = [
  "Filial",
  "Tipo",
  "Nº Proposta",
  "Revisão",
  "Ciclo",
  "Descrição",
  "Data Início",
  "Data Fim",
  "Status Engenharia",
  "Qtd PI",
  "Nível",
  "Dias úteis",
  "Data Limite",
  "Lead Time Útil",
  "Status Classificação",
];

function rowToCsvCells(row: LmpDashboardItem): string[] {
  return [
    row.branch ?? "",
    formatListingKind(row.listing_kind),
    row.sale_number,
    formatDashboardRevision(row),
    formatCycleIndex(row.cycle_index),
    row.sale_description ?? "",
    formatApiDate(row.start_date),
    formatApiDate(row.end_date),
    row.engineering_status ?? "",
    String(row.qtd_pi ?? 0),
    row.nivel,
    String(row.dias_uteis_sla),
    formatApiDate(row.data_limite),
    row.lead_time_util != null ? String(row.lead_time_util) : "",
    row.status,
  ];
}

export function exportLmpsDashboardCsv(
  items: LmpDashboardItem[],
  options?: { dateStart?: string; dateEnd?: string }
): void {
  if (items.length === 0) return;

  const period =
    options?.dateStart && options?.dateEnd
      ? `${options.dateStart}_${options.dateEnd}`
      : new Date().toISOString().slice(0, 10);

  downloadCsv(
    `lmps-${period}.csv`,
    EXPORT_HEADERS,
    items.map(rowToCsvCells)
  );
}
