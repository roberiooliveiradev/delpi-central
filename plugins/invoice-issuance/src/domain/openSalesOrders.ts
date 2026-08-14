import type { IssuanceItem, OpenSalesOrderLine } from "./types";

export function salesOrderLineKey(
  line: Pick<OpenSalesOrderLine, "sales_order" | "sales_order_item">,
): string {
  return `${line.sales_order}|${line.sales_order_item}`;
}

export function clampOpenQuantity(quantity: number, quantityOpen: number): number {
  if (!Number.isFinite(quantity) || quantity <= 0) return 0;
  const cap = Number.isFinite(quantityOpen) ? Math.max(0, quantityOpen) : 0;
  return Math.min(quantity, cap);
}

export function toIssuanceItemFromOpenLine(
  line: OpenSalesOrderLine,
  quantity: number,
  stockWriteOff = true,
): IssuanceItem & { quantity_open: number } {
  return {
    product_code: line.product_code,
    product_description: line.product_description,
    quantity: clampOpenQuantity(quantity, line.quantity_open),
    unit_price: line.unit_price,
    stock_write_off: stockWriteOff,
    sales_order: line.sales_order,
    sales_order_item: line.sales_order_item,
    customer_order_number: line.customer_order_number,
    quantity_open: line.quantity_open,
  };
}

export function mergeIssuanceItems(
  current: IssuanceItem[],
  incoming: IssuanceItem[],
): IssuanceItem[] {
  const next = [...current];
  for (const item of incoming) {
    if (!item.quantity || item.quantity <= 0) continue;
    const idx = next.findIndex(
      (row) =>
        Boolean(row.sales_order) &&
        row.sales_order === item.sales_order &&
        row.sales_order_item === item.sales_order_item,
    );
    if (idx >= 0) {
      next[idx] = { ...next[idx], ...item };
    } else {
      next.push(item);
    }
  }
  return next;
}
