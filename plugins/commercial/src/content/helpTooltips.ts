/**
 * Textos dos balões de explicação (HelpTooltip / SectionCard.hint / titleHint / FieldLabel.hint).
 * Fonte única — não espalhar strings de ajuda nos componentes.
 */
export const CM_HELP = {
  shell: {
    portal:
      "Portal operacional da carteira: Início, Meu dia, pedidos em aberto, contas e administração de vendedores. Analytics pesado fica nos deep links (Dashboard Comercial / Propostas).",
    scope:
      "Escopo atual da sessão: sua carteira ou a carteira do vendedor selecionado (admin). Filtra pedidos, clientes e alertas.",
    navHome: "Visão geral: alertas prioritários e atalhos para as áreas do portal.",
    navMyDay: "Fila de follow-ups e tarefas atribuídas a você (atrasadas, hoje e depois).",
    navOrders: "Linhas de pedido de venda em aberto no TOTVS, no escopo da carteira.",
    navCustomers: "Clientes da carteira com pedidos em aberto e indicadores comerciais.",
    navAdmin: "Cadastro de carteiras, vínculo de clientes e transferência entre vendedores.",
  },
  home: {
    overview:
      "Saudação e resumo do dia: chips de pedidos, follow-ups e atrasos no escopo atual.",
    alerts: "Fila do que precisa de ação agora — CTAs levam direto a Pedidos ou Meu dia.",
    kpis: "Indicadores operacionais da carteira (pedidos em aberto). Falha parcial não derruba o restante da Home.",
    kpiTasks: "Tarefas atrasadas + com prazo hoje na sua worklist.",
    management:
      "Área do administrador. KPIs ROL/OTD/conversão e tabela de equipe entram na etapa P1.",
    shortcuts: "Atalhos para as áreas principais — objetivo: chegar à ação em até dois cliques.",
    analytics:
      "BI e propostas ficam em apps irmãos. Aqui só há deep links para não misturar worklist com analytics.",
  },
  myDay: {
    worklist:
      "Fila operacional do dia (padrão CRM): atrasadas → hoje → depois. Cada tarefa tem prazo, prioridade e, de preferência, cliente vinculado.",
    bucketOverdue: "Tarefas com prazo anterior a hoje.",
    bucketToday: "Tarefas com prazo ainda hoje.",
    bucketLater: "Tarefas com prazo futuro.",
    newTask:
      "Cria follow-up atribuído a você. Prazo padrão = hoje (fim do dia). Vincule um cliente da carteira quando possível.",
    taskTitle: "Texto curto na fila. Prefira verbo + cliente/assunto.",
    taskDue: "Data de compromisso. Sem prazo a tarefa não entra bem na fila do dia.",
    taskPriority: "Ajuda a ordenar quando há várias tarefas no mesmo dia.",
    taskCustomer: "Cliente da sua carteira — abre atalho Abrir conta na linha da tarefa.",
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
      "Situação de estoque da linha: pode faturar, parcial ou sem estoque/atrasado.",
    filterDateStart: "Início da janela pela data de entrega prometida da linha.",
    filterDateEnd: "Fim da janela pela data de entrega prometida da linha.",
    table:
      "Cada linha é um item de pedido em aberto. Use colunas, ordenação e exportação Excel conforme a preferência salva.",
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
    billingValue: "Total faturado no período selecionado nos filtros de notas.",
    billingInvoiceCount: "Quantidade de notas fiscais de saída no período.",
    billingLastDate: "Data da nota mais recente no período filtrado.",
    billingLastValue: "Valor da nota mais recente no período filtrado.",
    billingFilters: "Período e opções da consulta de faturamento deste cliente.",
  },
  sellerPortfolios: {
    list: "Carteiras cadastradas na commercial-api (usuário Keycloak + nome de exibição).",
    create: "Cria carteira vinculada a um usuário do diretório. O nome aparece no seletor de escopo.",
    displayName: "Nome amigável exibido no Portal Comercial (não precisa ser o login).",
    directoryUser: "Usuário Keycloak que será o dono da carteira (busca por nome ou e-mail).",
    edit: "Altera o nome de exibição da carteira selecionada.",
    customers: "Clientes (código+loja) vinculados a esta carteira. Use busca TOTVS para incluir.",
  },
} as const;

/** Alias estável usado na coluna Tendência da carteira. */
export const BILLING_TREND_HELP = CM_HELP.customers.trend;
