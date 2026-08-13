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
