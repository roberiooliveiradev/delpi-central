import { CM_HELP } from "../content/helpTooltips";

/** Colunas da lista Minha Carteira. */
export const CUSTOMERS_LIST_COLUMN_HELP: Record<string, string> = {
  nome: CM_HELP.customers.columns.nome,
  sellerName: CM_HELP.customers.columns.sellerName,
  city: CM_HELP.customers.columns.city,
  lastPurchaseDate: CM_HELP.customers.columns.lastPurchaseDate,
  billed12m: CM_HELP.customers.columns.billed12m,
  billingTrend: CM_HELP.customers.trend,
  status: CM_HELP.customers.columns.status,
  valorTotalAberto: CM_HELP.customers.columns.valorTotalAberto,
  quantidadePedidosAtrasados: CM_HELP.customers.columns.quantidadePedidosAtrasados,
  proximaEntrega: CM_HELP.customers.columns.proximaEntrega,
};

export const CUSTOMER_ORDERS_COLUMN_HELP: Record<string, string> = {
  branch: CM_HELP.customerDetail.ordersColumns.branch,
  order: CM_HELP.customerDetail.ordersColumns.order,
  "customer-order": CM_HELP.customerDetail.ordersColumns.customerOrder,
  status: CM_HELP.customerDetail.ordersColumns.status,
  lines: CM_HELP.customerDetail.ordersColumns.lines,
  overdue: CM_HELP.customerDetail.ordersColumns.overdue,
  delivery: CM_HELP.customerDetail.ordersColumns.delivery,
  value: CM_HELP.customerDetail.ordersColumns.value,
};

export const CUSTOMER_ORDER_LINES_COLUMN_HELP: Record<string, string> = {
  product: CM_HELP.customerDetail.orderLinesColumns.product,
  ordered: CM_HELP.customerDetail.orderLinesColumns.ordered,
  delivered: CM_HELP.customerDetail.orderLinesColumns.delivered,
  balance: CM_HELP.customerDetail.orderLinesColumns.balance,
  delivery: CM_HELP.customerDetail.orderLinesColumns.delivery,
  "open-value": CM_HELP.customerDetail.orderLinesColumns.openValue,
  delay: CM_HELP.customerDetail.orderLinesColumns.delay,
};

export const CUSTOMER_INVOICE_COLUMN_HELP: Record<string, string> = {
  issue: CM_HELP.customerDetail.invoiceColumns.issue,
  invoice: CM_HELP.customerDetail.invoiceColumns.invoice,
  "sales-order": CM_HELP.customerDetail.invoiceColumns.salesOrder,
  "customer-order": CM_HELP.customerDetail.invoiceColumns.customerOrder,
  situation: CM_HELP.customerDetail.invoiceColumns.situation,
  items: CM_HELP.customerDetail.invoiceColumns.items,
  value: CM_HELP.customerDetail.invoiceColumns.value,
};

export const CUSTOMER_INVOICE_ITEM_COLUMN_HELP: Record<string, string> = {
  item: CM_HELP.customerDetail.invoiceItemColumns.item,
  product: CM_HELP.customerDetail.invoiceItemColumns.product,
  description: CM_HELP.customerDetail.invoiceItemColumns.description,
  quantity: CM_HELP.customerDetail.invoiceItemColumns.quantity,
  unit: CM_HELP.customerDetail.invoiceItemColumns.unit,
  "unit-price": CM_HELP.customerDetail.invoiceItemColumns.unitPrice,
  total: CM_HELP.customerDetail.invoiceItemColumns.total,
  order: CM_HELP.customerDetail.invoiceItemColumns.order,
};

export const CUSTOMER_ORDERS_PREVIEW_COLUMN_HELP: Record<string, string> = {
  order: CM_HELP.customerDetail.ordersColumns.order,
  issue: CM_HELP.customerDetail.invoiceColumns.issue,
  forecast: CM_HELP.customerDetail.ordersColumns.delivery,
  value: CM_HELP.customerDetail.ordersColumns.value,
  status: CM_HELP.customerDetail.ordersColumns.status,
  opportunity: CM_HELP.customerDetail.opportunities,
};

export const ADMIN_TEAM_COLUMN_HELP: Record<string, string> = {
  person: CM_HELP.administration.teamColPerson,
  online: CM_HELP.administration.teamColOnline,
  groups: CM_HELP.administration.teamColGroups,
  portfolios: CM_HELP.administration.teamColPortfolios,
};

