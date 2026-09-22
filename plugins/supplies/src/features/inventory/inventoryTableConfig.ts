import { INVENTORY_CONTENT as C } from "./content";

export type InventoryTableColumnKey =
  | "product_code"
  | "description"
  | "unit_of_measure"
  | "branch"
  | "warehouse"
  | "quantity"
  | "unit_cost"
  | "stock_value";

export type InventoryTableColumnDef = {
  key: InventoryTableColumnKey;
  label: string;
};

export const INVENTORY_COLUMN_STORAGE_KEY = "supplies:inventory:column-prefs:v1";

export const INVENTORY_TABLE_FONT_SIZE_STORAGE_KEY =
  "supplies:inventory:table-font-size:v1";

export const INVENTORY_TABLE_COLUMNS: readonly InventoryTableColumnDef[] = [
  { key: "product_code", label: C.colProduct },
  { key: "description", label: C.colDescription },
  { key: "unit_of_measure", label: C.colUm },
  { key: "branch", label: C.colUnit },
  { key: "warehouse", label: C.colWarehouse },
  { key: "quantity", label: C.colQuantity },
  { key: "unit_cost", label: C.colUnitCost },
  { key: "stock_value", label: C.colStockValue },
];

export const INVENTORY_TABLE_EMPTY_FALLBACK_KEYS: readonly InventoryTableColumnKey[] =
  ["product_code", "warehouse", "quantity", "stock_value"];
