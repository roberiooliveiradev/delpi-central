import type {
  LinkedPurchaseOrderSnapshot,
  NfeMappedItem,
  NfeProductMappingView,
  OpenPurchaseOrderGroup,
  OpenPurchaseOrderItem,
} from "../../domain/types";

export type InvoiceProductSummaryLine = {
  code: string;
  reference: string;
  quantity: string;
  unit: string;
};

export function invoiceProductSummary(view: NfeProductMappingView): InvoiceProductSummaryLine[] {
  if (view.status !== "ready") return [];
  return (view.detail.items ?? []).map((item) => invoiceProductLine(item));
}

function invoiceProductLine(item: NfeMappedItem): InvoiceProductSummaryLine {
  const code =
    item.mappingStatus === "mapped" ? String(item.internalProductCode ?? "").trim() : "";
  return {
    code: code || "—",
    reference: String(item.supplierProductCode ?? "").trim() || "—",
    quantity: String(item.quantity ?? "").trim() || "—",
    unit: String(item.unit ?? "").trim(),
  };
}

export function productCodeMatchKey(value: string | null | undefined): string {
  const trimmed = String(value ?? "").trim().toUpperCase();
  if (!trimmed) return "";
  const withoutLeadingZeros = trimmed.replace(/^0+/, "");
  return withoutLeadingZeros || trimmed;
}

/** Códigos Delpi só quando cada item da NF-e tem relação única. Caso contrário, não filtra. */
export function delpiProductCodesWhenFullyMapped(view: NfeProductMappingView): string[] | null {
  if (view.status !== "ready") return null;
  const items = view.detail.items ?? [];
  if (items.length === 0) return null;
  const codes: string[] = [];
  const seen = new Set<string>();
  for (const item of items) {
    const code = String(item.internalProductCode ?? "").trim();
    if (item.mappingStatus !== "mapped" || !code) return null;
    const key = productCodeMatchKey(code);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    codes.push(code);
  }
  return codes.length > 0 ? codes : null;
}

function isSameLinkedGroup(
  group: OpenPurchaseOrderGroup,
  linked: Pick<LinkedPurchaseOrderSnapshot, "order_number" | "delivery_date">,
): boolean {
  return (
    group.order_number === linked.order_number &&
    (group.delivery_date ?? null) === (linked.delivery_date ?? null)
  );
}

function itemStaysVisible(
  group: OpenPurchaseOrderGroup,
  item: OpenPurchaseOrderItem,
  productKeys: Set<string>,
  linked: Array<Pick<LinkedPurchaseOrderSnapshot, "order_number" | "delivery_date" | "lines">>,
): boolean {
  if (productKeys.has(productCodeMatchKey(item.product_code))) return true;
  const current = linked.find((entry) => isSameLinkedGroup(group, entry));
  if (!current) return false;
  const lines = current.lines ?? [];
  if (lines.length === 0) return true;
  return lines.some((line) => line.order_item && line.order_item === item.order_item);
}

export function filterPurchaseOrderGroupsByProductCodes(
  groups: OpenPurchaseOrderGroup[],
  productCodes: string[],
  linked: Array<Pick<LinkedPurchaseOrderSnapshot, "order_number" | "delivery_date" | "lines">> = [],
): OpenPurchaseOrderGroup[] {
  const productKeys = new Set(productCodes.map((code) => productCodeMatchKey(code)).filter(Boolean));
  if (productKeys.size === 0) return groups;
  const filtered: OpenPurchaseOrderGroup[] = [];
  for (const group of groups) {
    const items = group.items.filter((item) => itemStaysVisible(group, item, productKeys, linked));
    if (items.length === 0) continue;
    const distinct = new Set(
      items.map((item) => productCodeMatchKey(item.product_code)).filter(Boolean),
    );
    filtered.push({
      ...group,
      items,
      item_count: items.length,
      product_count: distinct.size,
      open_value: items.reduce((sum, item) => sum + Number(item.open_value || 0), 0),
    });
  }
  return filtered;
}
