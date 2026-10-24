export const PURCHASE_REQUESTS_CONTENT = {
  title: "Solicitações de compras",
  eyebrow: "Portal Suprimentos",
  description:
    "Acompanhamento global das solicitações no período. A unidade é filtro, não permissão. Clique na SC para abrir a ficha.",
  helpAriaLabel: "Ajuda sobre solicitações de compras",
  filtersAriaLabel: "Filtros de solicitações de compras",
  filtersTitle: "Filtros",
  listTitle: "Lista de solicitações",
  listHint:
    "Clique na SC ou na linha para abrir a ficha. Lista vazia significa ausência de item no período ou nos filtros.",
  tableMeta: (columns: number, requests: number) =>
    `${columns} coluna(s) · ${requests.toLocaleString("pt-BR")} SC(s)`,
  cardsMeta: (requests: number) => `${requests.toLocaleString("pt-BR")} SC(s)`,
  heroRequests: "Solicitações",
  heroOrdering: "Aguardando pedido",
  heroReceiving: "Aguardando recebimento",
  attentionLabel: "Atenção",
  attentionAriaLabel: "Atalhos de situação das solicitações",
  attentionAll: "Todos",
  attentionOrdering: "Aguardando pedido",
  attentionReceiving: "Aguardando recebimento",
  attentionCompleted: "Concluídas",
  attentionAllWithCount: (count: number) => `Todos (${count.toLocaleString("pt-BR")})`,
  attentionOrderingWithCount: (count: number) =>
    `Aguardando pedido (${count.toLocaleString("pt-BR")})`,
  attentionReceivingWithCount: (count: number) =>
    `Aguardando recebimento (${count.toLocaleString("pt-BR")})`,
  attentionCompletedWithCount: (count: number) =>
    `Concluídas (${count.toLocaleString("pt-BR")})`,
  openScLinkTitle: (number: string) => `Abrir solicitação ${number}`,
  branchLabel: "Unidade",
  dateFromLabel: "De",
  dateToLabel: "Até",
  periodLabel: "Período",
  requestNumberLabel: "Número SC",
  productLabel: "Produto",
  requesterLabel: "Solicitante",
  requesterAll: "Todos",
  costCenterLabel: "Centro de custo",
  costCenterAll: "Todos",
  stageLabel: "Situação",
  stageAll: "Todas",
  sortByLabel: "Ordenar por",
  sortAscLabel: "Crescente",
  sortDescLabel: "Decrescente",
  sortDirectionAriaLabel: "Direção da ordenação",
  clearFilters: "Limpar",
  refreshAction: "Atualizar",
  updatedAtLabel: (time: string) => `Atualizado às ${time}`,
  exportLabel: "Excel",
  exportTitle: "Baixa o recorte filtrado em Excel",
  excelExporting: "Gerando Excel…",
  excelError: "Não foi possível exportar o Excel.",
  viewAriaLabel: "Modo de visualização",
  viewTable: "Tabela",
  viewCards: "Cards",
  cardsAriaLabel: "Cards de solicitações de compra",
  cardRequester: "Solicitante",
  cardCc: "Centro de custo",
  cardOpened: "Abertura",
  cardStage: "Situação",
  loading: "Carregando solicitações…",
  emptyTitle: "Nenhuma solicitação neste recorte",
  emptyMessage:
    "Ajuste filtros ou período. Nesta tela o uso normal do Portal acompanha as solicitações das duas unidades.",
  noUnitsTitle: "Nenhuma unidade liberada",
  noUnitsMessage:
    "Seu acesso não inclui unidades neste módulo. Peça o escopo canônico ao administrador.",
  error: "Não foi possível carregar as solicitações.",
  stageSortTooLarge:
    "Ordenação por situação exige um recorte menor. Reduza o período ou selecione uma unidade.",
  forbiddenUnit:
    "Você não tem permissão para esta unidade neste módulo. Escolha outra unidade liberada ou peça o acesso canônico ao administrador.",
  retry: "Tentar novamente",
  detailTitle: "Solicitação",
  detailEyebrow: "Solicitação de compra",
  detailDescription:
    "Dados da solicitação e de todos os itens. A unidade é o recorte do filtro.",
  detailHint: "Itens da solicitação no recorte escolhido.",
  detailBack: "Solicitações de compras",
  detailLoading: "Carregando a solicitação…",
  detailError: "Não foi possível carregar esta solicitação de compra.",
  detailNotFound: "Solicitação não encontrada no seu escopo.",
  detailForbidden:
    "Você não tem permissão para esta unidade neste módulo. Peça o acesso canônico ao administrador.",
  detailRetry: "Tentar novamente",
  detailUnitLabel: "Unidade",
  detailRequesterLabel: "Solicitante",
  detailOpenedLabel: "Abertura",
  detailStageLabel: "Situação",
  detailCostCenterLabel: "Centro de custo",
  detailCostCenterOthers: (count: number) =>
    `Centros de custo da solicitação: ${count} — ver lista completa`,
  detailApprovalLabel: "Aprovação",
  detailApproversMany: (count: number) => `${count} aprovadores`,
  detailIndicatorItems: "Itens visíveis",
  detailIndicatorOrders: "Pedidos vinculados",
  detailIndicatorOverdue: "Atraso",
  detailOverdueNone: "Sem atraso",
  detailOverdueYes: "Em atraso",
  detailOverdueDays: (days: number) => `até ${days} ${days === 1 ? "dia" : "dias"}`,
  detailScopeNote:
    "Itens e indicadores respeitam o escopo de centros de custo visível para o seu usuário.",
  approvalApproved: "Aprovada",
  approvalRejected: "Rejeitada",
  approvalBlocked: "Bloqueada",
  approvalUnknown: "Não informada",
  itemsTitle: "Itens",
  itemsEmpty: "Esta solicitação não retornou itens visíveis no seu escopo.",
  colRequestedQty: "Solicitada",
  colOrderedQty: "Em pedido",
  colOpenQty: "Saldo",
  colRequiredDate: "Necessidade",
  colSuggestedSupplier: "Fornecedor sugerido",
  colAccountCode: "Conta contábil",
  ordersTitle: "Pedidos vinculados",
  ordersEmpty: "Nenhum pedido vinculado aos itens visíveis desta solicitação.",
  openOrderTitle: (number: string) => `Abrir pedido de compra ${number}`,
  colOrderNumber: "PC",
  colOrderItem: "Item PC",
  colOrderProduct: "Produto",
  colOrderSupplier: "Fornecedor",
  colOrderQty: "Pedida",
  colReceivedQty: "Recebida",
  colOrderOpenQty: "Saldo",
  colExpectedDelivery: "Prevista",
  colDeliveryStatus: "Entrega",
  ordersTableScrollRegion:
    "Tabela de pedidos vinculados — deslize horizontalmente para ver todas as colunas",
  receiptsTitle: "Recebimentos",
  receiptsEmpty: "Nenhum recebimento registrado nos pedidos vinculados.",
  colInvoice: "NF",
  colInvoiceSeries: "Série",
  colInvoiceItem: "Item NF",
  colReceiptOrder: "PC",
  colReceiptQty: "Qtd.",
  colReceiptValue: "Valor",
  colInvoiceDate: "Emissão NF",
  colEntryDate: "Entrada",
  receiptsTableScrollRegion:
    "Tabela de recebimentos — deslize horizontalmente para ver todas as colunas",
  timelineTitle: "Acompanhamento",
  timelineHint:
    "Eventos derivados dos dados da solicitação — não é um histórico auditável. «Prevista» marca datas planejadas, não ocorrências.",
  timelineEmpty: "Sem eventos derivados para os itens visíveis desta solicitação.",
  timelineListLabel: "Eventos do acompanhamento",
  timelinePlannedSuffix: "prevista",
  timelineRefOrder: (number: string) => `PC ${number}`,
  timelineRefInvoice: (number: string) => `NF ${number}`,
  timelineRefItem: (item: string) => `Item ${item}`,
  colSc: "SC",
  colItem: "Item",
  colProduct: "Produto",
  colRequester: "Solicitante",
  colCc: "Centro de custo",
  colOpened: "Abertura",
  colStage: "Situação",
  tableScrollRegion:
    "Tabela de solicitações — deslize horizontalmente para ver todas as colunas",
} as const;

export function mapPurchaseRequestsFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return PURCHASE_REQUESTS_CONTENT.forbiddenUnit;
  }
  if (
    /recorte menor/i.test(message) ||
    (/422/.test(message) && /situação|situacao|overall_stage|ordenação por situação/i.test(message))
  ) {
    return PURCHASE_REQUESTS_CONTENT.stageSortTooLarge;
  }
  return message || PURCHASE_REQUESTS_CONTENT.error;
}

export function classifyPurchaseRequestDetailError(message: string): {
  kind: "forbidden" | "not_found" | "error";
  text: string;
} {
  if (/403|forbidden/i.test(message)) {
    return { kind: "forbidden", text: PURCHASE_REQUESTS_CONTENT.detailForbidden };
  }
  if (/404|não encontrada|not found/i.test(message)) {
    return { kind: "not_found", text: PURCHASE_REQUESTS_CONTENT.detailNotFound };
  }
  return {
    kind: "error",
    text: message || PURCHASE_REQUESTS_CONTENT.detailError,
  };
}
