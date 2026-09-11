export const PURCHASE_ORDERS_CONTENT = {
  title: "Pedidos de compra",
  eyebrow: "Portal Suprimentos",
  description:
    "Linhas de pedidos em aberto no TOTVS (saldo a receber). O detalhe completo entra na próxima etapa do portal.",
  helpAriaLabel: "Ajuda sobre pedidos de compra",
  filtersAriaLabel: "Filtros de pedidos de compra",
  listTitle: "Pedidos em aberto",
  listHint:
    "Saldo C7_QUANT > C7_QUJE, sem residual. Clique na linha para marcar o pedido na URL; o detalhe completo virá na próxima entrega.",
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
  detailTitle: "Pedido selecionado",
  detailHint: "Resumo da linha selecionada. O detalhe completo (itens, recebimentos, SC origem) entra na etapa seguinte.",
  detailClose: "Fechar",
  detailComingSoon: "Detalhe completo em breve",
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
} as const;

export function mapPurchaseOrdersFetchError(message: string): string {
  if (/403|forbidden/i.test(message)) {
    return PURCHASE_ORDERS_CONTENT.forbiddenUnit;
  }
  return message || PURCHASE_ORDERS_CONTENT.error;
}
