/** Textos dos balões de explicação — PT de negócio, sem path técnico. */

const HOME_HELP = {
  vsOverview:
    "Início é ação e descoberta. Visão geral é o painel de KPIs do período — só aparece se você tiver acesso analítico.",
  attention:
    "Atalhos autorizados para o que precisa de ação. Contagens ao vivo entram nas próximas jornadas; se este bloco falhar, os caminhos abaixo continuam disponíveis.",
  paths:
    "Caminhos por seção liberados para o seu acesso. Busque, fixe favoritos e reabra os últimos acessos. Objetivo: chegar à ação em poucos cliques.",
  search:
    "Filtra seções e rotas do catálogo pelo nome ou palavras-chave. Também dá para buscar na barra superior (Ctrl/Cmd+K).",
  favorites:
    "Atalhos que você fixou com a estrela nos caminhos. Ficam neste navegador e só mostram áreas ainda liberadas para você.",
  recents:
    "Últimas áreas abertas neste navegador. A lista respeita as permissões atuais.",
  queueOk:
    "Nenhum atalho de atenção pendente no momento. Os caminhos e a busca abaixo continuam disponíveis.",
  heroAttention:
    "Quantidade de atalhos de atenção disponíveis agora. «Em dia» significa que não há pendências neste bloco.",
  heroUnits:
    "Quantas filiais estão liberadas no seu escopo do Portal. Os dados operacionais respeitam esse limite.",
  heroOverview:
    "Atalho para a Visão geral (KPIs do período). Só aparece liberado se você tiver acesso analítico.",
  scopeBadge:
    "Filiais liberadas na sessão. Sem filial no escopo, módulos TOTVS podem vir vazios ou bloqueados.",
  sections: {
    attention:
      "Entrada do Portal e fila pessoal (Minhas tarefas) — ação do dia, sem misturar com o painel de KPIs.",
    analytics:
      "Visão geral, negociações e indicadores do período. Não substitui o bloco Atenção do Início.",
    purchase_requests:
      "Solicitações de compras no escopo de centro de custo e filial. Lista vazia pode significar falta de CC, não ausência de SC.",
    operations:
      "Pedidos, entregas, fornecedores, produtos, estoque físico e estoque de segurança (ESTSEG).",
    administration:
      "Mappings, escopos e configurações do Portal — só com permissão de administrar.",
    help: "Manual do usuário: Quero→onde, FAQ e glossário do Portal Suprimentos.",
  },
} as const;

