export const FINANCIAL_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores financeiros do TOTVS: ROL, EBITDA, custos fixos e prazo médio de recebimento (PMR).",
    refresh: "Recarrega KPIs e gráficos com período e unidade selecionados.",
  },
  filters: {
    competence:
      "Mês de referência (aaaa-mm). Ao selecionar, ajusta o período para o mês inteiro — ou até hoje, no mês corrente. Fica vazio quando o período abrange mais de um mês.",
    dateStart:
      "Início do período. KPIs e gráficos usam o intervalo a partir desta data.",
    dateEnd: "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Unidade TOTVS para ROL, EBITDA, custos fixos e PMR. Vazio = consolidado; múltiplas unidades restringem o recorte exibido.",
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
    rol: "ROL consolidada ou por unidade conforme o filtro aplicado.",
    rolWithIpiDetail: "ROL com impostos (IPI) incluídos na base de cálculo.",
    ebitdaValue: "Valor absoluto de EBITDA no período.",
    fixedCostValue: "Valor absoluto de custos fixos no período.",
    pmr: "PMR em dias para o recorte de período e unidade.",
  },
  charts: {
    percentIndicators:
      "Comparativo de EBITDA/ROL e custos fixos/ROL no recorte filtrado.",
    ebitdaByBranch: "EBITDA sobre ROL por unidade TOTVS.",
    fixedCostByBranch: "Custos fixos sobre ROL por unidade.",
    pmrByBranch: "PMR em dias por unidade.",
  },
  pagination: {
    info: "Paginação: busca, ordenação e tamanho da página são aplicados na consulta ou na página atual.",
    pageSize: "Define quantos registros são exibidos por página (10, 20, 50 ou 100).",
    jump: "Digite o número da página e pressione Enter ou saia do campo.",
    jumpEmpty: "Informe um número de página.",
    jumpInvalid: "Use apenas números inteiros.",
    jumpBelowMin: "A página mínima é 1.",
    previous: "Volta uma página mantendo busca, ordenação e tamanho da lista.",
    next: "Avança uma página mantendo busca, ordenação e tamanho da lista.",
  },
  table: {
    section: "Listagem do período filtrado. Clique na linha para ver o detalhe quando disponível.",
    search: "Filtra os registros visíveis por texto nas colunas principais.",
    branch: "Unidade TOTVS do registro.",
  },
} as const;
