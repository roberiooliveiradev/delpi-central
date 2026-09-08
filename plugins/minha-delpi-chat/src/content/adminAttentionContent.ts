/**
 * Copy e limiares da fila de atenção do Painel admin (feature-help-sync).
 * Textos PT de negócio — sem operationId / paths de API.
 */

export const ADMIN_ATTENTION = {
  sectionTitle: "Fila de atenção",
  sectionDescription:
    "Itens que pedem ação nas últimas 24 horas. Clique para abrir a seção correspondente.",
  empty: "Nada urgente nas últimas 24 horas.",
  openAction: "Abrir",
  severityCritical: "Crítico",
  severityWarning: "Atenção",
  severityInfo: "Info",
  toolErrorTitle: "Ferramenta com falha",
  toolWarningTitle: "Ferramenta com alerta",
  toolDetail: "{label}: {description}",
  blockedTitle: "Bloqueios de segurança",
  blockedDetail: "{count} bloqueio(s) nas últimas 24 horas.",
  pendingCandidatesTitle: "Candidatos de aprendizagem pendentes",
  pendingCandidatesDetail: "{count} item(ns) aguardando revisão humana.",
  failingEvalTitle: "Casos de regressão falhando",
  failingEvalDetail: "{count} caso(s) de avaliação com falha.",
  errorRateTitle: "Taxa de erro elevada",
  errorRateDetail: "Taxa de erro nas últimas 24 horas: {rate}.",
  lowEvalScoreTitle: "Avaliações humanas com nota baixa",
  lowEvalScoreDetail: "Média {score} em {count} avaliação(ões) recentes.",
  thresholds: {
    errorRateWarning: 0.05,
    errorRateCritical: 0.15,
    lowAverageScore: 3,
  },
} as const;

export type AdminAttentionContent = typeof ADMIN_ATTENTION;
