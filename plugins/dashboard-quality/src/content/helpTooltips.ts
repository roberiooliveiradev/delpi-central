export const QUALITY_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores de qualidade: PPM interno/externo, kaizens, auditorias 5S e não conformidades.",
    refresh: "Recarrega PPM, kaizens e auditorias com os filtros atuais.",
  },
  filters: {
    competence:
      "Mês de referência (aaaa-mm). Ao selecionar, ajusta o período para o mês inteiro — ou até hoje, no mês corrente. Fica vazio quando o período abrange mais de um mês.",
    dateStart: "Início do período para PPM, kaizens e auditorias 5S.",
    dateEnd: "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Unidade TOTVS. Vazio = todas; múltiplas unidades restringem o recorte dos indicadores.",
  },
  kpis: {
    ppmInternal:
      "Parts Per Million interno: devoluções internas por milhão de unidades produzidas no período.",
    ppmExternal:
      "PPM externo: devoluções de clientes por milhão de unidades faturadas.",
    kaizenOpen: "Quantidade de kaizens abertos ou em andamento no recorte.",
    kaizenClosed: "Kaizens concluídos no período filtrado.",
    kaizenTotal: "Total de kaizens registrados no período conforme filtros aplicados.",
    kaizenFinancialGains:
      "Ganhos financeiros do kaizen no período: soma de daily_savings × dias ativos de cada melhoria implantada. Meta do indicador Ganhos Financeiros Kaizen/mês (Indicadores Estratégicos).",
    kaizenSavings:
      "Mesmo valor dos ganhos financeiros do kaizen — economia acumulada no período filtrado.",
    audit5sScore: "Nota média das auditorias 5S realizadas no período.",
    audit5sCount: "Quantidade de auditorias 5S registradas no recorte.",
    nonconformities: "Total de não conformidades abertas ou registradas no período.",
    ppmDetail: "PPM calculado com base em unidades devolvidas e produzidas/faturadas.",
    ppmReturned: "Quantidade total de unidades devolvidas no período.",
  },
  charts: {
    ppmEvolution: "Evolução temporal do PPM conforme granularidade selecionada.",
    kaizenByStatus: "Distribuição de kaizens por status no período.",
    audit5sEvolution: "Evolução das notas de auditoria 5S ao longo do tempo.",
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
