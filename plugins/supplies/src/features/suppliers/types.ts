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
  supplier_store: string;
  person_type: string;
  tax_id: string;
  supplier_name: string;
  supplier_short_name: string;
  address: string;
  district: string;
  postal_code: string;
  state: string;
  city: string;
  city_code: string;
  area_code: string;
  phone: string;
  contact_name: string;
  email: string;
  state_registration: string;
  municipal_registration: string;
  country_code: string;
  bacen_country_code: string;
  rohs_indicator: string;
  payment_condition_code: string;
  payment_method_code: string;
  accounting_account: string;
  financial_nature_code: string;
};

/** Specs derivadas da matriz REST→SA2 (SX3): input constraints only — a
 * validação autoritativa continua no backend. */
export type SupplierCreateFieldSpec = {
  key: keyof SupplierCreateDraft;
  maxLength: number;
  digitsOnly?: boolean;
  uppercase?: boolean;
  required?: boolean;
  options?: { value: string; label: string }[];
};

export const SUPPLIER_CREATE_SECTIONS: ReadonlyArray<{
  id: "identification" | "address" | "contact" | "fiscal" | "purchasing";
  fields: ReadonlyArray<SupplierCreateFieldSpec>;
}> = [
  {
    id: "identification",
    fields: [
      { key: "supplier_store", maxLength: 2, digitsOnly: true, required: true },
      {
        key: "person_type",
        maxLength: 1,
        options: [
          { value: "J", label: "Jurídica (CNPJ)" },
          { value: "F", label: "Física (CPF)" },
          { value: "X", label: "Outros" },
        ],
      },
      { key: "tax_id", maxLength: 14, digitsOnly: true },
      { key: "supplier_name", maxLength: 50 },
      { key: "supplier_short_name", maxLength: 20 },
    ],
  },
  {
    id: "address",
    fields: [
      { key: "address", maxLength: 40 },
      { key: "district", maxLength: 20 },
      { key: "postal_code", maxLength: 8, digitsOnly: true },
      { key: "state", maxLength: 2, uppercase: true },
      { key: "city", maxLength: 25 },
      { key: "city_code", maxLength: 5, digitsOnly: true },
    ],
  },
  {
    id: "contact",
    fields: [
      { key: "area_code", maxLength: 3, digitsOnly: true },
      { key: "phone", maxLength: 50 },
      { key: "contact_name", maxLength: 15 },
      { key: "email", maxLength: 50 },
    ],
  },
  {
    id: "fiscal",
    fields: [
      { key: "state_registration", maxLength: 18 },
      { key: "municipal_registration", maxLength: 18 },
      { key: "country_code", maxLength: 3 },
      { key: "bacen_country_code", maxLength: 5, digitsOnly: true },
      {
        key: "rohs_indicator",
        maxLength: 1,
        options: [
          { value: "N", label: "Não" },
          { value: "S", label: "Sim" },
        ],
      },
    ],
  },
  {
    id: "purchasing",
    fields: [
      { key: "payment_condition_code", maxLength: 3 },
      { key: "payment_method_code", maxLength: 2 },
      { key: "accounting_account", maxLength: 20 },
      { key: "financial_nature_code", maxLength: 10 },
    ],
  },
];

export const SUPPLIERS_PAGE_SIZE_OPTIONS = [20, 50, 100] as const;
export const SUPPLIERS_EDITABLE_FIELDS = {
  supplier_name: 50,
  supplier_short_name: 20,
} as const;
