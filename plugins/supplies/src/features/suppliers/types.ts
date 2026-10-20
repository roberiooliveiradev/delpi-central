export type SupplierListItem = {
  supplier_id: string;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string | null;
  supplier_short_name: string | null;
  state: string | null;
  blocked: boolean;
  tax_id: string | null;
  tax_id_masked: boolean;
};

export type SupplierDetailSection = Record<string, string | number | null>;

export type SupplierDetail = {
  supplier_id: string;
  supplier_code: string;
  supplier_store: string;
  blocked: boolean;
  tax_id: string | null;
  tax_id_masked: boolean;
  sections: {
    identification?: SupplierDetailSection;
    address?: SupplierDetailSection;
    contact?: SupplierDetailSection;
    fiscal?: SupplierDetailSection;
    purchasing?: SupplierDetailSection;
  };
};

export type SuppliersQuery = {
  query: string;
  state: string;
  blocked: string;
  page: number;
  page_size: number;
};

export type SupplierListEnvelope = {
  items?: SupplierListItem[];
  page?: number;
  page_size?: number;
  total?: number;
  total_pages?: number;
};

/** Resultado de escrita — nunca equivale HTTP 200 a persistência confirmada. */
export type SupplierWriteOutcome =
  | "rejected"
  | "acknowledged"
  | "persistence_confirmed"
  | "indeterminate"
  | "write_disabled";

export type SupplierWriteResponse = {
  acknowledged?: boolean;
  persistence_proven?: boolean;
  data?: Record<string, unknown>;
  outcome?: SupplierWriteOutcome;
  code?: string;
};

export type SupplierEditDraft = {
  supplier_name: string;
  supplier_short_name: string;
};

export type SupplierCreateDraft = {
  supplier_name: string;
  supplier_short_name: string;
  tax_id: string;
  state: string;
};

export const SUPPLIERS_PAGE_SIZE_OPTIONS = [20, 50, 100] as const;
export const SUPPLIERS_EDITABLE_FIELDS = {
  supplier_name: 50,
  supplier_short_name: 20,
} as const;
