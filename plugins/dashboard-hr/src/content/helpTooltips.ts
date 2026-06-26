export const HR_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores de RH: absenteísmo, turnover, satisfação interna, PDI e horas de treinamento.",
    refresh: "Recarrega os indicadores com período e filial selecionados.",
  },
  filters: {
    dateStart: "Início do período para os indicadores de RH.",
    dateEnd: "Fim do período. Deve ser igual ou posterior ao início.",
    branch:
      "Filial TOTVS. Vazio = média/consolidado das filiais; múltiplas filiais restringem o recorte.",
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
    branch: "Filial TOTVS do registro.",
  },
} as const;
