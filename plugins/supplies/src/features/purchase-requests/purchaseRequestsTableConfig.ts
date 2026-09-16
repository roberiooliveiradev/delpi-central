import { PURCHASE_REQUESTS_CONTENT as C } from "./content";

export type PurchaseRequestTableColumnKey =
  | "request_number"
  | "request_item"
  | "product"
  | "requester"
  | "cost_center"
  | "opened"
  | "stage";

export type PurchaseRequestTableColumnDef = {
  key: PurchaseRequestTableColumnKey;
  label: string;
};

export const PURCHASE_REQUESTS_COLUMN_STORAGE_KEY =
  "supplies:purchase-requests:column-prefs:v1";

export const PURCHASE_REQUESTS_TABLE_FONT_SIZE_STORAGE_KEY =
  "supplies:purchase-requests:table-font-size:v1";

export const PURCHASE_REQUESTS_TABLE_COLUMNS: readonly PurchaseRequestTableColumnDef[] = [
  { key: "request_number", label: C.colSc },
  { key: "request_item", label: C.colItem },
  { key: "product", label: C.colProduct },
  { key: "requester", label: C.colRequester },
  { key: "cost_center", label: C.colCc },
  { key: "opened", label: C.colOpened },
  { key: "stage", label: C.colStage },
];

export const PURCHASE_REQUESTS_TABLE_EMPTY_FALLBACK_KEYS: readonly PurchaseRequestTableColumnKey[] =
  ["request_number", "product"];
