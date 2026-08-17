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
  points: Array<
    CommercialRolSeriesPoint & {
      rol_matrix_prior?: number | null;
      rol_branch_prior?: number | null;
    }
  >,
  options: { includePriorYear?: boolean } = {},
): TableExportPayload {
  const includePrior = Boolean(options.includePriorYear);
  const columns = [
    { key: "periodo", label: "Período" },
    { key: "rolMatrix", label: ANALYTICS_ROL_SERIES_LABELS.unit01 },
    { key: "rolBranch", label: ANALYTICS_ROL_SERIES_LABELS.unit02 },
    ...(includePrior
      ? [
          { key: "rolMatrixPrior", label: `${ANALYTICS_ROL_SERIES_LABELS.unit01} (ano ant.)` },
          { key: "rolBranchPrior", label: `${ANALYTICS_ROL_SERIES_LABELS.unit02} (ano ant.)` },
        ]
      : []),
  ];
  return {
    title: "Evolução do ROL (R$)",
    columns,
    rows: points.map((point) => ({
      periodo: point.periodo,
      rolMatrix: formatCurrency(point.rol_matrix),
      rolBranch: formatCurrency(point.rol_branch),
      ...(includePrior
        ? {
            rolMatrixPrior:
              point.rol_matrix_prior == null
                ? "—"
                : formatCurrency(point.rol_matrix_prior),
            rolBranchPrior:
              point.rol_branch_prior == null
                ? "—"
                : formatCurrency(point.rol_branch_prior),
          }
        : {}),
    })),
  };
}

export function buildOverviewClosingRateSeriesPayload(
  points: Array<
    SalesConversionRateSeriesPoint & {
      conversion_filial_01_prior?: number | null;
      conversion_filial_02_prior?: number | null;
    }
  >,
  options: { includePriorYear?: boolean } = {},
): TableExportPayload {
  const includePrior = Boolean(options.includePriorYear);
  const columns = [
    { key: "periodo", label: "Período" },
    { key: "conversion01", label: ANALYTICS_CONVERSION_SERIES_LABELS.unit01 },
    { key: "conversion02", label: ANALYTICS_CONVERSION_SERIES_LABELS.unit02 },
    ...(includePrior
      ? [
          {
            key: "conversion01Prior",
            label: `${ANALYTICS_CONVERSION_SERIES_LABELS.unit01} (ano ant.)`,
          },
          {
            key: "conversion02Prior",
            label: `${ANALYTICS_CONVERSION_SERIES_LABELS.unit02} (ano ant.)`,
          },
        ]
      : []),
    { key: "won01", label: "Ganhas SC" },
    { key: "proposals01", label: "Propostas SC" },
    { key: "won02", label: "Ganhas ES" },
    { key: "proposals02", label: "Propostas ES" },
  ];
  return {
    title: "Evolução da taxa de conversão (%)",
    columns,
    rows: points.map((point) => ({
      periodo: point.periodo,
      conversion01: formatPct(point.conversion_filial_01),
      conversion02: formatPct(point.conversion_filial_02),
      ...(includePrior
        ? {
            conversion01Prior: formatPct(point.conversion_filial_01_prior),
            conversion02Prior: formatPct(point.conversion_filial_02_prior),
          }
        : {}),
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
