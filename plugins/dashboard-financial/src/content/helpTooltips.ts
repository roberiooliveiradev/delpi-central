export const FINANCIAL_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores financeiros do TOTVS: ROL, EBITDA, custos fixos e prazo médio de recebimento (PMR).",
    refresh: "Recarrega KPIs e gráficos com período e filial selecionados.",
  },
  kpis: {
    rolWithIpi:
      "Receita Operacional Líquida com IPI no período (vendas SD2 menos devoluções, conforme regra do indicador).",
    ebitdaOverRol:
      "Percentual de EBITDA sobre o ROL. Meta alinhada ao catálogo de Indicadores Estratégicos quando configurada.",
    fixedCostOverRol:
      "Peso dos custos fixos sobre o ROL no período. Quanto menor, melhor quando a meta é de redução.",
    pmrDays:
      "Prazo Médio de Recebimento em dias: média ponderada entre emissão e recebimento dos títulos.",
    rol: "ROL consolidada ou por filial conforme o filtro aplicado.",
    rolWithIpiDetail: "ROL com impostos (IPI) incluídos na base de cálculo.",
    ebitdaValue: "Valor absoluto de EBITDA no período.",
    fixedCostValue: "Valor absoluto de custos fixos no período.",
    pmr: "PMR em dias para o recorte de período e filial.",
  },
  charts: {
    percentIndicators:
      "Comparativo de EBITDA/ROL e custos fixos/ROL no recorte filtrado.",
    ebitdaByBranch: "EBITDA sobre ROL por filial TOTVS.",
    fixedCostByBranch: "Custos fixos sobre ROL por filial.",
    pmrByBranch: "PMR em dias por filial.",
  },
} as const;
