/** DTO tipado — POST /suppliers/creation-preview (X4.UX-R1.S1/S2). */

export type DuplicateCheckStatus =
  | "CLEAR"
  | "POSSIBLE_MATCH"
  | "INCONCLUSIVE";

export type CreationSuggestionSource = {
  provider_id: string;
  retrieved_at: string;
};

export type CreationSuggestion = {
  field_key: string;
  suggested_value: string;
  source: CreationSuggestionSource;
  applicable: boolean;
};

export type CreationDuplicateMatch = {
  supplier_code: string | null;
  supplier_store: string | null;
  supplier_name: string | null;
  state: string | null;
  blocked: boolean | null;
};

export type CreationDuplicateCheck = {
  status: DuplicateCheckStatus;
  matches: CreationDuplicateMatch[];
  total?: number | null;
};

export type SupplierCreationPreview = {
  tax_id_masked: string;
  person_type: string;
  duplicate_check: CreationDuplicateCheck;
  suggestions: CreationSuggestion[];
  unavailable_fields: string[];
  write_enabled: boolean;
};

/** Modos de início do cadastro assistido (RQ-01). */
export type CreationMode = "cnpj" | "name" | "manual";

/** Estados de UX da sugestão — não são enum de backend nem persistidos. */
export type SuggestionStatus =
  | "SUGGESTED"
  | "CONFIRMED"
  | "MANUALLY_CHANGED"
  | "UNAVAILABLE";

export type SuggestionEntry = {
  field_key: string;
  suggested_value: string | null;
  source: CreationSuggestionSource | null;
  applicable: boolean;
  status: SuggestionStatus;
};

export type SuggestionEntryMap = Record<string, SuggestionEntry>;

/** Resposta paginada — GET /suppliers/existing-suppliers (X4.UX-R1.S8). */
export type ExistingSuppliersPage = {
  items: CreationDuplicateMatch[];
  page: number;
  page_size: number;
  total: number;
};