export const SP_HELP = {
  shell: {
    navHome: "Atenção do dia, busca e atalhos para as áreas que você pode acessar.",
    navOverview:
      "Indicadores do período. Não é a tela inicial — o Início mostra o que precisa de ação.",
    navMyTasks: "Fila de acompanhamento atribuída a você.",
    navPurchaseRequests: "Solicitações de compras no seu escopo de centro de custo e filial.",
    navOperations: "Pedidos, entregas, fornecedores, produtos e estoques autorizados.",
    navAdmin: "Mappings, escopos e configurações do Portal.",
    navHelp: "O que é o Portal, diferença para os apps antigos e o que fazer em 403.",
  },
  coexistence:
    "O Portal Suprimentos reúne as jornadas. Os apps antigos (cockpit, SC, estoque de segurança) continuam no launcher até o cutover.",
  home: HOME_HELP,
  /** Alias estável para consumidores existentes. */
  homeVsOverview: HOME_HELP.vsOverview,
  homeAttention: HOME_HELP.attention,
  overviewTemporal:
    "Cada card tem natureza temporal própria: intervalo (OTD, CPV, economia), snapshot (estoque, críticos) ou estado atual (SC pendentes). Início não substitui este painel.",
  overviewFiltersPeriod:
    "Atalhos de período (Hoje, Esta semana, Este mês, trimestre, ano, 12 meses…). Ao mudar datas manualmente, o preset vira Personalizado. O recorte fica na URL (F5/compartilhar).",
  overviewFiltersFrom: "Data inicial do recorte analítico compartilhado na URL.",
  overviewFiltersTo: "Data final do recorte analítico compartilhado na URL.",
  overviewFiltersBranch:
    "Unidades liberadas no seu escopo (Santa Catarina e/ou Espírito Santo). Vazio ou ambas = consolidado. Unidade fora do escopo é bloqueada pela API.",
  overviewGoalTriad:
    "Meta do período vem do SI (comparable_goal). Para estoque (snapshot), a meta é o nível/teto cadastrado — não há pró-rata diária nem soma de meses. Meta mês/referência é a meta cadastrada consolidada. Nota IDD é o score do SI — não é recalculada no navegador.",
  overviewOtdChart:
    "Série de OTD de pedidos de compra com ChartViewShell completo (granularidade, tipo, YoY, cores e exportação). Usa o mesmo filtro de unidade e período da Visão geral. Abra OTD para ver os velocímetros.",
  overviewCompareChart:
    "Barras valor × meta só para KPIs de intervalo que já vieram no overview — com tipo, cores e exportação; não inventa série CPV/Savings.",
  otdAnalyticsPage:
    "Pontualidade de compras com velocímetros por unidade (Santa Catarina / Espírito Santo) e evolução no tempo. Diferente da Visão geral (placar de KPIs) e de Entregas (atrasos do dia).",
  purchaseRequests:
    "Lista linhas de SC no escopo de centro de custo e unidades. Sem CC liberado e sem visão ampla, a lista fica vazia (fail-closed). Exportação Excel/CSV exige permissão separada. Clique na SC ou na linha para abrir a ficha.",
  purchaseRequestsBranch:
    "Unidade do recorte (Santa Catarina e/ou Espírito Santo). «Todas» consulta todas as unidades liberadas na sessão. Códigos técnicos ficam só na URL e na API.",
  purchaseRequestsView:
    "Tabela ou Cards usam o mesmo recorte paginado. A preferência fica neste navegador e não muda dados nem permissões.",
  purchaseRequestsSort:
    "Ordene pelo cabeçalho da tabela ou, em Cards, por «Ordenar por» + Crescente/Decrescente. Colunas: SC, item, produto, solicitante, centro de custo, abertura e situação. A URL guarda sort_by e sort_dir; F5 restaura a ordem no recorte inteiro (não só a página). Situação processa o período selecionado e, se o volume for grande demais, pede um recorte menor (período ou unidade).",
  purchaseRequestsSortDirection:
    "Alterna crescente ou decrescente na mesma coluna. Vale para Cards e compartilha sort_by/sort_dir com a tabela.",
  purchaseRequestsPeriod:
    "Período de abertura da SC (em Mais filtros). Use os atalhos (Hoje, Esta semana…) ou as datas; editar datas manualmente vira Personalizado. Compartilhável pela URL via date_from/date_to (F5 restaura o recorte; o atalho é derivado das datas).",
  purchaseRequestsNumber: "Filtra pelo número da solicitação de compras.",
  purchaseRequestsProduct: "Filtra por código ou trecho de produto/MP da linha.",
  purchaseRequestsStage:
    "Situação consolidada da SC (aguardando pedido, parcial, concluída etc.).",
  purchaseRequestsExport:
    "Exporta para Excel o recorte filtrado inteiro (todas as unidades selecionadas), sem truncar na página. Exige permissão de exportação além do acesso à lista. CSV permanece disponível como formato legado.",
  purchaseRequestsFilters:
    "Filtros aplicam automaticamente. Texto confirma após um instante ou com Enter. Mais filtros revela o período e os atalhos. Limpar só aparece quando há filtro além do padrão (todas as unidades liberadas e período baseline não contam sozinhos).",
  purchaseRequestsRefresh:
    "Recarrega a lista com os mesmos filtros. O horário é da última consulta bem-sucedida nesta tela, não do TOTVS.",
  purchaseRequestsTableFontSize:
    "Ajusta o tamanho da fonte da tabela neste navegador. A preferência fica salva localmente.",
  purchaseRequestsTableColumns:
    "Escolha quais colunas exibir e arraste para reordenar. A preferência fica salva neste navegador; não altera permissões nem dados.",
  purchaseRequestsTableMeta:
    "Contagem de colunas visíveis nesta tabela e total de linhas do recorte filtrado (não só a página atual).",
  purchaseRequestsColCc: "Centro de custo da linha no escopo liberado ao usuário.",
  purchaseRequestsColOpened: "Data de abertura da solicitação de compras.",
  purchaseRequestsColStage: "Situação consolidada da SC a partir do andamento dos itens.",
  purchaseRequestsEntityLink:
    "O número da SC abre a ficha em página própria (/purchase-requests/unidade/número). Você também pode clicar na linha ou no card.",
  purchaseRequestDetail:
    "Ficha da solicitação de compra no escopo de centro de custo. Itens fora do seu CC não aparecem. Use Voltar para retornar à lista com os filtros anteriores.",
  purchaseOrders:
    "Pedidos de compra em aberto (saldo a receber). O hero mostra linhas em aberto, valor em aberto e atrasadas do recorte das unidades e filtros selecionados (o chip Atrasados não muda os totais). Não é o painel OTD de pontualidade — esse fica na analytics. Clique no PC ou na linha para abrir a ficha.",
  purchaseOrdersBranch:
    "Unidade do recorte (Santa Catarina e/ou Espírito Santo). «Todas» consulta todas as unidades liberadas na sessão. Códigos técnicos ficam só na URL e na API.",
  purchaseOrdersNumber: "Filtra pelo número do pedido de compra.",
  purchaseOrdersProduct: "Filtra por código de produto/MP da linha.",
  purchaseOrdersSupplier: "Filtra pelo código do fornecedor (A2).",
  purchaseOrdersDelivery:
    "Período de entrega prometida (em Mais filtros). Use os atalhos (Hoje, Esta semana…) ou as datas; editar datas manualmente vira Personalizado. O chip «Atrasados» em Atenção filtra linhas com prometida anterior a hoje. F5 deriva o atalho das datas na URL (sem param de preset).",
  purchaseOrdersAttention:
    "Todos (N) e Atrasados (N) usam o resumo do servidor no mesmo recorte de filtros; alternar o chip não muda os contadores. A URL guarda late_only para compartilhar ou atualizar (F5).",
  purchaseOrdersRefresh:
    "Recarrega a lista e o resumo com os mesmos filtros. O horário é da última consulta bem-sucedida nesta tela, não do TOTVS.",
  purchaseOrdersFilters:
    "Filtros aplicam automaticamente. Texto confirma após um instante ou com Enter. Mais filtros revela o período de entrega e os atalhos. Limpar só aparece quando há filtro além do padrão (todas as unidades liberadas não contam sozinhas).",
  purchaseOrdersView:
    "Tabela ou Cards usam o mesmo recorte paginado. A preferência fica neste navegador e não muda dados nem permissões.",
  purchaseOrdersSort:
    "Ordene pelo cabeçalho da tabela ou, em Cards, por «Ordenar por» + Crescente/Decrescente. A URL guarda sort_by e sort_dir; F5 restaura a ordem no recorte inteiro (não só a página atual).",
  purchaseOrdersSortDirection:
    "Alterna crescente ou decrescente na mesma coluna. Vale para Cards e compartilha sort_by/sort_dir com a tabela.",
  purchaseOrdersExcel:
    "Exporta para Excel o recorte filtrado inteiro (todas as unidades selecionadas), sem truncar na página. Exige o mesmo acesso de operações e as unidades pedidas.",
  purchaseOrdersTableFontSize:
    "Ajusta o tamanho da fonte da tabela neste navegador. Use − / + ou restaurar o padrão. A preferência fica salva localmente.",
  purchaseOrdersTableColumns:
    "Marque ou desmarque colunas e arraste pelo handle para reordenar. Restaurar volta ao padrão. A preferência fica salva neste navegador; não altera permissões nem dados.",
  purchaseOrdersTableMeta:
    "Contagem de colunas visíveis nesta tabela e total de linhas do recorte filtrado (não só a página atual).",
  purchaseOrdersColOpenQty: "Quantidade ainda em aberto (saldo a receber) nesta linha.",
  purchaseOrdersColDelivery: "Data prometida de entrega do item.",
  purchaseOrdersColStatus: "Situação em relação à data prometida: atrasado, no prazo ou sem data.",
  purchaseOrdersColOpenValue: "Valor em aberto da linha (saldo × preço).",
  purchaseOrdersEntityLink:
    "O número do PC abre a ficha do pedido. Você também pode clicar na linha.",
  purchaseOrderDetail:
    "Ficha somente leitura do pedido em aberto: itens, data prometida, recebimentos e a SC de origem de cada item. Copie o endereço da página para compartilhar; atualizar restaura a mesma ficha. Pedidos encerrados não aparecem.",
  purchaseOrderDetailItems:
    "Cada item traz fornecedor, quantidades, entrega prometida e a solicitação de origem. Um mesmo pedido pode ter itens de solicitações e fornecedores diferentes.",
  purchaseOrderDetailReceipts:
    "Recebimentos do item, com nota, quantidade, datas de emissão e entrada. Se a lista estiver vazia, ainda não há documento de entrada para aquela linha.",
  userProfile:
    "Perfil do Portal Suprimentos: identidade Minha DELPI (foto, cargo e contatos da Core, só leitura), atalhos por capability e preferências (filial padrão e densidade). Edite foto/cargo/contatos em /profile do Portal host.",
  userProfilePrefs:
    "Filial padrão e densidade de tabelas valem só neste Portal. Só você edita o próprio perfil; administradores podem ler outros usuários.",
  forbiddenUnit:
    "Você não tem permissão para esta filial ou para este módulo. Peça o acesso canônico do Portal ao administrador — aliases antigos sozinhos não abrem o app.",
} as const;
