/**
 * Catálogo de métricas da Visão geral — labels, tooltips e ids estáveis.
 * OverviewPage e docs consomem estas chaves; não espalhar textos de KPI no JSX.
 */
export type OverviewMetricId =
  | "rol_head_office"
  | "rol_branch"
  | "closing_rate"
  | "otd"
  | "new_business"
  | "rol_series"
  | "funnel";

export type OverviewMetricDefinition = {
  id: OverviewMetricId;
  label: string;
  tooltip: string;
};

export const OVERVIEW_METRICS: readonly OverviewMetricDefinition[] = [
  {
    id: "rol_head_office",
    label: "ROL vs meta",
    tooltip: "ROL consolidado versus meta no período filtrado.",
  },
  {
    id: "rol_branch",
    label: "ROL por unidade",
    tooltip: "ROL por unidade (Santa Catarina / Espírito Santo) versus meta.",
  },
  {
    id: "closing_rate",
    label: "Conversão",
    tooltip: "Taxa de conversão: propostas ganhas ÷ total de propostas.",
  },
  {
    id: "otd",
    label: "OTD",
    tooltip: "On-time delivery de linhas de pedido de venda.",
  },
  {
    id: "new_business",
    label: "Novos negócios",
    tooltip: "Participação de novos negócios no ROL do período.",
  },
  {
    id: "rol_series",
    label: "Evolução do ROL (R$)",
    tooltip: "Evolução do ROL por Santa Catarina e Espírito Santo no período.",
  },
  {
    id: "funnel",
    label: "Funil de conversão",
    tooltip: "Funil de conversão (propostas → ganhas).",
  },
] as const;

export const OVERVIEW_METRIC_BY_ID: Readonly<Record<OverviewMetricId, OverviewMetricDefinition>> =
  Object.fromEntries(OVERVIEW_METRICS.map((item) => [item.id, item])) as Record<
    OverviewMetricId,
    OverviewMetricDefinition
  >;

export function overviewMetricTooltip(id: OverviewMetricId): string {
  return OVERVIEW_METRIC_BY_ID[id].tooltip;
}
