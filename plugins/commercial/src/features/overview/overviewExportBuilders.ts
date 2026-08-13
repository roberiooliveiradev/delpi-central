import type { TableExportPayload } from "@delpi/plugin-ui/index";

import { ANALYTICS_CONVERSION_SERIES_LABELS, ANALYTICS_ROL_SERIES_LABELS } from "../analytics/utils/analyticsBranchFilters";
import type {
  ClosingRateData,
  CommercialRolSeriesPoint,
  SalesConversionRateSeriesPoint,
} from "../../types/analytics";
import { formatCurrency } from "../../utils/format";

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}%`;
}

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

export function buildOverviewClosingRateSeriesPayload(
  points: SalesConversionRateSeriesPoint[],
): TableExportPayload {
  return {
    title: "Evolução da taxa de conversão (%)",
    columns: [
      { key: "periodo", label: "Período" },
      { key: "conversion01", label: ANALYTICS_CONVERSION_SERIES_LABELS.unit01 },
      { key: "conversion02", label: ANALYTICS_CONVERSION_SERIES_LABELS.unit02 },
      { key: "won01", label: "Ganhas SC" },
      { key: "proposals01", label: "Propostas SC" },
      { key: "won02", label: "Ganhas ES" },
      { key: "proposals02", label: "Propostas ES" },
    ],
    rows: points.map((point) => ({
      periodo: point.periodo,
      conversion01: formatPct(point.conversion_filial_01),
      conversion02: formatPct(point.conversion_filial_02),
      won01: String(point.qtd_won_01),
      proposals01: String(point.qtd_proposals_01),
      won02: String(point.qtd_won_02),
      proposals02: String(point.qtd_proposals_02),
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
