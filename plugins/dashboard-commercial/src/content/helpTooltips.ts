export const COMMERCIAL_HELP_TOOLTIPS = {
  filters: {
    competence:
      "Mês de referência (aaaa-mm). Ao selecionar, ajusta o período para o mês inteiro — ou até hoje, no mês corrente. Fica vazio quando o período abrange mais de um mês.",
    dateStart:
      "Início do período. KPIs, gráficos e tabela usam propostas com abertura (AD1_DATA) a partir desta data.",
    dateEnd:
      "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Unidade TOTVS para conversão, OTD, ROL, ROL WEG, ROL novos negócios e % novos negócios. Vazio = consolidado de todas as unidades.",
    customerSegment:
      "WEG = cliente código 000001 (todas as lojas). Novos negócios = demais clientes. Afeta ROL, conversão, OTD, % novos negócios, gráfico de ROL e tabela de propostas.",
    proposalStatus:
      "Filtra a tabela: todas (abertura AD1_DATA no período), ganhas (status 9 com aceite AD1_DTASSI no período) ou em aberto.",
  },
  actions: {
    pageSubtitle:
      "Indicadores comerciais do TOTVS: ROL por unidade, taxa de conversão de propostas, OTD de pedidos e participação de novos negócios no ROL.",
    refresh:
      "Recarrega KPIs, gráficos e tabela com os filtros atuais (período e unidade).",
    back:
      "Retorna ao dashboard comercial preservando período e unidade na URL.",
    detailRefresh:
      "Atualiza cabeçalho da OV e histórico de processo/estágio no TOTVS.",
    totvsBanner:
      "Dados extraídos do Protheus (AD1010, SD2, SC5/SC6). Metas vêm do módulo Indicadores Estratégicos quando configuradas.",
  },
  pagination: {
    info: "Paginação server-side: busca, ordenação e tamanho da página são aplicados na consulta.",
    pageSize: "Define quantos registros são buscados por página (10, 20, 50 ou 100).",
    jump: "Digite o número da página e pressione Enter ou saia do campo.",
    jumpEmpty: "Informe um número de página.",
    jumpInvalid: "Use apenas números inteiros.",
    jumpBelowMin: "A página mínima é 1.",
    previous: "Volta uma página mantendo busca, ordenação e tamanho da lista.",
    next: "Avança uma página mantendo busca, ordenação e tamanho da lista.",
  },
  kpis: {
    rol: "ROL (R$) no período. Com unidade Todas, exibe soma ou comparativo de Santa Catarina e Espírito Santo conforme o card.",
    rolWeg:
      "ROL (R$) de clientes WEG (código 000001) no período, por unidade. Metas via indicador commercial-rol-weg no SI.",
    rolNewBusiness:
      "ROL (R$) de clientes não-WEG (novos negócios) no período, por unidade. Metas via commercial-rol-new-business no SI.",
    salesOrderOtd:
      "Percentual de linhas de pedido de venda no prazo (faturadas e não faturadas). Abra o painel OTD para ver linhas e evolução.",
    closingRate:
      "Taxa de conversão: ganhas com aceite (AD1_DTASSI) no período sobre propostas abertas (AD1_DATA) no período.",
    newBusinessRol:
      "Participação do ROL de clientes não-WEG no ROL total do período (vendas SD2 menos devoluções).",
  },
  otd: {
    kpiOtd: "OTD de pedidos de venda no período filtrado (data prometida C6_ENTREG).",
    kpiOnTime: "Linhas atendidas no prazo — faturadas com C6_DATFAT ≤ C6_ENTREG ou abertas ainda dentro do prazo.",
    kpiLate: "Linhas atrasadas — faturadas após o prazo ou abertas com prazo vencido.",
    chartEvolution: "Evolução do OTD por unidade. Clique em um ponto para ajustar o período.",
    filters: {
      status: "Filtra a tabela por linhas no prazo ou atrasadas.",
    },
    table: {
      section: "Linhas SC6 elegíveis no período (data prometida). Clique para abrir o detalhe.",
      status: "No prazo ou atrasada conforme faturamento e data prometida.",
      branch: "Filial TOTVS do pedido (C6_FILIAL).",
      orderNumber: "Número do pedido de venda (C6_NUM).",
      lineItem: "Item/linha do pedido (C6_ITEM).",
      productCode: "Código do produto (C6_PRODUTO).",
      productDescription: "Descrição do produto (SB1).",
      customerName: "Nome do cliente (SA1).",
      promisedDate: "Data prometida de entrega (C6_ENTREG).",
      invoiceDate: "Data de faturamento (C6_DATFAT) — vazio se ainda não faturado.",
      daysDiff: "Dias entre a data prometida e o faturamento (ou data de referência do período).",
      search: "Busca local por pedido, produto, cliente ou unidade.",
    },
    detail: {
      order: "Dados da linha SC6 e cabeçalho SC5.",
      product: "Produto vinculado à linha do pedido.",
    },
  },
  charts: {
    rolEvolution:
      "Evolução do ROL por Santa Catarina e Espírito Santo. Clique em um ponto para ajustar o período ao intervalo selecionado.",
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
    branch: "Unidade TOTVS em que a proposta está registrada (AD1_FILIAL).",
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
      "ROL segue o indicador commercial-rol no SI. Com unidade Todas, ROL soma Santa Catarina e Espírito Santo; demais KPIs vêm consolidados da api-delpi.",
  },
  detail: {
    pageSubtitle: "Detalhe da proposta comercial com cabeçalho AD1010 e histórico AIJ010.",
    statusKpi: "Status e estágio atual da proposta no fluxo comercial TOTVS.",
    openingKpi: "Data de abertura registrada no campo AD1_DATA.",
    closingKpi: "Data de aceite da proposta ganha (AD1_DTASSI), alinhada ao TOTVS.",
    proposalSection:
      "Cabeçalho da OV: unidade, revisão, processo, estágio, datas e status no AD1010.",
    customerSection:
      "Cliente e vendedor vinculados à proposta (SA1010 e SA3010).",
    historySection:
      "Histórico de processos e estágios da OV no AIJ010 — linha do tempo ou tabela detalhada.",
    proposalBranch: "Unidade TOTVS da proposta.",
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
    productsSection:
      "Produtos vinculados à OV no ADJ010 — código, descrição, grupo, tipo e quantidade PI.",
    productCode: "Código do produto no cadastro SB1 (B1_COD).",
    productDescription: "Descrição comercial do item na proposta.",
    productGroup: "Grupo de produtos (B1_GRUPO) no cadastro TOTVS.",
    productType:
      "Tipo do produto: PA (acabado), PI (intermediário), MP (matéria-prima), etc.",
    productQtdPi: "Quantidade de produto intermediário (PI) na linha da OV.",
    productStructureSection:
      "Estrutura analítica (BOM) de cada produto PI/PA da proposta, carregada via api-delpi.",
    structureCode: "Código do componente na estrutura.",
    structureDescription: "Descrição do item na estrutura analítica.",
    structureType: "Tipo do produto na estrutura (PA, PI, MP, etc.).",
    structureQuantity: "Quantidade prevista na estrutura para o componente.",
    structureTreeCode: "Código do nó na árvore de estrutura",
    structureTreeDescription: "Descrição do componente na árvore",
    structureTreeQuantity: "Quantidade e unidade de medida na estrutura",
  },
} as const;
