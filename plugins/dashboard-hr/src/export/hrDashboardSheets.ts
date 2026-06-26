import type { TableExportPayload } from "./types";
import type { HrBranchMetrics } from "../types/hr";
import { formatDecimal, formatPercent } from "../utils/format";
import { formatOperationalUnitCode } from "../utils/operationalUnitLabels";

export function buildHrBranchesExportPayload(
  branches: HrBranchMetrics[],
): TableExportPayload {
  return {
    title: "Indicadores por unidade",
    columns: [
      { key: "unidade", label: "Unidade" },
      { key: "absenteismo", label: "Absenteísmo" },
      { key: "turnover", label: "Turnover" },
      { key: "treinamento", label: "Treinamento (h)" },
      { key: "pdis", label: "PDIs ativos" },
      { key: "avaliacoes", label: "Avaliações concluídas" },
    ],
    rows: branches.map((row) => ({
      unidade: formatOperationalUnitCode(row.branch_code),
      absenteismo: formatPercent(row.absenteeism_pct),
      turnover: formatPercent(row.turnover_pct),
      treinamento: formatDecimal(row.training_hours_per_collaborator, 2),
      pdis: formatDecimal(row.active_pdi_count, 0),
      avaliacoes: formatPercent(row.performance_reviews_completion_pct),
    })),
  };
}