export const ANALYTICS_OTD_COLUMN_HELP: Record<string, string> = {
  branch: CM_HELP.analytics.columns.branch,
  order: CM_HELP.analytics.columns.order,
  customer: CM_HELP.analytics.columns.customer,
  product: CM_HELP.analytics.columns.product,
  productDesc: CM_HELP.analytics.columns.productDesc,
  status: CM_HELP.analytics.columns.status,
  promised: CM_HELP.analytics.columns.promised,
  invoice: CM_HELP.analytics.columns.invoice,
  daysDiff: CM_HELP.analytics.columns.daysDiff,
  qty: CM_HELP.analytics.columns.qty,
  periodo: CM_HELP.analytics.columns.periodo,
};

export const ANALYTICS_OPP_DETAIL_COLUMN_HELP: Record<string, string> = {
  code: CM_HELP.analytics.oppDetailColumns.code,
  desc: CM_HELP.analytics.oppDetailColumns.desc,
  group: CM_HELP.analytics.oppDetailColumns.group,
  type: CM_HELP.analytics.oppDetailColumns.type,
  qty: CM_HELP.analytics.oppDetailColumns.qty,
  rev: CM_HELP.analytics.oppDetailColumns.rev,
  process: CM_HELP.analytics.oppDetailColumns.process,
  stage: CM_HELP.analytics.oppDetailColumns.stage,
  start: CM_HELP.analytics.oppDetailColumns.start,
  end: CM_HELP.analytics.oppDetailColumns.end,
  dur: CM_HELP.analytics.oppDetailColumns.dur,
  status: CM_HELP.analytics.oppDetailColumns.status,
};

export const ANALYTICS_TEAM_COLUMN_HELP: Record<string, string> = {
  name: CM_HELP.analytics.teamColumns.name,
  customers: CM_HELP.analytics.teamColumns.customers,
  lines: CM_HELP.analytics.teamColumns.lines,
  openValue: CM_HELP.analytics.teamColumns.openValue,
};

export const PROPOSALS_DOCUMENTS_COLUMN_HELP: Record<string, string> = {
  ov: CM_HELP.proposals.columns.ov,
};

export const PROPOSAL_DETAIL_ITEMS_COLUMN_HELP: Record<string, string> = {
  item: CM_HELP.proposals.columns.item,
  produto: CM_HELP.proposals.columns.produto,
  desc: CM_HELP.proposals.columns.desc,
  qty: CM_HELP.proposals.columns.qty,
  total: CM_HELP.proposals.columns.total,
  prazo: CM_HELP.proposals.columns.prazo,
};

export const PORTFOLIO_BY_PRODUCT_COLUMN_HELP: Record<string, string> = {
  label: CM_HELP.customers.byProductColumns.label,
  domestic: CM_HELP.customers.byProductColumns.domestic,
  export: CM_HELP.customers.byProductColumns.export,
  total: CM_HELP.customers.byProductColumns.total,
  share: CM_HELP.customers.byProductColumns.share,
};

export const PORTFOLIO_ABC_COLUMN_HELP: Record<string, string> = {
  customer: CM_HELP.customers.abcColumns.customer,
  cnpj: CM_HELP.customers.abcColumns.cnpj,
  city: CM_HELP.customers.abcColumns.city,
  share: CM_HELP.customers.abcColumns.share,
};

export const PORTFOLIO_RANKING_COLUMN_HELP: Record<string, string> = {
  rank: CM_HELP.customers.rankingColumns.rank,
  customer: CM_HELP.customers.rankingColumns.customer,
  seller: CM_HELP.customers.rankingColumns.seller,
  trend: CM_HELP.customers.rankingColumns.trend,
  current: CM_HELP.customers.rankingColumns.current,
  prior: CM_HELP.customers.rankingColumns.prior,
  deltaPct: CM_HELP.customers.rankingColumns.deltaPct,
};

export function withColumnHelp<T extends { key: string; headerHint?: string }>(
  columns: T[],
  helpByKey: Record<string, string>,
): T[] {
  return columns.map((column) => {
    const hint = helpByKey[column.key];
    if (!hint || column.headerHint) return column;
    return { ...column, headerHint: hint };
  });
}
