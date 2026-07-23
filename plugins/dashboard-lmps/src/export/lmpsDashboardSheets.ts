import type { TableExportPayload } from "./types";
import type { LmpDashboardItem } from "../types/lmp";
import { formatLmpApiDate } from "../utils/dates";
import { formatOperationalUnitCode } from "../utils/operationalUnitLabels";
import {
  formatCycleIndex,
  formatDashboardRevision,
} from "../utils/lmpListingDisplay";

function formatApiDate(value?: string | null): string {
  return formatLmpApiDate(value, "");
}

function formatListingKind(kind?: string | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "";
}

export function buildLmpsTableExportPayload(
  items: LmpDashboardItem[],
): TableExportPayload {
  return {
    title: "Registros filtrados",
    columns: [
      { key: "unidade", label: "Unidade" },
      { key: "tipo", label: "Tipo" },
      { key: "proposta", label: "Nº Proposta" },
      { key: "revisao", label: "Revisão" },
      { key: "ciclo", label: "Ciclo" },
      { key: "descricao", label: "Descrição" },
      { key: "inicio", label: "Data Início" },
      { key: "fim", label: "Data Fim" },
      { key: "statusEng", label: "Status Engenharia" },
      { key: "qtdPi", label: "Qtd PI" },
      { key: "nivel", label: "Nível" },
      { key: "diasUteis", label: "Dias úteis" },
      { key: "dataLimite", label: "Data Limite" },
      { key: "leadTime", label: "Lead Time Útil" },
      { key: "status", label: "Status Classificação" },
    ],
    rows: items.map((row) => ({
      unidade: formatOperationalUnitCode(row.branch, ""),
      tipo: formatListingKind(row.listing_kind),
      proposta: row.sale_number,
      revisao: formatDashboardRevision(row),
      ciclo: formatCycleIndex(row.cycle_index),
      descricao: row.sale_description ?? "",
      inicio: formatApiDate(row.start_date),
      fim: formatApiDate(row.end_date),
      statusEng: row.engineering_status ?? "",
      qtdPi: String(row.qtd_pi ?? 0),
      nivel: row.nivel,
      diasUteis: String(row.dias_uteis_sla),
      dataLimite: formatApiDate(row.data_limite),
      leadTime: row.lead_time_util != null ? String(row.lead_time_util) : "",
      status: row.status,
    })),
  };
}
