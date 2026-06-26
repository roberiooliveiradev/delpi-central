export const SUPPLIES_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores de suprimentos no TOTVS: CPV, pontualidade de compras, estoque, giro e economia em negociações.",
    refresh:
      "Recarrega KPIs e gráficos com os filtros atuais (período, filial e localização).",
  },
  filters: {
    dateStart:
      "Início do período. KPIs e gráficos consideram movimentos e saldos a partir desta data.",
    dateEnd: "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Filial TOTVS para CPV, OTD, estoque e economia. Vazio = consolidado; múltiplas filiais comparam o recorte selecionado.",
    location:
      "Código de localização de estoque (armazém). Vazio = todas as localizações no recorte de filial.",
  },
  kpis: {
    cpvTotal:
      "Custo dos Produtos Vendidos no período (movimentos SD3 classificados como CPV). Meta alinhada ao catálogo de Indicadores Estratégicos quando configurada.",
    cpvRol:
      "Participação do CPV sobre o ROL com IPI no mesmo período. Quanto menor, melhor quando a meta é de redução.",
    otdPurchases:
      "Percentual de linhas de pedido de compra recebidas no prazo prometido (data de recebimento ≤ data prometida).",
    stockValue:
      "Valor total do estoque (SB9) no recorte de filial e localização selecionados.",
    inventoryTurnoverMonths:
      "Giro de estoque em meses: relação entre saldo médio e CPV mensalizado no período.",
    negotiationSavings:
      "Economia registrada em negociações de compras na planilha IDD Suprimentos (Google Sheets).",
    cpvMovements: "Quantidade de movimentos SD3 considerados no cálculo do CPV.",
    avgCostPerUnit: "Custo médio por unidade nos movimentos de CPV do período.",
    otd: "Percentual de pontualidade (OTD) das linhas de compra recebidas no período.",
    onTimeLines: "Linhas de compra recebidas dentro do prazo prometido.",
    lateLines: "Linhas de compra recebidas após a data prometida.",
    turnoverMonths: "Giro de estoque expresso em meses de cobertura.",
    turnoverTimes: "Giro em vezes: CPV total dividido pelo valor de estoque.",
    stockQuantity: "Quantidade total em estoque no recorte filtrado.",
    locations: "Quantidade de localizações com saldo registrado.",
    avgUnitValue: "Valor médio por unidade em estoque (custo unitário médio).",
    savingsTotal: "Soma da economia em negociações no período e filial selecionados.",
    savingsEntries: "Quantidade de lançamentos na planilha IDD no recorte.",
    savingsPeriod: "Economia acumulada no intervalo de datas filtrado.",
  },
  charts: {
    cpvByCfop: "Distribuição do CPV por código fiscal de operação (CFOP).",
    cpvByTm: "Distribuição do CPV por tipo de movimento (TES/TM) no SD3.",
    otdEvolution: "Evolução mensal da pontualidade de compras (OTD).",
    lateSuppliers: "Fornecedores com maior volume de linhas em atraso no período.",
    stockByLocation: "Valor de estoque agrupado por localização (armazém).",
    stockByBranch: "Valor de estoque consolidado por filial TOTVS.",
    savingsByBranch: "Economia em negociações agrupada por filial.",
    percentIndicators: "Comparativo visual de indicadores percentuais do módulo.",
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
