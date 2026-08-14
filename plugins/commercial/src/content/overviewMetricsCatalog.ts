/**
 * Catálogo de métricas da Visão geral — labels, tooltips e ids estáveis.
 * OverviewPage e docs consomem estas chaves; não espalhar textos de KPI no JSX.
 */
export type OverviewMetricId =
  | "rol"
  | "rol_weg"
  | "rol_new_business"
  | "closing_rate"
  | "otd"
  | "new_business_pct"
  | "open_portfolio"
  | "portfolio_billing_share"
  | "gap_to_target"
  | "open_portfolio_horizon"
  | "rol_series"
  | "closing_rate_series"
  | "funnel";

export type OverviewMetricDefinition = {
  id: OverviewMetricId;
  label: string;
  tooltip: string;
};

export const OVERVIEW_METRICS: readonly OverviewMetricDefinition[] = [
  {
    id: "rol",
    label: "ROL",
    tooltip: "Receita operacional líquida consolidada versus meta por unidade.",
  },
  {
    id: "rol_weg",
    label: "ROL WEG",
    tooltip: "ROL do segmento WEG versus meta por unidade.",
  },
  {
    id: "rol_new_business",
    label: "ROL Novos Negócios",
    tooltip: "ROL de novos negócios versus meta por unidade.",
  },
  {
    id: "closing_rate",
    label: "Taxa de conversão",
    tooltip:
      "Hit rate: propostas ganhas (status TOTVS 9, aceite no período) ÷ revisões abertas no período. Cohorts de numerador e denominador podem diferir.",
  },
  {
    id: "open_portfolio",
    label: "Carteira em aberto",
    tooltip:
      "Saldo comercial agora (valor e linhas de pedidos). Não é programação do PCP, não é forecast e não some com o ROL do período.",
  },
  {
    id: "portfolio_billing_share",
    label: "Share empresa",
    tooltip:
      "Percentual do ROL do escopo atual sobre o ROL consolidado da empresa no mesmo período. Não mistura com carteira em aberto.",
  },
  {
    id: "gap_to_target",
    label: "Gap vs meta",
    tooltip:
      "Quanto falta para a meta ROL SI do período (max(meta − ROL, 0)). Carteira do mês é só contexto — não some com o gap.",
  },
  {
    id: "open_portfolio_horizon",
    label: "Carteira no tempo",
    tooltip:
      "Valor aberto por data de entrega (atrasado, este mês, 1–3 meses, depois, sem data). Clique abre Meus pedidos filtrados.",
  },
  {
    id: "otd",
    label: "OTD — pedidos de venda",
    tooltip: "On-time delivery de linhas de pedido de venda.",
  },
  {
    id: "new_business_pct",
    label: "% ROL — novos negócios",
    tooltip: "Participação de novos negócios no ROL do período.",
  },
  {
    id: "rol_series",
    label: "Evolução do ROL (R$)",
    tooltip: "Evolução do ROL por Santa Catarina e Espírito Santo no período.",
  },
  {
    id: "closing_rate_series",
    label: "Evolução da taxa de conversão (%)",
    tooltip:
      "Hit rate ao longo do tempo por unidade (SC/ES). Mesma fórmula do KPI: ganhas com aceite no bucket ÷ revisões abertas no bucket.",
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
