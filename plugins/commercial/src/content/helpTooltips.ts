/**
 * Textos dos balões de explicação (HelpTooltip / SectionCard.hint / titleHint / FieldLabel.hint).
 * Fonte única — não espalhar strings de ajuda nos componentes.
 */
export const CM_HELP = {
  shell: {
    portal:
      "Portal comercial: Início, Visão geral, Minhas tarefas, pedidos, carteira e administração de vendedores — tudo no mesmo app.",
    scope:
      "Identidade da sessão: mostra as carteiras em que você participa. Não é filtro — nas listas de pedidos e clientes use o seletor de carteira quando houver mais de uma opção. Em Propostas a lista de documentos também não usa este escopo.",
    navHome: "Alertas prioritários, eventos do dia e atalhos para as áreas do portal.",
    navOverview:
      "Dashboard do período: filtros, indicadores, evolução ROL e funil. Sem lista de OVs — use Oportunidades no Início ou na Conta.",
    navMyTasks: "Fila de follow-ups e tarefas atribuídas a você (atrasadas, hoje e depois).",
    navOrders: "Itens de pedidos de venda em aberto nas carteiras que você atende.",
    navCustomers:
      "Clientes das carteiras que você atende, com pedidos em aberto e indicadores comerciais.",
    navAdmin: "Cadastro de carteiras, vínculo de clientes e transferência entre vendedores.",
  },
  home: {
    overview:
      "Saudação personalizada, escopo da carteira e KPIs operacionais (follow-ups, valor aberto, atrasos) — sem BI do período. CTA contextual quando há atrasos ou tarefas urgentes.",
    alerts:
      "Eventos e interações do seu dia: alertas da carteira e as primeiras tarefas da fila — os atalhos levam direto a Pedidos ou Minhas tarefas. Se a fila estiver vazia, aparece o chip «Fila em dia».",
    kpis: "Indicadores operacionais da carteira (pedidos em aberto). Falha parcial não derruba o restante da Home.",
    kpiTasks: "Tarefas atrasadas + com prazo hoje na sua worklist.",
    management:
      "Indicadores de gestão, conversão e pontualidade, além da visão da equipe por carteira.",
    kpiRol: "ROL consolidado versus meta no mês corrente (Gestão do Portal Comercial).",
    kpiClosing: "Taxa de conversão de propostas no mês (ganhas ÷ propostas).",
    kpiOtd: "On-time delivery de linhas de pedido de venda no mês.",
    shortcuts:
      "Caminhos por seção (Operação, Gestão à vista, Documentos, Administração). Busque, fixe favoritos ou use Ctrl/Cmd+K. Objetivo: chegar à ação em até dois cliques.",
    search:
      "Filtra seções e rotas do catálogo (rótulo e palavras-chave). A URL guarda ?q= para compartilhar o filtro.",
    favorites: "Atalhos fixados por você (persistidos na conta). Clique na estrela em uma rota para adicionar ou remover.",
    palette: "Busca rápida do portal (Ctrl/Cmd+K). Mesmo catálogo do Início, em modal contido no app.",
    analytics:
      "Atalhos internos para Gestão e Propostas no Portal Comercial (sem deep link para MFEs irmãos).",
    scope:
      "Escopo atual: sua carteira ou a de outro vendedor que você pode consultar.",
  },
  users: {
    profile:
      "Perfil do usuário no Portal Comercial: nome e e-mail do diretório, cargo e foto editáveis (você ou gestor de carteiras).",
    jobTitle: "Cargo exibido no Comercial. Não sincroniza RH nesta fase.",
    portfolios: "Carteiras do usuário com papel, quantidade de clientes e membros.",
    access:
      "Permissões commercial.* e capacidades efetivas desta sessão (somente no próprio perfil).",
    shortcuts: "Atalhos para as áreas do Portal Comercial liberadas para você.",
    editMode: "Ativa o modo edição para alterar cargo e foto do perfil.",
  },
  myDay: {
    worklist:
      "Fila operacional do dia: atrasadas → hoje → depois → concluídas. Filtre por tipo e consulte as observações em cada atividade.",
    scopeMine: "Só tarefas atribuídas a você.",
    scopeTeam:
      "Fila de todas as tarefas (gestão). Opcional: filtrar por responsável (usuário do portal).",
    teamAssigneeFilter:
      "Restringe a fila da equipe a um usuário do portal com acesso ao Comercial.",
    bucketOverdue: "Tarefas com prazo anterior a hoje.",
    bucketToday: "Tarefas com prazo ainda hoje.",
    bucketLater: "Tarefas com prazo futuro.",
    bucketDone:
      "Histórico das tarefas já concluídas (mais recentes primeiro). Somente leitura — sem editar, adiar ou concluir de novo.",
    typeFilter: "Filtra a fila pelo tipo de atividade comercial.",
    newTask:
      "Cria follow-up com prazo (fim do dia). Gestores podem atribuir a qualquer usuário do portal com acesso ao Comercial.",
    taskTitle: "Texto curto na fila. Prefira verbo + cliente/assunto.",
    taskDue: "Data de compromisso. Sem prazo a tarefa não entra bem na fila do dia.",
    taskCompletedAt: "Quando a tarefa foi marcada como concluída.",
    taskCompletedBy:
      "Quem concluiu a tarefa (responsável individual ou membro do grupo atribuído).",
    taskPriority: "Ajuda a ordenar quando há várias tarefas no mesmo dia.",
    taskType: "Follow-up, ligação, e-mail, visita ou outra ação comercial.",
    taskAssignee:
      "Um ou mais usuários do portal com acesso ao Comercial (máx. 20). Vazio = você. Só gestores atribuem a outros. Exclusivo com Grupos.",
    taskAssigneeXor:
      "Escolha Usuários ou Grupos — não os dois. Trocar a opção limpa a seleção anterior.",
    taskGroups:
      "Grupos operacionais responsáveis (exclusivo com Usuários). Membros atuais do grupo veem a tarefa na fila Minhas; um membro conclui para todos.",
    taskAssignedBy:
      "Quem criou e atribuiu a tarefa. Só o criador edita, adia ou exclui; qualquer responsável (ou membro do grupo) conclui.",
    taskCustomer:
      "Um ou mais clientes TOTVS (máx. 20). No card, o nome abre a Conta na aba Contatos; Abrir conta usa o primeiro cliente.",
    taskDescription:
      "Observação interna. Visível no card da tarefa e no histórico da conta — não é e-mail ao cliente.",
    taskAttachment:
      "Adicione ou remova anexos em Nova tarefa / Editar. No card da fila só há prévia (clique para abrir).",
    editTask:
      "Só quem criou a tarefa pode editar título, observação, prazo, tipo, prioridade, cliente e anexos. Gestores criadores também trocam o responsável aqui.",
    deleteTask: "Só o criador remove a tarefa aberta da fila. Confirme antes de excluir.",
    deferTask: "Só o criador empurra o prazo em +1 dia. O responsável apenas conclui.",
    reassignTask:
      "Troca o responsável no formulário Editar (campo Responsável). Destino = qualquer usuário do portal com acesso ao Comercial.",
  },
  openOrders: {
    page:
      "Consulta operacional de pedidos de venda em aberto. Totais e tabela respeitam os filtros e o escopo da carteira.",
    kpiLines: "Quantidade de itens de pedido em aberto no escopo e nos filtros atuais.",
    kpiValue: "Soma do valor em aberto das linhas filtradas (saldo × preço).",
    kpiCanInvoice: "Linhas com estoque suficiente para faturar integralmente.",
    kpiPartialStock: "Linhas com estoque parcial — atendem só parte da quantidade em aberto.",
    kpiLate: "Linhas com data de entrega prometida vencida e ainda em aberto.",
    filters: "Refine a lista por busca, unidade, cliente, status de estoque e janela de entrega.",
    filterSearch: "Busca em cliente, pedido, produto e códigos da linha.",
    filterBranch:
      "Unidade responsável pelo pedido (Santa Catarina ou Espírito Santo). Vazio = todas as unidades do escopo.",
    filterClient: "Um ou mais clientes da carteira (código+loja).",
    filterStock:
      "Situação de estoque da linha: pode faturar, parcial ou sem estoque/atrasado. Os chips de atenção também aplicam este filtro.",
    filterLate: "Filtrar só linhas com entrega prometida vencida e saldo em aberto.",
    filterDateStart: "Início da janela pela data de entrega prometida da linha.",
    filterDateEnd: "Fim da janela pela data de entrega prometida da linha.",
    sellerScope:
      "Filtra pedidos pela carteira do vendedor selecionado. Vazio = todas as carteiras que você pode ver.",
    table:
      "Cada linha é um item de pedido em aberto. Clique abre o detalhe da linha. Use colunas, ordenação e exportação Excel conforme a preferência salva.",
    tableRowOpensDetail:
      "Clique na linha (exceto ações/links com destino próprio, como Cliente→Conta) abre o detalhe do item.",
    layoutToggle:
      "Alterna entre tabela, cards e board Kanban (colunas por etapa). A preferência fica salva neste navegador.",
    kanbanBoard:
      "Visão somente leitura: cada coluna é uma etapa operacional. Clique no card abre o detalhe da linha (mesmos filtros da lista).",
    kanbanUpcoming:
      "Próximos: linhas em aberto sem estoque suficiente e sem atraso (fila à frente).",
    kanbanInProgress:
      "Em andamento: entrega prometida vencida ou estoque parcial — ainda não dá para faturar o saldo inteiro.",
    kanbanReadyToInvoice:
      "Pronto para faturar: estoque alocado cobre o saldo em aberto (inclui atrasados com estoque completo).",
    kanbanCompleted:
      "Concluídos: linhas encerradas recentemente (fora da lista de abertos), no período configurado.",
    sortBy: "Campo usado para ordenar a lista (mesma ordenação da tabela e dos cards).",
    sortDirection: "Crescente ou decrescente no campo de ordenação selecionado.",
    cardOpenHint: "Abrir detalhes",
    cardAriaOpen: "Abrir detalhes da linha",
    columns: {
      nome_cliente:
        "Nome do cliente no pedido. Clique para abrir a Conta 360 (código + loja).",
      loja_cadastro: "Loja vinculada ao cadastro do cliente.",
      filial: "Unidade em que o pedido foi registrado (Santa Catarina ou Espírito Santo).",
      pedido: "Número do pedido de venda e identificação do item.",
      pedido_cliente: "Número de referência informado pelo cliente, quando disponível.",
      produto: "Código comercial do produto no item em aberto.",
      codigo_cliente: "Código do produto no cliente (quando cadastrado).",
      quantidade: "Quantidade original pedida na linha.",
      entregue: "Quantidade já entregue / faturada desta linha.",
      saldo: "Quantidade ainda em aberto (pedida − entregue).",
      no_estoque:
        "Estoque físico alocado a esta linha (FIFO por produto/unidade no cliente — não é reserva formal).",
      cobertura:
        "Proporção estoque alocado ÷ saldo em aberto. Verde ≈ 100%; amarelo parcial; vermelho sem cobertura.",
      data_entrega: "Data de entrega prometida no pedido (compromisso comercial).",
      previsao_entrega_op:
        "Previsão de disponibilidade pela cobertura FIFO das OPs abertas. Clique para o detalhe da linha. O badge compara previsão OP × entrega do pedido.",
      data_despacho: "Data de despacho registrada para o item, quando houver.",
      valor_aberto: "Valor em aberto da linha (saldo × preço).",
      status:
        "Situação operacional de estoque/atraso calculada no cliente: pode faturar, parcial, sem estoque ou atrasado.",
      atraso_dias:
        "Dias corridos desde a data de entrega prometida, só se ainda houver saldo em aberto.",
    },
    detail: {
      page:
        "Página do item: situação fabril do produto, indicadores, gráficos, evolução da produção e ordens usadas na previsão.",
      guideResumo: "Cartões de situação, cobertura, entrega do pedido e previsão de produção no início da página.",
      guideFabril: "Status fabril do produto: produção PA/PI, expedição e capacidade de matéria-prima.",
      guideIndicadores: "Saldo, estoque alocado, valor aberto e demais indicadores da linha do pedido.",
      guideCobertura: "Gráficos de cobertura estoque × demanda e prazo (entrega vs previsão OP).",
      guideProducao: "OPs alocadas, prazo OTD, timeline, apontamentos e tabela desta linha.",
      factoryStatus:
        "Visão fabril consolidada do produto nesta unidade: produção PA/PI, expedição e restrições de matéria-prima.",
      factoryPaStarted: "Indica se a produção do produto acabado (PA) deste código já foi iniciada.",
      factoryPiStarted:
        "Indica se a produção de produto intermediário (PI) vinculada a este código já foi iniciada.",
      factoryOpsPaPi: "Quantidade de ordens de produção de PA e de PI relacionadas a este produto.",
      factoryShipped: "Quantidade já expedida deste produto.",
      factoryInspectionLoss: "Quantidade registrada como perda em inspeção.",
      factoryMpPa:
        "Máximo de PA que o estoque atual de matéria-prima permite produzir.",
      factoryMpLimiting: "Matéria-prima que limita a produção de uma unidade do produto acabado.",
      factoryMpWithoutStock:
        "Quantidade de matérias-primas sem saldo suficiente para produzir 1 PA.",
      snapshotSituacao:
        "Situação operacional da linha (pode faturar, parcial, sem estoque ou atrasado) — mesmo critério da coluna Status.",
      snapshotCobertura:
        "Como a linha está coberta na previsão: estoque, OP completa, parcial, sem OP ou OP sem data.",
      metricsTitle:
        "Indicadores desta linha do pedido: saldo, estoque alocado, valor e despacho.",
      appointments:
        "Apontamentos da OP: período, quantidade produzida e centros de trabalho.",
      timeline:
        "Marcos da OP (emissão, início/fim previstos, entrega do pedido, apontamentos e fim real) em ordem cronológica.",
      opProgress: "Progresso produzido ÷ planejado da OP selecionada.",
      otdStatus: "Classificação OTD da OP: no prazo, atrasada ou em aberto.",
      otdDays:
        "Diferença em dias entre a data prevista e a finalização real (negativo = antecipou).",
      otdDue: "Data de entrega prevista da OP.",
      otdFinish: "Data de finalização real da OP, quando disponível.",
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
      despacho: "Data de despacho informada no sistema, quando houver.",
      previsaoEntrega:
        "Data (ou rótulo) da previsão pela OP mais tarde necessária na alocação FIFO.",
      chartCobertura:
        "Compara quantidade alocada em estoque versus saldo a produzir para fechar a linha.",
      chartPrazo:
        "Dias até a entrega do pedido e até a previsão OP (valor negativo = data já passou).",
      chartPrazoCaption: "Negativo = já passou",
      chartOps: "Por OP: quanto foi alocado a este pedido versus o saldo restante da OP.",
      chartOpsCaption: "Alocado no pedido vs saldo OP",
      opsNote:
        "OPs são compartilhadas por produto/unidade e alocadas por ordem de entrega dos pedidos — indicação operacional, não reserva formal ao cliente.",
      opsTable:
        "Ordens de produção usadas na previsão desta linha (FIFO). Clique na linha para focar a timeline.",
      otdPrazo:
        "Status OTD e dias entre a previsão e a conclusão da OP. Valor negativo indica finalização antecipada.",
      otdLinkedPi:
        "OPs intermediárias (PI) vinculadas pelo mesmo número de OP. Mostra resumo no prazo / atrasadas / em aberto.",
      opNumero: "Número da ordem de produção.",
      opProduzido: "Quantidade já produzida nesta OP.",
      opPlanejado: "Quantidade planejada nesta OP.",
      opSaldo: "Saldo restante da OP no momento da alocação.",
      opAlocado: "Quanto desta OP foi atribuído a esta linha do pedido.",
      opFim: "Data fim prevista da OP (quando cadastrada).",
      opStatus: "Status da OP ou comparação do fim previsto com a entrega do pedido.",
      opOtd: "On-time delivery da OP (no prazo, atrasada ou em aberto), quando disponível.",
      opObs: "Observação cadastrada na OP, quando houver.",
      bom: "Estrutura de componentes do produto deste item.",
      copyPedido: "Copia o número do pedido para a área de transferência.",
      openAccount: "Abre a Conta 360 do cliente (código + loja) no Portal Comercial.",
      openOv:
        "Abre o detalhe da oportunidade de venda (OV) na Gestão, quando o vínculo com o pedido for encontrado.",
    },
    freshness: "Horário da última carga bem-sucedida desta página neste navegador.",
    portfolioEmpty:
      "A carteira selecionada não tem clientes cadastrados. Quem gerencia carteiras pode incluir clientes em Administração.",
  },
  customers: {
    page:
      "Clientes da carteira com pedidos de venda em aberto, agrupados por conta.",
    kpiActive: "Clientes da carteira que têm pelo menos um pedido em aberto.",
    kpiNoSale60:
      "Clientes cuja última venda (quando disponível) foi há 60 dias ou mais — priorize reativação.",
    kpiOpenValue: "Soma do valor em aberto de todos os clientes listados (após filtros).",
    kpiOpenOrders: "Quantidade de pedidos distintos em aberto na carteira filtrada.",
    kpiLateCustomers: "Clientes com ao menos uma linha de pedido vencida.",
    glossaryOpenVsBilled:
      "Glossário: «Em aberto / carteira aberta» = pedidos com saldo (backlog). «Faturamento» = notas fiscais / ROL no período. O share empresa e a tendência usam só faturamento — nunca o valor em aberto.",
    portfolioBillingShare:
      "Share = ROL (ou faturamento agregado) da carteira/escopo ÷ ROL da empresa no mesmo período. Exige permissão de analytics, equipe ou gestão de carteiras.",
    billingRanking:
      "Ranking de crescimento/queda do faturamento (ROL) versus o mesmo período no ano anterior. Gestores podem agrupar por vendedor.",
    billingSeries:
      "Soma das notas fiscais de saída no período escolhido. Selecione um cliente para ver só a curva dele. Presets iguais à Visão geral; opcionalmente compare com o ano anterior.",
    billingSeriesPeriod:
      "Recorte do gráfico (paridade Visão geral): hoje, semana, mês, mês passado, trimestre, ano, últimos 12 meses ou intervalo personalizado.",
    billingSeriesGrain:
      "Agrupamento da série. Dia e semana ficam indisponíveis quando o período é longo demais para aquele recorte.",
    billingSeriesYoy:
      "Sobrepõe o mesmo período filtrado deslocado −1 ano (linha tracejada). Alinhamento por bucket em qualquer granularidade permitida.",
    filterSearch: "Busca por código, loja, nome fantasia/razão ou número de pedido.",
    filterFocus:
      "Situação do pedido em aberto. Atenção = atraso ou atendimento parcial. Em dia = aberto sem atraso. Sem venda 60d usa a última NF quando o cadastro estiver coberto.",
    lateOrdersShortcut:
      "Abre Meus pedidos já filtrado em linhas com entrega atrasada (focus=late), sem novo dump TOTVS nesta tela.",
    filterTrend:
      "Tendência de faturamento (janela recente vs. a anterior de mesma duração). Combina com o foco operacional: um cliente em atenção pode estar em alta, estável ou queda.",
    trendWindow:
      "Janela da tendência: 7, 30 ou 90 dias (default 30), ou custom (1–365). Compara o período recente com o imediatamente anterior.",
    trendWindowCustom: "Quantidade de dias da janela recente (1–365). A janela anterior tem a mesma duração.",
    sellerScope:
      "Restringe a lista à carteira do vendedor selecionado. Sem seleção, considera as carteiras que você pode consultar.",
    portfolioAudit:
      "Linha do tempo das alterações na carteira (clientes, membros, responsável). Com «Todas» no filtro, escolha qual carteira acompanhar.",
    list: "Lista paginada da carteira. Clique na linha para abrir a Conta 360.",
    tableRowOpensDetail:
      "Clique na linha ou no nome do cliente abre a Conta 360. Controles internos com destino diferente não propagam o clique.",
    layoutToggle:
      "Alterna entre grade tabular (mais colunas) e cards (melhor em telas estreitas). A preferência fica salva neste navegador.",
    sortBy: "Campo usado para ordenar a lista (mesma ordenação da tabela e dos cards).",
    sortDirection: "Crescente ou decrescente no campo de ordenação selecionado.",
    cardOpenHint: "Abrir conta",
    cardAriaOpen: "Abrir Conta 360 do cliente",
    tableColumns:
      "Escolha a ordem e as colunas exibidas. A preferência fica salva neste navegador.",
    trend:
      "Comparamos o faturamento da janela recente com a janela anterior de mesma duração (default 30 dias; configurável em 7/30/90/custom). Se subir mais de 5%, mostramos alta (verde); se cair mais de 5%, mostramos queda; entre −5% e +5%, estável. Sem histórico suficiente, a tendência fica indefinida.",
    contacts:
      "Contatos da conta: cadastro TOTVS somente leitura e contatos locais da equipe comercial (CRUD + WhatsApp).",
    columns: {
      nome: "Nome fantasia/razão e código+loja da conta na carteira.",
      sellerName: "Vendedor/carteira responsável pelo cliente no escopo atual.",
      city: "Cidade e UF do cadastro TOTVS (quando o enriquecimento estiver disponível).",
      lastPurchaseDate: "Data da última nota fiscal de saída conhecida para a conta.",
      billed12m: "Soma do faturamento dos últimos 12 meses (quando coberto).",
      status: "Situação operacional na carteira (ativo, sem venda recente, etc.).",
      valorTotalAberto: "Soma do valor em aberto dos pedidos de venda desta conta.",
      quantidadePedidosAtrasados: "Quantidade de pedidos com linha vencida e saldo em aberto.",
      proximaEntrega: "Menor data de entrega prometida ainda em aberto nesta conta.",
    },
  },
  customerDetail: {
    header:
      "Visão integrada da conta: indicadores, pedidos em aberto, faturamento, atividades e próximos passos.",
    contacts:
      "Aba Contatos: dados oficiais TOTVS (read-only) e lista de contatos mantidos localmente pela equipe.",
    contactsTotvs:
      "Nome, telefone e e-mail do cadastro SA1. Não dá para editar aqui — use o Protheus se precisar corrigir.",
    contactsLocal:
      "Contatos complementares desta conta. Quem vê a Conta pode criar, editar e remover. No máximo um contato principal. Use o card colapsável para incluir ou editar.",
    contactFullName:
      "Nome completo do contato comercial local. Não altera o cadastro TOTVS da conta.",
    contactRoleTitle:
      "Cargo ou função do contato na conta, quando conhecido pela equipe.",
    contactChannel:
      "Canal preferencial de comunicação (telefone, e-mail, WhatsApp etc.).",
    contactEmail:
      "E-mail do contato local para comunicação comercial com a conta.",
    contactPhoneE164:
      "Use +, código do país, DDD e número. Ex.: +5547999999999.",
    whatsapp:
      "Abre o WhatsApp Web/app com saudação pronta (wa.me). Exige celular em formato brasileiro e canal WhatsApp marcado.",
    copyValue:
      "Copia o telefone ou e-mail para a área de transferência.",
    accountData:
      "Resumo cadastral e comercial da conta no recorte disponível, incluindo última venda, faturamento, situação e próxima ação.",
    billed12m: "Faturamento (NFs de saída) nos últimos 12 meses deste cliente.",
    openValue: "Soma do saldo em aberto dos pedidos deste cliente.",
    openOrders: "Quantidade de pedidos distintos ainda em aberto.",
    ordersScopeEmpty:
      "Nenhum pedido em aberto neste escopo para a conta. Contatos, histórico e demais abas seguem disponíveis.",
    outsidePortfolioNotice:
      "Cliente fora da sua carteira — dados da conta (histórico, oportunidades, contatos e pedidos deste cliente) permanecem disponíveis. Indicadores de cobertura de carteira ficam ocultos.",
    lastSale: "Data da última venda conhecida para o cliente (quando disponível).",
    purchaseEvolution:
      "Comparativo mês a mês: últimos 12 meses versus os 12 meses imediatamente anteriores.",
    purchaseEvolutionComparison:
      "Compara os últimos 12 meses com os 12 meses anteriores para evidenciar mudança de ritmo nas compras.",
    timeline:
      "Atividades e follow-ups registrados para esta conta, em ordem cronológica.",
    scheduleFollowUp:
      "Abre o Meu dia com este cliente já selecionado para criar um follow-up com prazo.",
    avatarChange:
      "Envia ou troca o logo da conta (JPEG, PNG, WebP ou GIF, até 2 MB). Quem vê a Conta pode alterar.",
    avatarRemove:
      "Remove o logo da conta. A ação fica registrada na timeline de auditoria da aba Contatos.",
    billingValue: "Total faturado no período selecionado nos filtros de notas.",
    billingInvoiceCount: "Quantidade de notas fiscais de saída no período.",
    billingLastDate: "Data da nota mais recente no período filtrado.",
    billingLastValue: "Valor da nota mais recente no período filtrado.",
    billingFilters: "Período e opções da consulta de faturamento deste cliente.",
    billingFilterDateStart:
      "Início do período das notas fiscais de saída listadas nesta conta.",
    billingFilterDateEnd: "Fim do período das notas fiscais de saída listadas nesta conta.",
    billingFilterSituation:
      "Restringe a lista a emitidas, devoluções ou todas as situações fiscais do período.",
    billingFilterSearch:
      "Busca por número da nota, série, pedido de venda ou código/descrição do produto.",
    billingSeriesCustomer:
      "Filtra a série de faturamento da carteira a um ou mais clientes (código+loja).",
    billingSeriesDateStart: "Início do intervalo personalizado da série de faturamento.",
    billingSeriesDateEnd: "Fim do intervalo personalizado da série de faturamento.",
    purchaseEvolutionPeriod:
      "Recorte do comparativo de compras (últimos 12 meses vs. período anterior).",
    opportunities:
      "Oportunidades de venda (OV) só deste cliente. Clique na linha ou no número da OV para abrir o detalhe.",
    tableRowOpensDetail:
      "Clique na linha ou na OV abre o detalhe da oportunidade. Controles internos com destino diferente não propagam o clique.",
    ordersColumns: {
      branch: "Unidade operacional (SC/ES) do pedido de venda.",
      order: "Número do pedido de venda no Protheus.",
      customerOrder: "Pedido de compra do cliente, quando informado.",
      status: "Situação consolidada do pedido (em dia, atraso, parcial).",
      lines: "Quantidade de linhas com saldo em aberto neste pedido.",
      overdue: "Maior atraso em dias entre as linhas em aberto.",
      delivery: "Próxima data de entrega prometida ainda em aberto.",
      value: "Valor em aberto consolidado do pedido.",
    },
    orderLinesColumns: {
      product: "Código do produto da linha do pedido.",
      ordered: "Quantidade pedida na linha.",
      delivered: "Quantidade já entregue/faturada.",
      balance: "Saldo ainda em aberto na linha.",
      delivery: "Data de entrega prometida da linha.",
      openValue: "Valor em aberto da linha.",
      delay: "Indicador de atraso da linha em relação à entrega prometida.",
    },
    invoiceColumns: {
      issue: "Data de emissão da nota fiscal de saída.",
      invoice: "Número e série da nota fiscal.",
      salesOrder: "Pedido de venda vinculado à nota.",
      customerOrder: "Pedido do cliente associado, quando houver.",
      situation: "Situação fiscal da nota (emitida, devolução, etc.).",
      items: "Quantidade de itens na nota.",
      value: "Valor total da nota no período filtrado.",
    },
    invoiceItemColumns: {
      item: "Sequência do item na nota.",
      product: "Código do produto faturado.",
      description: "Descrição do item na nota fiscal.",
      quantity: "Quantidade faturada no item.",
      unit: "Unidade de medida do item.",
      unitPrice: "Preço unitário do item.",
      total: "Valor total do item.",
      order: "Pedido de venda de origem do item.",
    },
  },
  sellerPortfolios: {
    list: "Carteiras cadastradas (usuários com acesso ao Portal Comercial + nome de exibição).",
    filter: "Filtre por situação (ativas/inativas), overlapping ou clientes sem cobertura.",
    filterOverlapping:
      "Mostra só carteiras ativas que compartilham ao menos um cliente (código+loja) com outra carteira.",
    filterUncovered:
      "Lista clientes com pedido em aberto que não estão em nenhuma carteira ativa (gap global).",
    overlappingCustomer:
      "Este cliente também está em outra carteira ativa. Revise a cobertura se for necessário.",
    create: "Cria uma carteira só com o nome. Responsáveis e membros entram depois no detalhe.",
    createDialog:
      "Informe o nome da carteira. Usuários responsáveis e membros são adicionados na tela de detalhe.",
    displayName:
      "Nome amigável no portal (seletor de escopo, lista e detalhe).",
    directoryUser:
      "Usuário com acesso ao Portal Comercial (busca por nome ou e-mail). O primeiro vira responsável.",
    members:
      "Usuários com acesso a esta carteira no Portal Comercial. Defina um responsável e inclua membros.",
    membersAdd:
      "Busque e adicione usuários que já têm acesso ao Portal Comercial. O primeiro usuário vira responsável se a carteira ainda não tiver.",
    setOwner: "Define este usuário como responsável da carteira.",
    removeMember: "Remove o acesso deste usuário à carteira (não apaga o usuário do portal).",
    edit: "Altera o nome de exibição da carteira selecionada.",
    customers:
      "Clientes vinculados a esta carteira. Busque e selecione vários para vincular de uma vez.",
    searchCustomers:
      "Busca no cadastro ativo TOTVS (código ou nome). Já vinculados não entram na seleção.",
    linkSelectedCustomers:
      "Inclui na carteira todos os clientes selecionados nos chips (até 20 por vez).",
    unlinkSelectedCustomers:
      "Remove da carteira os clientes marcados na tabela.",
    colDisplayName: "Nome da carteira no seletor de escopo e nas telas do portal.",
    colUserId: "Responsável da carteira (usuário Minha Delpi).",
    colCustomerCount: "Quantidade de clientes (código+loja) vinculados a esta carteira.",
    colMemberCount: "Quantidade de usuários com acesso a esta carteira (responsável + membros).",
    colCustomerCode: "Código e loja do cliente (chave cadastral TOTVS).",
    colCustomerName: "Nome fantasia ou razão social do cliente.",
    colCoverageHit:
      "Indica se o cliente da busca já está nesta carteira ou em outra carteira ativa.",
    colMemberUser: "Usuário Minha Delpi com acesso a esta carteira.",
    colMemberRole: "Papel na carteira: responsável ou membro.",
    colUncoveredOpenValue:
      "Soma do valor em aberto dos pedidos do cliente sem cobertura de carteira.",
    colOpenValue:
      "Soma do valor em aberto dos pedidos da carteira (TOTVS). Exibe — se a agregação falhar.",
    colAttentionCount:
      "Clientes da carteira com pedido em atraso (entrega < hoje e saldo > 0). Exibe — se a agregação falhar.",
    colStatus: "Ativa: aparece no escopo. Inativa: ocultada para operação normal.",
    bulkTransferConfirmFrom:
      "Carteira de origem da transferência (somente leitura neste passo).",
    layoutToggle: "Alterna a lista entre tabela e cards, com o mesmo recorte.",
    shellViewToggle: "Lista mostra o cadastro em tabela/cards. Organização mostra o organograma interativo carteira ↔ pessoa (pan/zoom).",
    orgAxisToggle: "Inverte a raiz do organograma: por carteira (membros abaixo) ou por pessoa (carteiras abaixo).",
    orgLoadSnippet:
      "Carga compacta: clientes, valor aberto, atenção e membros (ou carteiras no eixo pessoa).",
    cardOpenHint: "Abrir carteira",
    deactivate:
      "A carteira sai do escopo operacional. Os clientes continuam vinculados.",
    purge:
      "Apaga a carteira em definitivo. Os clientes vinculados serão desvinculados.",
    transfer:
      "Move clientes de uma carteira para outra com motivo registrado (auditoria).",
    transferSource: "Carteira de onde os clientes saem.",
    transferTarget: "Carteira que recebe os clientes.",
    transferCustomers: "Selecione um ou mais clientes da carteira de origem.",
    transferReason: "Motivo obrigatório da transferência (fica no histórico).",
    bulkTransferWizard:
      "Wizard em etapas para transferir vários clientes entre carteiras, com motivo e auditoria.",
    exportOrgMatrix:
      "Gera planilha Excel da matriz de organização (carteira, membros, clientes e valor aberto).",
    auditTimeline:
      "Registro completo da carteira: vínculo/desvínculo de clientes, membros, responsável, transferência, nome e ativação.",
  },
  analytics: {
    portfolioFilter:
      "Não filtrar = indicadores no consolidado global (TOTVS). Selecione uma ou mais carteiras (ou «Selecionar visíveis») para restringir ao escopo dessas carteiras.",
    filters:
      "Período, competência, unidade (Santa Catarina / Espírito Santo), segmento e carteira(s) aplicados aos painéis e listas desta página.",
    filterDateStart: "Início do período analítico.",
    filterDateEnd: "Fim do período analítico.",
    filterPeriodPreset:
      "Atalhos de período (hoje, semana, mês, mês passado, trimestre, ano, últimos 12 meses) no fuso America/Sao_Paulo. Personalizado mantém as datas que você informar.",
    filterCompetence:
      "Mês de referência (aaaa-mm). Ao selecionar, ajusta o período para o mês inteiro — ou até hoje, no mês corrente. Vazio = só as datas informadas.",
    filterBranch:
      "Unidades incluídas no consolidado (Santa Catarina / Espírito Santo). Vazio = todas as unidades do escopo.",
    filterSegment: "Segmento de cliente (TOTVS). Vazio = todos.",
    otdPage:
      "Pontualidade de linhas de pedido no período: KPIs, série por unidade, insights e linhas com busca/filtro/ordenação.",
    otdKpi: "OTD %, linhas no prazo e atrasadas no período filtrado.",
    otdKpiLatePct: "Percentual de linhas atrasadas sobre o total elegível no período.",
    otdKpiLateDays:
      "Distribuição dos dias de atraso (média, P50 e P90) apenas nas linhas classificadas como atrasadas.",
    otdSeries:
      "Evolução do OTD por Santa Catarina e Espírito Santo no período.",
    otdLines:
      "Linhas do período com busca, status, ordenação e paginação no servidor. Clique abre o detalhe.",
    otdLinesSearch: "Busca por pedido, cliente ou produto.",
    otdLinesStatus: "Filtra linhas no prazo ou atrasadas (server-side).",
    otdRecurrence:
      "Clientes com duas ou mais linhas atrasadas no período (top 10 por quantidade).",
    otdWorstDelays: "Top 10 linhas com maior atraso em dias no período.",
    otdUpcomingPromises:
      "Top 10 linhas ainda não faturadas com a promessa mais próxima.",
    opportunitiesPage:
      "Lista global de oportunidades de venda (OV) no período. Use a Conta para ver só um cliente.",
    opportunitiesList: "OVs do período. Clique na linha ou no número da OV para abrir o detalhe.",
    tableRowOpensDetail:
      "Clique na linha (ou na identidade) abre o detalhe. Controles internos com destino diferente não propagam o clique.",
    ovStatus: "Etapa atual da oportunidade comercial.",
    ovOpen: "Data de abertura da oportunidade.",
    ovClose: "Data de fechamento ou assinatura, quando houver.",
    ovHeader:
      "Resumo da oportunidade: unidade, revisão, processo, etapa e descrição.",
    ovCustomer: "Cliente e vendedor responsáveis pela oportunidade.",
    ovProducts: "Produtos da oportunidade: código, descrição, grupo, tipo e quantidade.",
    ovBom: "Estrutura de componentes de cada produto da oportunidade.",
    ovHistory:
      "Histórico da oportunidade em ordem cronológica, com os principais eventos comerciais.",
    searchOpportunities:
      "Filtra a lista por número da OV, código ou nome do cliente no período selecionado.",
    columns: {
      order: "Número do pedido e item da linha avaliada no OTD.",
      branch: "Unidade operacional (Santa Catarina ou Espírito Santo) da linha.",
      customer: "Cliente da linha do pedido (nome ou código).",
      product: "Código do produto da linha no período OTD.",
      productDesc: "Descrição do produto (truncada na lista).",
      status: "Pontualidade da linha: no prazo ou atrasado no período.",
      promised: "Data de entrega prometida usada no cálculo de OTD.",
      invoice: "Data de faturamento da linha, quando houver.",
      daysDiff: "Diferença em dias entre a promessa e o faturamento (ou data de referência se aberta).",
      qty: "Quantidade vendida da linha.",
      periodo: "Competência ou bucket da série OTD (mês/período).",
    },
    oppDetailColumns: {
      code: "Código comercial do produto na oportunidade.",
      desc: "Descrição do produto cadastrada na OV.",
      group: "Grupo de produto do item na oportunidade.",
      type: "Tipo do produto (PA, PI ou outro) na OV.",
      qty: "Quantidade de produto intermediário (PI) vinculada.",
      rev: "Número da revisão do evento no histórico da OV.",
      process: "Processo comercial associado ao evento do histórico.",
      stage: "Etapa do processo no momento do evento.",
      start: "Data de início registrada para o evento do histórico.",
      end: "Data de fim registrada para o evento do histórico.",
      dur: "Duração do evento (início até fim) no histórico.",
      status: "Situação do evento no histórico da oportunidade.",
    },
    teamColumns: {
      name: "Nome do vendedor ou carteira ativa na equipe.",
      customers: "Quantidade de clientes vinculados à carteira.",
      lines: "Linhas de pedido em aberto na carteira do vendedor.",
      openValue: "Soma do valor em aberto dos pedidos da carteira.",
    },
  },
  overview: {
    page:
      "Dashboard do período: filtros, indicadores (≤8), evolução ROL (com YoY opcional), série de conversão e funil. Sem lista de OVs nem faixa Aprofundar.",
    filters:
      "Datas, competência, atalho de período (hoje…últimos 12 meses), unidade, segmento e carteira (quando permitido) aplicados aos painéis de período. O KPI «Carteira em aberto» é snapshot agora e ignora o período.",
    kpis: "Indicadores do período: ROL vs meta, conversão, OTD% e novos negócios. «Carteira em aberto» é saldo comercial atual (pedidos) — não some com ROL e não é programação do PCP.",
    rolSeries:
      "Evolução do ROL por Santa Catarina e Espírito Santo no período selecionado.",
    rolSeriesYoy:
      "Sobrepõe o mesmo período filtrado deslocado −1 ano (linhas tracejadas), em Dia/Semana/Mês/Ano. Alinhamento por bucket; drill só no período atual.",
    closingRateSeries:
      "Evolução da taxa de conversão (hit rate) por Santa Catarina e Espírito Santo. Cada ponto usa a mesma fórmula do KPI no intervalo do bucket.",
    closingRateSeriesYoy:
      "Sobrepõe hit rate do mesmo período filtrado −1 ano (tracejado), em qualquer granularidade. Mesma regra de buckets; drill só no período atual.",
    funnel:
      "Funil de conversão: propostas abertas no período (denominador) versus ganhas com status TOTVS 9 e data de aceite no período (numerador). Cohorts podem diferir — ver ficha KPI-HIT-RATE.",
    closingRate:
      "Taxa de conversão (hit rate): propostas ganhas (AD1_STATUS=9, aceite no período) ÷ revisões abertas no período. Metodologia atual do Portal — não alterar sem homologação.",
    openPortfolio:
      "Carteira comercial em aberto agora: valor e linhas de pedidos/compromissos. Não é programação do PCP, não é forecast e não deve ser somada ao ROL do período (bases diferentes).",
    gapToTarget:
      "Gap vs meta ROL SI do período filtrado. A carteira «este mês» aparece só como contexto — nunca some gap + carteira.",
    openPortfolioHorizon:
      "Buckets por data de entrega dos pedidos em aberto (snapshot). Clique concentra Meus pedidos; ≠ PCP e ≠ forecast F6.",
    glossaryOpenVsBilled:
      "Glossário: «Carteira aberta» = backlog de pedidos ainda não faturados (snapshot). «Faturamento / ROL» = notas/receita líquida no período filtrado. Não somar nem comparar % entre as duas bases.",
    portfolioBillingShare:
      "Percentual do ROL do escopo atual sobre o ROL consolidado da empresa no mesmo período (carteira ÷ empresa). Visível só com analytics, visão de equipe ou gestão de carteiras — não mistura com valor em aberto.",
  },
  administration: {
    panel:
      "Resumo de cobertura das carteiras e atalhos para cadastro, transferência e membros.",
    portfolios: "CRUD de carteiras, organização, membros e transferência de clientes.",
    members: "Roster de pessoas com acesso às carteiras ativas do Portal.",
    teamSearch: "Filtra a lista de pessoas por nome ou e-mail.",
    teamFilterGroup: "Mostra só membros do grupo operacional selecionado.",
    teamFilterPortfolio: "Mostra só pessoas com acesso à carteira selecionada.",
    groupCreateName: "Nome do grupo operacional (visível na Equipe e no MyDay).",
    groupRename: "Altera o nome de exibição do grupo. O tipo (kind) não muda aqui.",
    teamColPerson: "Pessoa com acesso ao Portal Comercial e vínculo a grupos/carteiras.",
    teamColOnline: "Presença em tempo real no Portal (online/offline).",
    teamColEmail: "E-mail do diretório Minha Delpi.",
    teamColGroups: "Grupos operacionais dos quais a pessoa é membro.",
    teamColPortfolios: "Carteiras às quais a pessoa tem acesso.",
  },
  proposals: {
    page: "Propostas-documento: lista e emissão de PDF. Não confundir com OVs em Oportunidades.",
    list: "Catálogo de propostas-documento. Clique na linha ou na proposta interna para abrir o detalhe.",
    search: "Busca por OV, proposta interna, oportunidade ou cliente.",
    layoutToggle:
      "Alterna entre tabela densa e cards. A preferência fica salva neste navegador.",
    scopeNote:
      "O menu do usuário no topo leva a Minha Carteira filtrada; a lista de propostas-documento não filtra por carteira — é o catálogo com permissão de propostas.",
    tableRowOpensDetail:
      "Clique na linha (ou na proposta) abre o detalhe do documento. Controles internos com destino diferente não propagam o clique.",
    cardOpenHint: "Abrir proposta",
    pdfContact:
      "Contato base da Conta usado para pré-preencher os campos do PDF. Vale só para esta emissão.",
    pdfContactNome:
      "Nome exibido no PDF. Não grava no cadastro da Conta nem na proposta.",
    pdfContactDepartamento:
      "Departamento exibido no PDF. Não grava no cadastro da Conta nem na proposta.",
    pdfContactEmail:
      "E-mail exibido no PDF. Não grava no cadastro da Conta nem na proposta.",
    pdfContactTelefone:
      "Telefone exibido no PDF. Não grava no cadastro da Conta nem na proposta.",
    pdfObservacoes:
      "Observações incluídas só neste PDF. Não alteram a proposta salva.",
    columns: {
      ov: "Número da oportunidade de venda vinculada à proposta-documento.",
      item: "Sequência do item na proposta-documento.",
      produto: "Código do produto do item na proposta.",
      desc: "Descrição comercial do item na proposta-documento.",
      qty: "Quantidade pedida do item nesta proposta.",
      total: "Valor total do item na proposta-documento.",
      prazo: "Prazo de entrega do item em dias, quando informado.",
    },
  },
} as const;

/** Alias estável usado na coluna Tendência da carteira. */
export const BILLING_TREND_HELP = CM_HELP.customers.trend;

/** Alias estável do help do share carteira÷empresa. */
export const PORTFOLIO_BILLING_SHARE_HELP = CM_HELP.customers.portfolioBillingShare;
