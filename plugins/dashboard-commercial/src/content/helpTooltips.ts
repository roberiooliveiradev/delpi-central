export const COMMERCIAL_HELP_TOOLTIPS = {
  filters: {
    dateStart:
      "Início do período. KPIs, gráficos e tabela usam propostas com abertura (AD1_DATA) a partir desta data.",
    dateEnd:
      "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Filial TOTVS para conversão, OTD, ROL e % novos negócios. Vazio = consolidado de todas as filiais.",
    customerSegment:
      "WEG = cliente código 000001 (todas as lojas). Novos negócios = demais clientes. Afeta ROL, conversão, OTD, % novos negócios, gráfico de ROL e tabela de propostas.",
    proposalStatus:
      "Filtra a tabela: todas (abertura AD1_DATA no período), ganhas (status 9 com aceite AD1_DTASSI no período) ou em aberto.",
  },
  actions: {
    pageSubtitle:
      "Indicadores comerciais do TOTVS: ROL por filial, taxa de conversão de propostas, OTD de pedidos e participação de novos negócios no ROL.",
    refresh:
      "Recarrega KPIs, gráficos e tabela com os filtros atuais (período e filial).",
    print:
      "Gera relatório para impressão com o resumo do período e indicadores visíveis.",
    back:
      "Retorna ao dashboard comercial preservando período e filial na URL.",
    detailRefresh:
      "Atualiza cabeçalho da OV e histórico de processo/estágio no TOTVS.",
    totvsBanner:
      "Dados extraídos do Protheus (AD1010, SD2, SC5/SC6). Metas vêm do módulo Indicadores Estratégicos quando configuradas.",
  },
  pagination: {
    info: "Paginação local dos registros já carregados, respeitando busca e ordenação.",
    previous: "Volta uma página mantendo busca e ordenação.",
    next: "Avança uma página mantendo busca e ordenação.",
  },
  kpis: {
    rol: "ROL (R$ com IPI) no período. Com filial Todas, exibe soma ou comparativo das filiais 01 e 02 conforme o card.",
    salesOrderOtd:
      "Percentual de linhas de pedido de venda entregues no prazo (data de faturamento ≤ data de entrega prometida).",
    closingRate:
      "Taxa de conversão: ganhas com aceite (AD1_DTASSI) no período sobre propostas abertas (AD1_DATA) no período.",
    newBusinessRol:
      "Participação do ROL de clientes não-WEG no ROL total do período (vendas SD2 menos devoluções).",
  },
  charts: {
    rolEvolution:
      "Evolução do ROL por filial 01 (matriz) e 02. Clique em um ponto para ajustar o período ao intervalo selecionado.",
    rolGranularity:
      "Agrupa os pontos do gráfico por dia, semana ou mês conforme o intervalo filtrado.",
    rolExport:
      "Exporta a série visível do gráfico de ROL para arquivo CSV.",
    conversionFunnel:
      "Volume de propostas abertas no período, ganhas (status 9) e sem conversão. Largura proporcional ao volume; alinhado ao KPI de conversão.",
  },
  table: {
    section:
      "Última revisão por proposta no período. Clique na linha para abrir o detalhe da OV com histórico.",
    branch: "Filial TOTVS em que a proposta está registrada (AD1_FILIAL).",
    proposal: "Número da oportunidade de venda / proposta comercial (AD1_NROPOR).",
    revision: "Revisão da proposta no AD1010 (AD1_REVISA).",
    description: "Descrição comercial resumida da proposta (AD1_DESCRI).",
    proposalDate: "Data de abertura da proposta no TOTVS (AD1_DATA).",
    endDate: "Data de aceite da proposta (Dt.Ass.Prop. / AD1_DTASSI), com fallback para AD1_DTFIM.",
    status: "Status TOTVS da proposta (ex.: aberta, ganha status 9).",
    customerCode: "Código do cliente vinculado à OV (AD1_CODCLI / SA1).",
    customerStore: "Loja do cliente no cadastro TOTVS (AD1_LOJCLI).",
    search:
      "Filtra localmente por proposta, descrição, status, código de cliente, loja, etc.",
  },
  summary: {
    howToRead:
      "ROL segue o indicador commercial-rol no SI. Com filial Todas, ROL soma 01+02; demais KPIs vêm consolidados da api-delpi.",
  },
  detail: {
    pageSubtitle: "Detalhe da proposta comercial com cabeçalho AD1010 e histórico AIJ010.",
    statusKpi: "Status e estágio atual da proposta no fluxo comercial TOTVS.",
    openingKpi: "Data de abertura registrada no campo AD1_DATA.",
    closingKpi: "Data de aceite da proposta ganha (AD1_DTASSI), alinhada ao TOTVS.",
    proposalSection:
      "Cabeçalho da OV: filial, revisão, processo, estágio, datas e status no AD1010.",
    customerSection:
      "Cliente e vendedor vinculados à proposta (SA1010 e SA3010).",
    historySection:
      "Histórico de processos e estágios da OV no AIJ010 — linha do tempo ou tabela detalhada.",
    proposalBranch: "Filial TOTVS da proposta.",
    proposalNumber: "Número da proposta / OV.",
    proposalRevision: "Revisão atual consultada.",
    proposalDescription: "Descrição comercial da oportunidade.",
    proposalProcess: "Processo do fluxo (código e rótulo AC1010).",
    proposalStage: "Estágio atual dentro do processo (AC2010).",
    proposalOpening: "Data de abertura (AD1_DATA).",
    proposalClosing: "Data de aceite da proposta (Dt.Ass.Prop. / AD1_DTASSI).",
    proposalStatus: "Status TOTVS da proposta.",
    customerName: "Razão social ou nome do cliente.",
    customerCode: "Código do cliente no SA1.",
    customerStore: "Loja do cliente no cadastro TOTVS.",
    sellerName: "Nome do vendedor responsável.",
    sellerCode: "Código do vendedor no SA3.",
    historyTimelineView:
      "Linha do tempo agrupada por revisão, com badges de situação (atual, em andamento, atrasado).",
    historyTableView:
      "Tabela completa dos eventos AIJ010 com colunas ordenáveis.",
    historyTimelineFootnote:
      "Eventos conforme registro no TOTVS; duração em aberto usa o momento atual.",
    historyRevision: "Revisão da proposta vinculada ao evento.",
    historyProcess: "Processo do fluxo (código e rótulo).",
    historyStage: "Estágio dentro do processo.",
    historyStart: "Data e hora de início do evento.",
    historyLimit: "Data e hora limite previstas.",
    historyEnd: "Encerramento ou em andamento.",
    historyDuration: "Duração registrada ou calculada para o evento.",
    historyStatus: "Status do evento no workflow.",
    historyState: "Situação derivada: concluído, em andamento ou atrasado.",
    historyEngineering: "Indica fluxo de engenharia quando aplicável.",
  },
} as const;
