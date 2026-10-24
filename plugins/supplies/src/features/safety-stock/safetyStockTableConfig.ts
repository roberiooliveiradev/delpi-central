import { SAFETY_STOCK_CONTENT as C } from "./content";
import type { SafetyStockSortField } from "./types";

export type SafetyStockTableColumnKey =
  | "product_code"
  | "product_description"
  | "branch"
  | "product_type"
  | "product_group"
  | "unit"
  | "safety_stock"
  | "primary_stock"
  | "work_in_process_stock"
  | "deficit_quantity"
  | "status";

export type SafetyStockTableColumnDef = {
  key: SafetyStockTableColumnKey;
  label: string;
};

export const SAFETY_STOCK_COLUMN_STORAGE_KEY =
  "supplies:safety-stock:column-prefs:v1";

export const SAFETY_STOCK_TABLE_FONT_SIZE_STORAGE_KEY =
  "supplies:safety-stock:table-font-size:v1";

export const SAFETY_STOCK_TABLE_COLUMNS: readonly SafetyStockTableColumnDef[] = [
  { key: "product_code", label: C.colProduct },
  { key: "product_description", label: C.colDescription },
  { key: "branch", label: C.colBranch },
  { key: "product_type", label: C.colType },
  { key: "product_group", label: C.colGroup },
  { key: "unit", label: C.colUm },
  { key: "safety_stock", label: C.colSafetyStock },
  { key: "primary_stock", label: C.colPrimaryStock },
  { key: "work_in_process_stock", label: C.colWorkInProcessStock },
  { key: "deficit_quantity", label: C.colDeficit },
  { key: "status", label: C.colStatus },
];

export const SAFETY_STOCK_TABLE_EMPTY_FALLBACK_KEYS: readonly SafetyStockTableColumnKey[] =
  ["product_code", "product_description", "safety_stock", "deficit_quantity", "status"];

/** Colunas cuja ordenação é real no servidor (allowlist BFF). */
export const SAFETY_STOCK_SORTABLE_COLUMNS = new Set<SafetyStockTableColumnKey>([
  "product_code",
  "product_description",
  "product_group",
  "unit",
  "safety_stock",
  "primary_stock",
  "work_in_process_stock",
  "deficit_quantity",
  "status",
]);

/** Identidade da linha para o futuro detalhe E11.S3: produto + filial. */
export function safetyStockRowKey(
  productCode: string | null | undefined,
  branch: string | null | undefined,
  index: number,
): string {
  return `${branch ?? ""}|${productCode ?? ""}|${index}`;
}

export function columnSortField(
  key: SafetyStockTableColumnKey,
): SafetyStockSortField | null {
  return SAFETY_STOCK_SORTABLE_COLUMNS.has(key) ? (key as SafetyStockSortField) : null;
}
