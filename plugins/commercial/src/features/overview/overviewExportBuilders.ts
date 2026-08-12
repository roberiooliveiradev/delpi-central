import type { TableExportPayload } from "@delpi/plugin-ui/index";

import { ANALYTICS_ROL_SERIES_LABELS } from "../analytics/utils/analyticsBranchFilters";
import type { ClosingRateData, CommercialRolSeriesPoint } from "../../types/analytics";
import { formatCurrency } from "../../utils/format";

export function buildOverviewRolSeriesPayload(
  points: CommercialRolSeriesPoint[],
): TableExportPayload {
  return {
    title: "Evolução do ROL (R$)",
    columns: [
      { key: "periodo", label: "Período" },
      { key: "rolMatrix", label: ANALYTICS_ROL_SERIES_LABELS.unit01 },
      { key: "rolBranch", label: ANALYTICS_ROL_SERIES_LABELS.unit02 },
    ],
    rows: points.map((point) => ({
      periodo: point.periodo,
      rolMatrix: formatCurrency(point.rol_matrix),
      rolBranch: formatCurrency(point.rol_branch),
    })),
  };
}

export function buildOverviewFunnelPayload(
  funnel: ClosingRateData | null,
): TableExportPayload {
  const proposals = funnel?.qtd_proposals ?? 0;
  const won = funnel?.qtd_won ?? 0;
  const lost = Math.max(proposals - won, 0);
  const rate = funnel?.sales_conversion_rate_pct;
  return {
    title: "Funil de conversão",
    columns: [
      { key: "metrica", label: "Métrica" },
      { key: "valor", label: "Valor" },
    ],
    rows: [
      { metrica: "Propostas no período", valor: String(proposals) },
      { metrica: "Ganhas (aceite no período)", valor: String(won) },
      { metrica: "Sem conversão", valor: String(lost) },
      {
        metrica: "Taxa de conversão (%)",
        valor:
          rate == null || Number.isNaN(rate)
            ? "—"
            : rate.toLocaleString("pt-BR", { maximumFractionDigits: 2 }),
      },
    ],
  };
}
