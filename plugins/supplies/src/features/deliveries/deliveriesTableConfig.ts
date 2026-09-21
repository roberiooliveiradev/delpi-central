import { DELIVERIES_CONTENT as C } from "./content";

export type DeliveryTableColumnKey =
  | "branch"
  | "order_number"
  | "order_item"
  | "supplier"
  | "product"
  | "quantity"
  | "expected_delivery_date"
  | "receipt_entry_date"
  | "days_diff"
  | "status";

export type DeliveryTableColumnDef = {
  key: DeliveryTableColumnKey;
  label: string;
};

export const DELIVERIES_COLUMN_STORAGE_KEY = "supplies:deliveries:column-prefs:v1";

export const DELIVERIES_TABLE_FONT_SIZE_STORAGE_KEY =
  "supplies:deliveries:table-font-size:v1";

export const DELIVERIES_TABLE_COLUMNS: readonly DeliveryTableColumnDef[] = [
  { key: "branch", label: C.colUnit },
  { key: "order_number", label: C.colPc },
  { key: "order_item", label: C.colItem },
  { key: "supplier", label: C.colSupplier },
  { key: "product", label: C.colProduct },
  { key: "quantity", label: C.colQty },
  { key: "expected_delivery_date", label: C.colPromised },
  { key: "receipt_entry_date", label: C.colEntry },
  { key: "days_diff", label: C.colDays },
  { key: "status", label: C.colStatus },
];

export const DELIVERIES_TABLE_EMPTY_FALLBACK_KEYS: readonly DeliveryTableColumnKey[] =
  ["order_number", "product", "status"];
