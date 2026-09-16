import { PURCHASE_ORDERS_CONTENT as C } from "./content";

export type PurchaseOrderTableColumnKey =
  | "order_number"
  | "order_item"
  | "product"
  | "supplier"
  | "open_quantity"
  | "delivery"
  | "status"
  | "open_value";

export type PurchaseOrderTableColumnDef = {
  key: PurchaseOrderTableColumnKey;
  label: string;
};

export const PURCHASE_ORDERS_COLUMN_STORAGE_KEY =
  "supplies:purchase-orders:column-prefs:v1";

export const PURCHASE_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY =
  "supplies:purchase-orders:table-font-size:v1";

export const PURCHASE_ORDERS_TABLE_COLUMNS: readonly PurchaseOrderTableColumnDef[] = [
  { key: "order_number", label: C.colPc },
  { key: "order_item", label: C.colItem },
  { key: "product", label: C.colProduct },
  { key: "supplier", label: C.colSupplier },
  { key: "open_quantity", label: C.colOpenQty },
  { key: "delivery", label: C.colDelivery },
  { key: "status", label: C.colStatus },
  { key: "open_value", label: C.colOpenValue },
];

export const PURCHASE_ORDERS_TABLE_EMPTY_FALLBACK_KEYS: readonly PurchaseOrderTableColumnKey[] =
  ["order_number", "product"];
