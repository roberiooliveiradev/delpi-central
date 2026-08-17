import type { InvoiceType, IssuanceItem } from "./types";

/** Venda e devolução saem de estoque; amostra/conserto/outros nascem sem baixa. */
export const INVOICE_TYPES_DEFAULT_STOCK_WRITE_OFF: ReadonlySet<InvoiceType> = new Set([
  "sale",
  "return",
]);

export function defaultStockWriteOff(invoiceType: InvoiceType | string): boolean {
  return INVOICE_TYPES_DEFAULT_STOCK_WRITE_OFF.has(invoiceType as InvoiceType);
}

export function applyDefaultStockWriteOff<
  T extends Pick<IssuanceItem, "stock_write_off"> & { stockHint?: string },
>(items: T[], invoiceType: InvoiceType | string): T[] {
  const writeOff = defaultStockWriteOff(invoiceType);
  return items.map((item) =>
    item.stock_write_off === writeOff
      ? item
      : { ...item, stock_write_off: writeOff, stockHint: undefined },
  );
}
