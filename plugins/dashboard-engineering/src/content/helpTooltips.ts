export const ENGINEERING_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores estratégicos de engenharia: LMPs no prazo e ganhos do programa TRANSFORMA+.",
    refresh: "Recarrega KPIs de LMP e TRANSFORMA+ com os filtros atuais.",
  },
  filters: {
    competence:
      "Mês de referência (aaaa-mm). Ao selecionar, ajusta o período para o mês inteiro — ou até hoje, no mês corrente. Fica vazio quando o período abrange mais de um mês.",
    dateStart:
      "Início do período para LMP e TRANSFORMA+. KPIs e gráficos usam propostas/melhorias a partir desta data.",
    dateEnd: "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Unidade TOTVS. Vazio = consolidado; múltiplas unidades restringem o recorte dos indicadores.",
    listingType:
      "Classificação da listagem (LMP, Amostra ou Outro). Vazio = todos os tipos.",
    status:
      "Status de classificação de prazo (Pontual, Atrasado, Andamento, Retornada). Vazio = todos.",
  },
  kpis: {
    lmpOnTime:
      "Percentual de LMPs/propostas classificadas como dentro do prazo no período e unidade.",
    avgLeadTime:
      "Média de lead time útil (dias úteis) das propostas no recorte filtrado.",
    totalProposals:
      "Quantidade de propostas/LMPs/amostras consideradas no período.",
    transformaSavings:
      "Ganhos brutos registrados no programa TRANSFORMA+ no período (planilha).",
    implementedSolutions:
      "Quantidade de soluções/melhorias implementadas no TRANSFORMA+.",
    averageRoi:
      "Retorno sobre investimento no recorte: economia líquida ÷ investimento total (razão da API × 100). Mesmo cálculo do dashboard Transformômetro.",
    netSavings: "Economia líquida acumulada no recorte filtrado.",
    hoursSaved: "Total de horas economizadas pelas soluções implementadas.",
    listedProcesses: "Quantidade de processos listados com os filtros aplicados.",
    avgLeadTimeUseful: "Média de lead time útil (dias úteis) das propostas LMP.",
  },
  charts: {
    lmpEvolution: "Evolução temporal dos indicadores de LMP.",
    transformaEvolution: "Evolução dos ganhos TRANSFORMA+ no período.",
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
