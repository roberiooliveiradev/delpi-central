import type { PaginationParams } from "./pagination";

export type NonconformityType = "internal" | "external" | "all";

export type ListNonconformitiesParams = PaginationParams & {
  type?: NonconformityType;
  branch?: string;
  date_start?: string;
  date_end?: string;
  status?: string;
  item_code?: string;
  description?: string;
};

export type Nonconformity = {
  branch: string;
  code: string;
  revision: string;
  type_code: string;
  type_label: string | null;
  status_code: string | null;
  status_label: string | null;
  description: string | null;
  item_code: string | null;
  op_code: string | null;
  registered_date: string | null;
  occurrence_date: string | null;
  priority_code: string | null;
  priority_label: string | null;
  origin_department: string | null;
  destination_department: string | null;
  customer_code: string | null;
  customer_store: string | null;
  supplier_code: string | null;
  supplier_store: string | null;
  produced_quantity: number | null;
  returned_quantity: number | null;
};
