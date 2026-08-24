// portal/src/ui/usage/userUsageLabels.ts

export const USER_USAGE_PERIOD_OPTIONS = [
  { value: 7 as const, label: "7 dias" },
  { value: 30 as const, label: "30 dias" },
  { value: 90 as const, label: "90 dias" },
];

export const USER_USAGE_LABELS = {
  periodLabel: "Período:",
  updatedAt: "Atualizado:",
  loading: "Carregando uso…",
  retry: "Tentar novamente",
  emptyRankings: "Nenhum dado de uso no período selecionado.",
  emptyRoutes: "Nenhuma rota registrada no período.",
  consentDisabled:
    "Rastreamento de uso desativado para este usuário. Métricas abaixo refletem zero eventos no período.",
  consentDisabledAdminNote:
    "O titular pode ativar o rastreamento nas preferências de privacidade.",
  consentCta: "Ativar nas preferências de privacidade",
  trackingDisabledServer:
    "Rastreamento de uso desabilitado no servidor — métricas de tempo podem estar incompletas.",
  adminPanelTitle: "Uso na plataforma",
  adminPanelHint:
    "Engajamento individual nos últimos dias · respeita consentimento LGPD",
  myUsageTitle: "Meu uso na plataforma",
  myUsageHint: "Como você utiliza o portal e os aplicativos",
  totalOpens: "Aberturas no período",
  appsUsed: "Apps usados",
  totalDuration: "Tempo total",
  portalDuration: "Tempo no portal",
  avgSession: "Sessão média",
  lastUsage: "Último uso",
  opensSeries: "Aberturas por dia",
  durationSeries: "Tempo de uso por dia",
  topAppsOpens: "Apps mais abertos",
  topAppsDuration: "Apps com mais tempo",
  topRoutes: "Rotas mais visitadas",
  coverage: "Cobertura de rastreamento",
  chartHoverHint: "Passe o mouse sobre o gráfico para ver os valores.",
  opensSuffix: "aberturas",
};
