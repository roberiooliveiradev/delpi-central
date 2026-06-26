export const HR_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores de RH: absenteísmo, turnover, satisfação interna, PDI e horas de treinamento.",
    refresh: "Recarrega os indicadores com período e filial selecionados.",
  },
  kpis: {
    absenteeism:
      "Percentual de absenteísmo no período. Com filial Todas, exibe média das filiais com dado.",
    turnover:
      "Percentual de turnover no período. Meta alinhada ao catálogo de Indicadores Estratégicos.",
    internalSatisfaction:
      "Índice de satisfação interna consolidado no período (fonte configurada na API).",
    activePdi:
      "Percentual de colaboradores com PDI ativo no recorte de filial ou média das filiais.",
    trainingHours:
      "Média de horas de treinamento por colaborador no período filtrado.",
  },
  charts: {
    absenteeismTurnoverByBranch:
      "Comparativo de absenteísmo e turnover por filial quando nenhuma filial específica está selecionada.",
    trainingByBranch: "Horas de treinamento por colaborador agrupadas por filial.",
  },
} as const;
