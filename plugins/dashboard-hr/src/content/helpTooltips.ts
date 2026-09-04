export const HR_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores de RH alinhados ao catálogo de Indicadores Estratégicos: absenteísmo, turnover, satisfação, PDIs, avaliações e treinamento.",
    refresh: "Recarrega os indicadores com período e unidade selecionados.",
  },
  filters: {
    competence:
      "Mês de referência (aaaa-mm). Ao selecionar, ajusta o período para o mês inteiro — ou até hoje, no mês corrente. Fica vazio quando o período abrange mais de um mês.",
    dateStart: "Início do período para os indicadores de RH.",
    dateEnd: "Fim do período. Deve ser igual ou posterior ao início.",
    branch:
      "Unidade TOTVS. Vazio = consolidado: realizado e meta SI agregam as filiais; múltiplas unidades restringem o recorte. Só aparece aviso para filtrar unidade se o SI não puder agregar a meta.",
  },
  kpis: {
    absenteeism:
      "Percentual de absenteísmo versus meta SI. Com unidade Todas, realizado e meta agregam pelo SI (não é média inventada no MFE).",
    turnover:
      "Percentual de turnover versus meta SI. Em consolidado, meta e realizado agregam pelo SI.",
    internalSatisfaction:
      "Índice de satisfação interna versus meta SI no período (fonte configurada na API). Em consolidado, agregação pelo SI.",
    activePdi:
      "Quantidade de PDIs ativos no período (contagem) versus meta SI. Em consolidado, agregação pelo SI.",
    performanceReviews:
      "Percentual de avaliações de desempenho finalizadas versus meta SI. Em consolidado, agregação pelo SI.",
    trainingHours:
      "Média de horas de treinamento por colaborador versus meta SI. Em consolidado, agregação pelo SI.",
  },
  charts: {
    absenteeismTurnoverByBranch:
      "Comparativo de absenteísmo e turnover por unidade quando nenhuma unidade específica está selecionada.",
    trainingByBranch: "Horas de treinamento por colaborador agrupadas por unidade.",
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
