import type { OverviewTemporalNature } from "../../api/overview";

export const OVERVIEW_CONTENT = {
  title: "Visão geral",
  eyebrow: "Portal Suprimentos",
  description:
    "Indicadores do período no seu escopo. O Início é para ação e descoberta — não use a Visão geral como fila operacional.",
  helpAriaLabel: "Ajuda: Visão geral e natureza temporal",
  scopeBadgeAll: "Consolidado (filiais liberadas)",
  scopeBadgeBranch: (branch: string) => `Filial ${branch}`,
  branchAll: "Todas as liberadas",
  branchLabel: "Filial",
  periodPresetLabel: "Período",
  periodFromLabel: "De",
  periodToLabel: "Até",
  filtersAriaLabel: "Filtros da Visão geral",
  reloadLabel: "Atualizar",
  loading: "Carregando indicadores…",
  loadingKpisTitle: "Carregando indicadores",
  error: "Não foi possível carregar a Visão geral.",
  forbiddenUnit:
    "Você não tem permissão para esta filial neste módulo. Escolha outra unidade liberada ou peça o acesso canônico ao administrador.",
  empty: "Nenhum indicador disponível para este recorte.",
  unavailable: "Indisponível",
  partialNote: "Alguns indicadores falharam; o restante permanece utilizável.",
  indicatorsTitle: "Indicadores",
  indicatorsHint:
    "Cada card mostra a natureza temporal (intervalo, snapshot ou estado) e a meta quando houver.",
  otdChartTitle: "OTD no tempo",
  otdChartHint: "Evolução mensal do OTD de pedidos de compra no recorte filtrado.",
  otdChartLoading: "Carregando série OTD…",
  otdChartEmptyTitle: "Sem pontos de OTD",
  otdChartEmptyMessage: "Não há série OTD para este período e filial.",
  otdChartError: "Não foi possível carregar a série OTD.",
  otdSeriesLabel: "OTD %",
  compareTitle: "Comparativo no período",
  compareHint: "Valor × meta dos indicadores de intervalo disponíveis no overview — sem série inventada.",
  compareLoading: "Montando comparativo…",
  compareEmptyTitle: "Sem comparativo",
  compareEmptyMessage: "Não há KPIs de intervalo com valor e meta neste recorte.",
  compareValueLabel: "Valor",
  compareMetaLabel: "Meta",
  temporalLabels: {
    interval: "Intervalo",
    snapshot: "Snapshot",
    state: "Estado atual",
  } satisfies Record<OverviewTemporalNature, string>,
} as const;

export function firstDayOfMonthIso(today = new Date()): string {
  const y = today.getFullYear();
  const m = String(today.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}-01`;
}

export function todayIso(today = new Date()): string {
  const y = today.getFullYear();
  const m = String(today.getMonth() + 1).padStart(2, "0");
  const d = String(today.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function temporalNatureLabel(nature: OverviewTemporalNature): string {
  return OVERVIEW_CONTENT.temporalLabels[nature];
}

export function mapOverviewFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return OVERVIEW_CONTENT.forbiddenUnit;
  }
  return message || OVERVIEW_CONTENT.error;
}
