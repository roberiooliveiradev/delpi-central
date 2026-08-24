import type { AdminEngagementTopUser } from "../../../data/adminApi";
import { formatGeneratedAt } from "./StatsShared";
import { formatDuration } from "./engagementFormatting";

export const ENGAGEMENT_PERIOD_OPTIONS = [
  { value: 7 as const, label: "7 dias" },
  { value: 30 as const, label: "30 dias" },
  { value: 90 as const, label: "90 dias" },
];

export const ENGAGEMENT_LABELS = {
  pageTitle: "Engajamento da plataforma",
  pageDescription:
    "Atividade, tempo de uso, rankings de apps e usuários mais presentes no portal.",
  dau: "DAU",
  wau: "WAU",
  mau: "MAU",
  stickiness: "Stickiness",
  avgPortalTime: "Tempo médio no portal",
  avgAppTime: "Tempo médio por app",
  topAppsOpens: "Top apps — aberturas",
  topAppsDuration: "Top apps — tempo total",
  topAppsUnique: "Top apps — usuários únicos",
  topUsers: "Usuários mais ativos",
  topRoutes: "Rotas mais acessadas",
  activeUsersSeries: "Usuários ativos por dia",
  durationSeries: "Tempo total por dia",
  chartHoverHint: "Passe o mouse sobre o gráfico para ver os valores.",
  coverage: "Cobertura de rastreamento",
  viewEngagement: "Ver engajamento completo",
  mostActiveUsers: "Mais ativos no período",
  emptyRankings: "Sem dados de engajamento no período selecionado.",
  trackingDisabled:
    "Rastreamento de uso desabilitado no servidor — métricas de tempo podem estar incompletas.",
};

export function formatSeriesDateLabel(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(isoDate);
  if (!match) {
    return isoDate;
  }

  return `${match[3]}/${match[2]}`;
}

export function formatEngagementUserRow(user: AdminEngagementTopUser) {
  return {
    primary: user.name,
    secondary: user.email,
    metrics: [
      `${user.totalOpens} aberturas`,
      `${user.appsUsed} apps`,
      formatDuration(user.totalDurationSeconds),
    ],
    lastUsage: user.lastAppUsageAt
      ? formatGeneratedAt(user.lastAppUsageAt)
      : "—",
  };
}
