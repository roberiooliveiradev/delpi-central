import type { ChecklistFlags, FreightMode, InvoiceType, IssuanceItem, Party } from "./types";

export function buildReviewChecklist(input: {
  party: Party | null;
  items: IssuanceItem[];
  invoiceType: InvoiceType;
  invoiceTypeOther: string;
  freightMode: FreightMode;
  weightKg: string;
  volumeCount: string;
}): ChecklistFlags {
  const items = input.items;
  const weight = Number(input.weightKg);
  const volumes = Number(input.volumeCount);
  return {
    recipient: Boolean(input.party?.party_code && input.party?.party_store),
    item_codes: items.length > 0 && items.every((item) => Boolean(item.product_code)),
    quantity_price:
      items.length > 0 &&
      items.every((item) => Number(item.quantity) > 0 && Number(item.unit_price) >= 0),
    stock_write_off: items.length > 0,
    invoice_type:
      input.invoiceType !== "other" || input.invoiceTypeOther.trim().length > 0,
    freight_mode: input.freightMode === "cif" || input.freightMode === "fob",
    weight_volumes: weight > 0 && volumes > 0,
  };
}
