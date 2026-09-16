export const PURCHASE_ORDERS_CONTENT = {
  title: "Pedidos de compra",
  eyebrow: "Portal Suprimentos",
  description:
    "Itens de pedidos de compra com saldo pendente de recebimento no recorte selecionado. Clique no PC para abrir a ficha.",
  helpAriaLabel: "Ajuda sobre pedidos de compra",
  filtersAriaLabel: "Filtros de pedidos de compra",
  filtersTitle: "Filtros",
  listTitle: "Pedidos em aberto",
  listHint:
    "Somente itens com saldo pendente de recebimento. Clique no PC ou na linha para abrir itens, datas prometidas, recebimentos e a SC de origem.",
  tableMeta: (columns: number, rows: number) =>
    `${columns} coluna(s) · ${rows.toLocaleString("pt-BR")} linha(s)`,
  cardsMeta: (rows: number) => `${rows.toLocaleString("pt-BR")} linha(s)`,
  openPcLinkTitle: (number: string) => `Abrir pedido de compra ${number}`,
  branchLabel: "Unidade",
  orderNumberLabel: "Número PC",
  productLabel: "Produto",
  supplierLabel: "Fornecedor",
  deliveryFromLabel: "De",
  deliveryToLabel: "Até",
  periodLabel: "Período de entrega",
  sortByLabel: "Ordenar por",
  sortAscLabel: "Crescente",
  sortDescLabel: "Decrescente",
  sortDirectionAriaLabel: "Direção da ordenação",
  attentionLabel: "Atenção",
  attentionAriaLabel: "Recorte por atraso na entrega prometida",
  attentionAll: "Todos",
  attentionLate: "Atrasados",
  attentionAllWithCount: (n: number) => `Todos (${n.toLocaleString("pt-BR")})`,
  attentionLateWithCount: (n: number) => `Atrasados (${n.toLocaleString("pt-BR")})`,
  heroOpenLines: "Linhas em aberto",
  heroOpenValue: "Valor em aberto",
  heroLate: "Atrasadas",
  refreshAction: "Atualizar",
  updatedAtLabel: (time: string) => `Atualizado às ${time}`,
  clearFilters: "Limpar",
  loading: "Carregando pedidos…",
  emptyTitle: "Nenhum pedido aberto neste recorte",
  emptyMessage: "Ajuste filtros ou unidades. Pedidos encerrados ou residual não aparecem nesta lista.",
  noUnitsTitle: "Nenhuma filial liberada",
  noUnitsMessage:
    "Seu acesso não inclui unidades neste módulo. Peça o escopo canônico ao administrador.",
  error: "Não foi possível carregar os pedidos de compra.",
  forbiddenUnit:
    "Você não tem permissão para esta filial neste módulo. Escolha outra unidade liberada ou peça o acesso canônico ao administrador.",
  retry: "Tentar novamente",
  colPc: "PC",
  colItem: "Item",
  colProduct: "Produto",
  colSupplier: "Fornecedor",
  colOpenQty: "Saldo",
  colDelivery: "Prometida",
  colStatus: "Situação",
  colOpenValue: "Valor aberto",
  pageLabel: "Página",
  prevPage: "Anterior",
  nextPage: "Próxima",
  totalLabel: (total: number) => `${total} linha(s)`,
  detailTitle: "Pedido de compra",
  detailEyebrow: "Ficha do pedido",
  detailDescription:
    "Itens em aberto, datas prometidas, recebimentos e SC de origem de cada item.",
  detailBack: "Pedidos de compra",
  detailLoading: "Carregando o pedido…",
  detailError: "Não foi possível carregar este pedido de compra.",
  detailNotFound:
    "Pedido não encontrado ou fora do universo em aberto. Encerrados e residual não aparecem nesta ficha.",
  detailForbidden:
    "Você não tem permissão para esta filial neste módulo. Peça o acesso canônico ao administrador.",
  itemsTitle: "Itens",
  itemsHint: "Fornecedor, datas e quantidades são por item. Um pedido pode ter mais de um fornecedor.",
  itemsEmpty: "Este pedido não retornou itens visíveis.",
  receiptsTitle: "Recebimentos",
  receiptsEmpty: "Nenhum recebimento registrado neste item.",
  sourceRequestLabel: "SC origem",
  buyerLabel: "Comprador",
  issueDateLabel: "Emissão",
  orderedQtyLabel: "Pedido",
  deliveredQtyLabel: "Entregue",
  unitPriceLabel: "Preço unit.",
  invoiceLabel: "NF",
  invoiceDateLabel: "Emissão NF",
  entryDateLabel: "Entrada",
  receiptQtyLabel: "Qtd.",
  receiptValueLabel: "Valor",
  viewTable: "Tabela",
  viewCards: "Cards",
  viewAriaLabel: "Modo de visualização",
  excelLabel: "Excel",
  excelExporting: "Exportando…",
  excelError: "Não foi possível exportar o recorte para Excel.",
  cardsAriaLabel: "Cards de pedidos em aberto",
  cardOpenQty: "Saldo",
  cardDelivery: "Prometida",
  cardStatus: "Situação",
  cardValue: "Valor aberto",
  tableScrollRegion: "Tabela de pedidos — deslize horizontalmente para ver todas as colunas",
  receiptsTableScrollRegion:
    "Tabela de recebimentos — deslize horizontalmente para ver todas as colunas",
} as const;

export function mapPurchaseOrdersFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return PURCHASE_ORDERS_CONTENT.forbiddenUnit;
  }
  return message || PURCHASE_ORDERS_CONTENT.error;
}

export type PurchaseOrderDetailErrorKind = "forbidden" | "not_found" | "error";

export function classifyPurchaseOrderDetailError(
  message: string,
): { kind: PurchaseOrderDetailErrorKind; text: string } {
  if (/403|forbidden/i.test(message)) {
    return { kind: "forbidden", text: PURCHASE_ORDERS_CONTENT.detailForbidden };
  }
  if (/404|not found|not_found|não encontrado/i.test(message)) {
    return { kind: "not_found", text: PURCHASE_ORDERS_CONTENT.detailNotFound };
  }
  return { kind: "error", text: message || PURCHASE_ORDERS_CONTENT.detailError };
}
