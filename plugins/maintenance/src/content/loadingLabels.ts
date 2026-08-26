import type { LoadingActivityCardLabels } from "@delpi/plugin-ui/index";

export const MAINTENANCE_LOADING_LABELS: LoadingActivityCardLabels = {
  progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
  progressAriaDeterminate: (remainingPercent: number) =>
    `Carregamento: faltam ${remainingPercent} por cento`,
  progressAriaIndeterminate: "Carregamento em andamento",
};

export const MAINTENANCE_LOADING_TITLES = {
  default: "Carregando…",
  filiais: "Carregando filiais…",
  ferramentas: "Carregando ferramentas…",
  relatorio: "Carregando relatório preventivo…",
  configuracao: "Carregando configuração…",
  detalhe: "Carregando detalhes…",
  grafico: "Carregando histórico…",
  revisao: "Carregando revisão programada…",
  programas: "Carregando programas de máquina…",
  manutencaoGeral: "Carregando formulário…",
  home: "Carregando filiais e submódulos…",
} as const;
