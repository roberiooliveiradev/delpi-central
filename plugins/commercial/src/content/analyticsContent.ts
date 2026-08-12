export const ANALYTICS_CONTENT = {
  nav: {
    overview: "Visão geral",
    otd: "OTD",
    equipe: "Equipe",
    oportunidades: "Oportunidades",
  },
  overview: {
    title: "Visão geral",
    subtitle:
      "Indicadores do período, evolução de ROL e funil de conversão. OTD e Oportunidades abrem pelo Início.",
    filters: "Período, filial e segmento aplicados a todos os painéis desta página.",
    rolKpi: "ROL da matriz versus meta no período filtrado.",
    branchRolKpi: "ROL da filial selecionada versus meta.",
    closingKpi: "Taxa de conversão: propostas ganhas ÷ total de propostas.",
    otdKpi: "On-time delivery de linhas de pedido de venda.",
    newBusinessKpi: "Participação de novos negócios no ROL do período.",
    rolSeries: "Evolução do ROL matriz e filial no período.",
    funnel: "Funil de conversão (propostas → ganhas).",
    chartEmpty: {
      rolLoading: "Carregando evolução de ROL…",
      rolError: "Erro ao carregar série de ROL.",
      rolTitle: "Sem evolução no período",
      rolMessage: "Não há pontos de ROL para os filtros atuais. Ajuste datas, filial ou segmento.",
      funnelTitle: "Sem funil no período",
      funnelMessage: "Não há propostas no período filtrado para montar o funil de conversão.",
    },
  },
  otd: {
    title: "OTD de pedidos",
    subtitle: "Painel de on-time delivery por linha de pedido de venda.",
    lineDetail: "Detalhe da linha de pedido selecionada.",
  },
  equipe: {
    title: "Equipe",
    subtitle: "Carteiras ativas com contagem de clientes e resumo de pedidos em aberto.",
  },
  oportunidades: {
    title: "Oportunidades",
    subtitle: "Lista de OVs/propostas comerciais do período.",
    detail:
      "Detalhe da oportunidade: indicadores, dados comerciais, produtos, estrutura de componentes e histórico.",
  },
  filters: {
    start: "Data inicial",
    end: "Data final",
    competence: "Competência (mês)",
    branch: "Filial",
    segment: "Segmento",
    segmentAll: "Todos",
    segmentWeg: "WEG",
    segmentNewBusiness: "Novos negócios",
  },
};

export const PROPOSALS_CONTENT = {
  list: {
    title: "Propostas comerciais",
    subtitle: "Consulta de propostas comerciais ativas (documentos).",
    scopeNote:
      "O chip Escopo no topo identifica sua sessão de carteira; esta lista de propostas documento não filtra por carteira — é o catálogo com permissão de propostas.",
    search: "Buscar por OV, proposta interna, oportunidade ou cliente.",
    empty: "Nenhuma proposta encontrada.",
    emptySearch: "Ajuste a busca ou limpe o filtro para ver a lista completa.",
  },
  detail: {
    title: "Proposta comercial",
    exportPdf: "Emitir PDF",
    back: "Voltar",
    items: "Itens",
  },
};
