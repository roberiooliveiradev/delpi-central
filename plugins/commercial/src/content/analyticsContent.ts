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
    filters:
      "Período, unidade (Santa Catarina / Espírito Santo) e segmento aplicados a todos os painéis desta página.",
    rolKpi: "ROL consolidado versus meta no período filtrado.",
    branchRolKpi: "ROL por unidade versus meta no período filtrado.",
    closingKpi: "Taxa de conversão: propostas ganhas ÷ total de propostas.",
    otdKpi: "On-time delivery de linhas de pedido de venda.",
    newBusinessKpi: "Participação de novos negócios no ROL do período.",
    rolSeries:
      "Evolução do ROL por Santa Catarina e Espírito Santo no período.",
    funnel: "Funil de conversão (propostas → ganhas).",
    funnelFootnote:
      "Largura das etapas proporcional ao volume; números absolutos em cada faixa. Ganhas = propostas com status TOTVS 9 e aceite (AD1_DTASSI) no período filtrado.",
    chartEmpty: {
      rolLoading: "Carregando evolução de ROL…",
      rolError: "Erro ao carregar série de ROL.",
      rolTitle: "Sem evolução no período",
      rolMessage:
        "Não há pontos de ROL para os filtros atuais. Ajuste datas, unidade ou segmento.",
      funnelTitle: "Sem funil no período",
      funnelMessage: "Não há propostas no período filtrado para montar o funil de conversão.",
    },
  },
  otd: {
    title: "Pontualidade (OTD)",
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
    accountHint:
      "Oportunidades (OV) deste cliente. Clique na linha ou no número para abrir o detalhe.",
    detail:
      "Detalhe da oportunidade: indicadores, dados comerciais, produtos, estrutura de componentes e histórico.",
    openProposal: "Abrir proposta",
    openProposalBusy: "Abrindo…",
    openProposalEmpty:
      "Não há documento ADY vinculado a esta OV. A proposta pode não ter sido gerada ainda.",
    openProposalError: "Não foi possível localizar a proposta ADY desta OV.",
    openProposalMultipleHint: "Há mais de um documento ADY; abrimos o mais recente.",
    openProposalReturnLabel: "Oportunidade",
  },
  filters: {
    start: "Data inicial",
    end: "Data final",
    competence: "Competência (mês)",
    branch: "Unidade (indicadores)",
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
      "O menu do usuário no topo leva a Minha Carteira filtrada; esta lista de propostas-documento não filtra por carteira — é o catálogo com permissão de propostas.",
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
