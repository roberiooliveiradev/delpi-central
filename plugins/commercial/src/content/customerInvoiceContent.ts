/**
 * Copy PT da página de detalhe de NF de saída (Conta / Histórico).
 */
export const CUSTOMER_INVOICE_DETAIL_CONTENT = {
  backToHistory: "Histórico",
  historyCrumb: "Histórico",
  noteLabel: "NF",
  refresh: "Atualizar",
  loading: "Carregando nota fiscal…",
  loadError: "Não foi possível carregar a nota fiscal.",
  notFound: "Nota fiscal não encontrada para esta conta.",
  headerSection: "Dados da nota",
  itemsSection: "Itens",
  emptyItems: "Sem itens nesta nota.",
  fields: {
    issueDate: "Emissão",
    accessKey: "Chave NFe",
    carrier: "Transportadora",
    salesOrder: "Pedido de venda",
    customerOrder: "Pedido do cliente",
    customer: "Cliente",
    totalValue: "Valor",
  },
} as const;
