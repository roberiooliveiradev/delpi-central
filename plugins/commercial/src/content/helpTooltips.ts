/**
 * Textos dos balões de explicação (HelpTooltip / SectionCard.hint / titleHint / FieldLabel.hint).
 * Fonte única — não espalhar strings de ajuda nos componentes.
 */
export const CM_HELP = {
  shell: {
    portal:
      "Portal comercial: Início, Meu dia, pedidos, carteira, propostas, gestão e administração de vendedores — tudo no mesmo app.",
    scope:
      "Escopo atual da sessão: sua carteira ou a carteira do vendedor selecionado (team.view ou admin). Filtra pedidos, clientes e alertas.",
    navHome: "Visão geral: alertas prioritários e atalhos para as áreas do portal.",
    navMyDay: "Fila de follow-ups e tarefas atribuídas a você (atrasadas, hoje e depois).",
    navOrders: "Linhas de pedido de venda em aberto no TOTVS, no escopo da carteira.",
    navCustomers: "Clientes da carteira com pedidos em aberto e indicadores comerciais.",
    navProposals: "Propostas comerciais (ADY) read-only com emissão de PDF.",
    navGestao: "KPIs, OTD, equipe e oportunidades comerciais no período filtrado.",
    navAdmin: "Cadastro de carteiras, vínculo de clientes e transferência entre vendedores.",
  },
  home: {
    overview:
      "Saudação com o nome do usuário (perfil /core-api/me) acima da top bar; chips e alertas abaixo da navegação.",
    alerts: "Fila do que precisa de ação agora — CTAs levam direto a Pedidos ou Meu dia.",
    kpis: "Indicadores operacionais da carteira (pedidos em aberto). Falha parcial não derruba o restante da Home.",
    kpiTasks: "Tarefas atrasadas + com prazo hoje na sua worklist.",
    management:
      "KPIs de gestão (ROL, conversão, OTD) via api-delpi e tabela da equipe por carteira. Falha parcial não derruba a Home.",
    kpiRol: "ROL da matriz versus meta no mês corrente (Gestão do Portal Comercial).",
    kpiClosing: "Taxa de conversão de propostas no mês (ganhas ÷ propostas).",
    kpiOtd: "On-time delivery de linhas de pedido de venda no mês.",
    shortcuts: "Atalhos para as áreas principais — objetivo: chegar à ação em até dois cliques.",
    analytics:
      "Atalhos internos para Gestão e Propostas no Portal Comercial (sem deep link para MFEs irmãos).",
    scope:
      "Escopo atual: sua carteira ou a de um vendedor da equipe (team.view ou admin de carteiras).",
  },
  myDay: {
    worklist:
      "Fila operacional do dia (padrão CRM): atrasadas → hoje → depois → concluídas. Filtre por tipo; notas aparecem na linha (HubSpot/Pipedrive).",
    scopeMine: "Só tarefas atribuídas a você.",
    scopeTeam:
      "Fila de todos os vendedores com carteira ativa (gestão). Opcional: filtrar por responsável.",
    teamAssigneeFilter: "Restringe a fila da equipe a um vendedor com carteira ativa.",
    bucketOverdue: "Tarefas com prazo anterior a hoje.",
    bucketToday: "Tarefas com prazo ainda hoje.",
    bucketLater: "Tarefas com prazo futuro.",
    bucketDone:
      "Histórico das tarefas já concluídas (mais recentes primeiro). Somente leitura — sem editar, adiar ou concluir de novo.",
    typeFilter: "Filtra a fila pelo tipo de atividade (padrão Pipedrive/HubSpot).",
    newTask:
      "Cria follow-up com prazo (fim do dia). Gestores podem atribuir a outro vendedor da equipe.",
    taskTitle: "Texto curto na fila. Prefira verbo + cliente/assunto.",
    taskDue: "Data de compromisso. Sem prazo a tarefa não entra bem na fila do dia.",
    taskCompletedAt: "Quando a tarefa foi marcada como concluída.",
    taskPriority: "Ajuda a ordenar quando há várias tarefas no mesmo dia.",
    taskType: "Follow-up, ligar, e-mail, visita ou to-do — alinhado a HubSpot/Pipedrive.",
    taskAssignee:
      "Responsável com carteira ativa. Vazio = você. Só gestores atribuem a outro vendedor.",
    taskAssignedBy:
      "Quem criou e atribuiu a tarefa. Só o criador edita, adia ou exclui; o responsável apenas conclui.",
    taskCustomer:
      "Cliente da carteira do responsável — abre atalho Abrir conta na linha da tarefa.",
    taskDescription:
      "Observação interna (notes). Visível no card da tarefa e no histórico da conta — não é e-mail ao cliente.",
    taskAttachment:
      "Adicione ou remova anexos em Nova tarefa / Editar. No card da fila só há prévia (clique para abrir).",
    editTask:
      "Só quem criou a tarefa pode editar título, observação, prazo, tipo, prioridade, cliente e anexos. Gestores criadores também trocam o responsável aqui.",
    deleteTask: "Só o criador remove a tarefa aberta da fila. Confirme antes de excluir.",
    deferTask: "Só o criador empurra o prazo em +1 dia. O responsável apenas conclui.",
    reassignTask:
      "Troca o responsável no formulário Editar (campo Responsável). Destino deve ter carteira ativa.",
  },
  openOrders: {
    page:
      "Consulta operacional de pedidos de venda em aberto (TOTVS). Totais e tabela respeitam filtros e o escopo da carteira.",
    kpiLines: "Quantidade de linhas SC6 em aberto no escopo e filtros atuais.",
    kpiValue: "Soma do valor em aberto das linhas filtradas (saldo × preço).",
    kpiCanInvoice: "Linhas com estoque suficiente para faturar integralmente.",
    kpiPartialStock: "Linhas com estoque parcial — atendem só parte da quantidade em aberto.",
    kpiLate: "Linhas com data de entrega prometida vencida e ainda em aberto.",
    filters: "Refine a lista por busca, filial, cliente, status de estoque e janela de entrega.",
    filterSearch: "Busca em cliente, pedido, produto e códigos da linha.",
    filterBranch: "Filial TOTVS do pedido. Vazio = todas as filiais do escopo.",
    filterClient: "Um ou mais clientes da carteira (código+loja).",
    filterStock:
      "Situação de estoque da linha: pode faturar, parcial ou sem estoque/atrasado. Os chips de atenção também aplicam este filtro.",
    filterLate: "Filtrar só linhas com entrega prometida vencida e saldo em aberto.",
    filterDateStart: "Início da janela pela data de entrega prometida da linha.",
    filterDateEnd: "Fim da janela pela data de entrega prometida da linha.",
    sellerScope:
      "Filtra pedidos pela carteira do vendedor selecionado. Vazio = todas as carteiras que você pode ver.",
    table:
      "Cada linha é um item de pedido em aberto. Use colunas, ordenação e exportação Excel conforme a preferência salva.",
    layoutToggle:
      "Alterna entre grade tabular (mais colunas) e cards (melhor em telas estreitas). A preferência fica salva neste navegador.",
    sortBy: "Campo usado para ordenar a lista (mesma ordenação da tabela e dos cards).",
    sortDirection: "Crescente ou decrescente no campo de ordenação selecionado.",
    cardOpenHint: "Abrir detalhes",
    cardAriaOpen: "Abrir detalhes da linha",
    columns: {
      nome_cliente:
        "Nome do cliente no pedido. Clique para abrir a Conta 360 (código + loja).",
      loja_cadastro: "Loja do cadastro do cliente no TOTVS (A1_LOJA).",
      filial: "Filial TOTVS em que o pedido foi digitado.",
      pedido: "Número do pedido de venda e número da linha (item SC6).",
      pedido_cliente: "Número do pedido no cliente (quando informado no TOTVS).",
      produto: "Código do produto (B1_COD) da linha em aberto.",
      codigo_cliente: "Código do produto no cliente (quando cadastrado).",
      quantidade: "Quantidade original pedida na linha.",
      entregue: "Quantidade já entregue / faturada desta linha.",
      saldo: "Quantidade ainda em aberto (pedida − entregue).",
      no_estoque:
        "Estoque físico alocado a esta linha (FIFO por produto/filial no cliente — não é reserva formal).",
      cobertura:
        "Proporção estoque alocado ÷ saldo em aberto. Verde ≈ 100%; amarelo parcial; vermelho sem cobertura.",
      data_entrega: "Data de entrega prometida no pedido (compromisso comercial).",
      previsao_entrega_op:
        "Previsão de disponibilidade pela cobertura FIFO das OPs abertas. Clique para o detalhe da linha. O badge compara previsão OP × entrega do pedido.",
      data_despacho: "Data de despacho informada no TOTVS, quando houver.",
      valor_aberto: "Valor em aberto da linha (saldo × preço).",
      status:
        "Situação operacional de estoque/atraso calculada no cliente: pode faturar, parcial, sem estoque ou atrasado.",
      atraso_dias:
        "Dias corridos desde a data de entrega prometida, só se ainda houver saldo em aberto.",
    },
    detail: {
      modal:
        "Detalhe da linha: status fabril do produto, indicadores, gráficos, timeline da OP e lista FIFO das ordens usadas na previsão.",
      factoryStatus:
        "Visão fabril consolidada do produto (PA/PI, produção iniciada, expedição) via api-delpi /factory-status.",
      saldo: "Quantidade ainda em aberto nesta linha do pedido.",
      estoqueAlocado:
        "Parte do estoque físico já atribuída a esta linha no algoritmo FIFO do portal.",
      saldoProduzir: "Quanto ainda precisa ser produzido após considerar o estoque alocado.",
      valorAberto: "Valor monetário ainda em aberto nesta linha.",
      atraso: "Dias de atraso da entrega prometida, se a linha ainda estiver em aberto.",
      status: "Pode faturar / parcial / sem estoque / atrasado — mesmo critério da coluna Status.",
      coberturaKind:
        "Como a linha está coberta: estoque, OP completa, parcial, sem OP ou OP sem data prevista.",
      entregaPedido: "Data de entrega prometida no pedido de venda.",
      despacho: "Data de despacho informada no TOTVS, quando houver.",
      previsaoEntrega: "Data (ou rótulo) da previsão pela OP mais tarde necessária na alocação FIFO.",
      chartCobertura:
        "Compara quantidade alocada em estoque versus saldo a produzir para fechar a linha.",
      chartPrazo:
        "Dias até a entrega do pedido e até a previsão OP (valor negativo = data já passou).",
      chartPrazoCaption: "Negativo = já passou",
      chartOps: "Por OP: quanto foi alocado a este pedido versus o saldo restante da OP.",
      chartOpsCaption: "Alocado no pedido vs saldo OP",
      opsNote:
        "OPs são compartilhadas por produto/filial e alocadas por ordem de entrega dos pedidos — indicação operacional, não reserva formal ao cliente.",
      opsTable: "Ordens de produção usadas na previsão desta linha (FIFO). Clique na linha para focar a timeline.",
      otdPrazo:
        "Status OTD e dias (previsto × real) da OP via by-op. Negativo = finalização antes do previsto. «Ver no OTD produção» abre a ficha completa no dashboard de produção.",
      otdLinkedPi:
        "OPs intermediárias (PI) vinculadas pelo mesmo nº OP (C2_NUM). Resumo on_time / late / open vem do link_summary da api-delpi.",
      opNumero: "Número da ordem de produção no TOTVS.",
      opProduzido: "Quantidade já produzida na OP (C2_QUJE / by-op).",
      opPlanejado: "Quantidade planejada da OP (C2_QUANT / by-op).",
      opSaldo: "Saldo restante da OP no momento da alocação.",
      opAlocado: "Quanto desta OP foi atribuído a esta linha do pedido.",
      opFim: "Data fim prevista da OP (quando cadastrada).",
      opStatus: "Status Protheus da OP ou comparação fim previsto × entrega do pedido.",
      opOtd: "On-time delivery da OP (on_time / late / open) quando disponível em by-op.",
      opObs: "Observação cadastrada na OP, quando houver.",
      bom: "Estrutura (BOM) do produto desta linha — mesma API /products/{code}/structure do dashboard.",
      copyPedido: "Copia o número do pedido para a área de transferência.",
      openAccount: "Abre a Conta 360 do cliente (código + loja) no Portal Comercial.",
      openOv:
        "Abre o detalhe da oportunidade (OV) na Gestão do Portal, quando o vínculo pedido↔OV for resolvido.",
    },
  },
  customers: {
    page:
      "Carteira agregada a partir dos pedidos em aberto: um cartão/linha por cliente (código+loja).",
    kpiActive: "Clientes da carteira que têm pelo menos um pedido em aberto.",
    kpiNoSale60:
      "Clientes cuja última venda (quando disponível) foi há 60 dias ou mais — priorize reativação.",
    kpiOpenValue: "Soma do valor em aberto de todos os clientes listados (após filtros).",
    kpiOpenOrders: "Quantidade de pedidos distintos em aberto na carteira filtrada.",
    kpiLateCustomers: "Clientes com ao menos uma linha de pedido vencida.",
    billingSeries:
      "Soma das notas fiscais de saída nos últimos 12 meses. Selecione um cliente para ver só a curva dele.",
    filterSearch: "Busca por código, loja, nome fantasia/razão ou número de pedido.",
    filterSituation:
      "Atalhos de atenção: todos, com atraso ou parcialmente atendidos nos pedidos em aberto.",
    list: "Lista paginada da carteira. Clique na linha para abrir a Conta 360.",
    trend:
      "Comparamos o faturamento dos últimos 6 meses com o dos 6 meses anteriores. Se subir mais de 5%, mostramos alta (verde); se cair mais de 5%, mostramos queda; entre −5% e +5%, estável. Sem histórico suficiente, a tendência fica indefinida.",
  },
  customerDetail: {
    header:
      "Conta 360 do cliente (código+loja): indicadores, pedidos em aberto, faturamento, timeline e atalhos.",
    billed12m: "Faturamento (NFs de saída) nos últimos 12 meses deste cliente.",
    openValue: "Soma do saldo em aberto dos pedidos deste cliente.",
    openOrders: "Quantidade de pedidos distintos ainda em aberto.",
    lastSale: "Data da última venda conhecida para o cliente (quando disponível).",
    purchaseEvolution:
      "Comparativo mês a mês: últimos 12 meses versus os 12 meses imediatamente anteriores.",
    timeline:
      "Atividades e follow-ups registrados na commercial-api para esta conta (código+loja).",
    scheduleFollowUp:
      "Abre o Meu dia com este cliente já selecionado para criar um follow-up com prazo.",
    billingValue: "Total faturado no período selecionado nos filtros de notas.",
    billingInvoiceCount: "Quantidade de notas fiscais de saída no período.",
    billingLastDate: "Data da nota mais recente no período filtrado.",
    billingLastValue: "Valor da nota mais recente no período filtrado.",
    billingFilters: "Período e opções da consulta de faturamento deste cliente.",
  },
  sellerPortfolios: {
    list: "Carteiras cadastradas (usuário Minha Delpi + nome de exibição).",
    filter: "Filtre a lista por status: todas, só ativas ou só inativas.",
    create: "Cria carteira vinculada a um usuário do diretório. O nome aparece no seletor de escopo.",
    displayName:
      "Nome amigável no portal. Se vazio ao criar, usa o nome do usuário Minha Delpi.",
    directoryUser:
      "Usuário Minha Delpi que será o dono da carteira (busca por nome ou e-mail).",
    edit: "Altera o nome de exibição da carteira selecionada.",
    customers:
      "Clientes (código+loja) vinculados a esta carteira. Use busca TOTVS para incluir.",
    colDisplayName: "Nome da carteira no seletor de escopo e nas telas do portal.",
    colUserId: "Nome e e-mail do usuário Minha Delpi dono da carteira.",
    colCustomerCount: "Quantidade de clientes (código+loja) vinculados a esta carteira.",
    colStatus: "Ativa: aparece no escopo. Inativa: ocultada para operação normal.",
    colActions: "Editar nome, gerenciar clientes ou ativar/desativar a carteira.",
    managePortfolio: "Carteira cujos clientes você vai vincular ou remover.",
    searchCustomers:
      "Busca clientes ativos no TOTVS por código ou nome (mínimo 2 caracteres).",
    transfer:
      "Move clientes de uma carteira para outra com motivo registrado (auditoria).",
    transferSource: "Carteira de onde os clientes saem.",
    transferTarget: "Carteira que recebe os clientes.",
    transferCustomers: "Selecione um ou mais clientes da carteira de origem.",
    transferReason: "Motivo obrigatório da transferência (fica no histórico).",
  },
  analytics: {
    ovStatus: "Status atual da OV no Protheus (AD1010).",
    ovOpen: "Data de abertura da oportunidade (AD1_DATA).",
    ovClose: "Data de fechamento / assinatura (AD1_DTASSI), quando houver.",
    ovHeader: "Cabeçalho AD1010: filial, revisão, processo, estágio e descrição.",
    ovCustomer: "Cliente e vendedor vinculados à OV (SA1 / SA3).",
    ovProducts: "Itens da OV (ADJ010): código, descrição, grupo, tipo e quantidade.",
    ovBom: "Estrutura de produto (BOM) via /products/{code}/structure para cada item da OV.",
    ovHistory:
      "Histórico AIJ010 da OV — timeline ou tabela. Fonte: GET /commercial/proposals/{n}/history/events.",
  },
} as const;

/** Alias estável usado na coluna Tendência da carteira. */
export const BILLING_TREND_HELP = CM_HELP.customers.trend;
