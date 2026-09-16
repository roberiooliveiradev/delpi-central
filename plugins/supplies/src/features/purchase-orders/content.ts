export const PURCHASE_ORDERS_CONTENT = {
  title: "Pedidos de compra",
  eyebrow: "Portal Suprimentos",
  description:
    "Linhas de pedidos em aberto (saldo a receber). Clique na linha para abrir a ficha do pedido.",
  helpAriaLabel: "Ajuda sobre pedidos de compra",
  filtersAriaLabel: "Filtros de pedidos de compra",
  listTitle: "Pedidos em aberto",
  listHint:
    "Somente pedidos com saldo a receber. Clique na linha para abrir itens, entregas prometidas, recebimentos e a SC de origem.",
  branchLabel: "Filial",
  orderNumberLabel: "Número PC",
  productLabel: "Produto",
  supplierLabel: "Fornecedor",
  deliveryFromLabel: "Entrega de",
  deliveryToLabel: "Entrega até",
  lateOnlyLabel: "Somente atrasados",
  lateOnlyYes: "Sim",
  lateOnlyNo: "Todos",
  applyFilters: "Aplicar filtros",
  clearFilters: "Limpar",
  loading: "Carregando pedidos…",
  emptyTitle: "Nenhum pedido aberto neste recorte",
  emptyMessage: "Ajuste filtros ou filial. Pedidos encerrados ou residual não aparecem nesta lista.",
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
    "Itens em aberto, entrega prometida, recebimentos e a solicitação de origem de cada item.",
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
