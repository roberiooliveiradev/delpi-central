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

export type SupplierDetailSectionKey =
  | "identification"
  | "address"
  | "contact"
  | "fiscal"
  | "purchasing";

export type SupplierDetail = {
  supplier_id: string;
  supplier_code: string;
  supplier_store: string;
  blocked: boolean;
  tax_id: string | null;
  tax_id_masked: boolean;
  sections: Partial<Record<SupplierDetailSectionKey, SupplierDetailSection>>;
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

/** Chave de campo cadastral: os campos POST mais o código (system-generated). */
export type SupplierFieldKey = keyof SupplierCreateDraft | "supplier_code";

/** Onde o valor do campo aparece no payload do GET detail da BFF. */
export type SupplierFieldGetSource =
  | "section" // detail.sections[section][key]
  | "top" // top-level projection (tax_id — já mascarado pela BFF)
  | "identity"; // top-level supplier_code / supplier_store

/** Evidência contratual que respalda a capacidade do campo. */
export type SupplierFieldEvidence =
  | "post-matrix" // matriz REST→SA2 (POST documentado)
  | "put-contract" // exemplo PUT do contrato REST (editável comprovado)
  | "identity" // parte da chave supplier_id (A2_COD + A2_LOJA)
  | "system"; // gerado pelo ERP — nunca enviado pelo cliente

/**
 * Registry compartilhado dos campos cadastrais do fornecedor — fonte única
 * usada por criação, consulta e edição. Constraints derivadas da matriz
 * REST→SA2 (SX3); a validação autoritativa continua no backend.
 */
export type SupplierFieldSpec = {
  key: SupplierFieldKey;
  label: string;
  section: SupplierDetailSectionKey;
  maxLength: number;
  digitsOnly?: boolean;
  uppercase?: boolean;
  options?: { value: string; label: string }[];
  /** POST: campo aceito pelo contrato de inclusão. */
  post: boolean;
  /** POST: obrigatório no Portal; demais obrigatoriedades ficam no ERP. */
  required?: boolean;
  /**
   * PUT: "editable" somente com evidência upstream comprovada no contrato.
   * Campos sem evidência permanecem "readonly" até homologação TOTVS.
   */
  put: "editable" | "readonly";
  get: SupplierFieldGetSource;
  evidence: SupplierFieldEvidence;
};

const F = (
  spec: Omit<SupplierFieldSpec, "get" | "put" | "evidence"> &
    Partial<Pick<SupplierFieldSpec, "get" | "put" | "evidence">>,
): SupplierFieldSpec => ({
  get: "section",
  put: "readonly",
  evidence: "post-matrix",
  ...spec,
});

export const SUPPLIER_FIELD_REGISTRY: ReadonlyArray<SupplierFieldSpec> = [
  // Identificação
  F({
    key: "supplier_code",
    label: "Código",
    section: "identification",
    maxLength: 6,
    digitsOnly: true,
    post: false,
    get: "identity",
    evidence: "system",
  }),
  F({
    key: "supplier_store",
    label: "Loja",
    section: "identification",
    maxLength: 2,
    digitsOnly: true,
    required: true,
    post: true,
    get: "identity",
    evidence: "identity",
  }),
  F({
    key: "person_type",
    label: "Tipo de pessoa",
    section: "identification",
    maxLength: 1,
    post: true,
    options: [
      { value: "J", label: "Jurídica (CNPJ)" },
      { value: "F", label: "Física (CPF)" },
      { value: "X", label: "Outros" },
    ],
  }),
  F({
    key: "tax_id",
    label: "CNPJ/CPF",
    section: "identification",
    maxLength: 14,
    digitsOnly: true,
    post: true,
    get: "top",
  }),
  F({
    key: "supplier_name",
    label: "Razão social",
    section: "identification",
    maxLength: 50,
    post: true,
    put: "editable",
    evidence: "put-contract",
  }),
  F({
    key: "supplier_short_name",
    label: "Nome fantasia",
    section: "identification",
    maxLength: 20,
    post: true,
    put: "editable",
    evidence: "put-contract",
  }),
  // Endereço
  F({ key: "address", label: "Endereço", section: "address", maxLength: 40, post: true }),
  F({ key: "district", label: "Bairro", section: "address", maxLength: 20, post: true }),
  F({
    key: "postal_code",
    label: "CEP",
    section: "address",
    maxLength: 8,
    digitsOnly: true,
    post: true,
  }),
  F({
    key: "state",
    label: "UF",
    section: "address",
    maxLength: 2,
    uppercase: true,
    post: true,
  }),
  F({ key: "city", label: "Cidade", section: "address", maxLength: 25, post: true }),
  F({
    key: "city_code",
    label: "Código IBGE",
    section: "address",
    maxLength: 5,
    digitsOnly: true,
    post: true,
  }),
  // Contato
  F({
    key: "area_code",
    label: "DDD",
    section: "contact",
    maxLength: 3,
    digitsOnly: true,
    post: true,
  }),
  F({ key: "phone", label: "Telefone", section: "contact", maxLength: 50, post: true }),
  F({ key: "contact_name", label: "Contato", section: "contact", maxLength: 15, post: true }),
  F({ key: "email", label: "E-mail", section: "contact", maxLength: 50, post: true }),
  // Fiscal
  F({
    key: "state_registration",
    label: "Inscrição estadual",
    section: "fiscal",
    maxLength: 18,
    post: true,
  }),
  F({
    key: "municipal_registration",
    label: "Inscrição municipal",
    section: "fiscal",
    maxLength: 18,
    post: true,
  }),
  F({ key: "country_code", label: "País", section: "fiscal", maxLength: 3, post: true }),
  F({
    key: "bacen_country_code",
    label: "País (BACEN)",
    section: "fiscal",
    maxLength: 5,
    digitsOnly: true,
    post: true,
  }),
  F({
    key: "rohs_indicator",
    label: "Indicador ROHS",
    section: "fiscal",
    maxLength: 1,
    post: true,
    options: [
      { value: "N", label: "Não" },
      { value: "S", label: "Sim" },
    ],
  }),
  // Compras
  F({
    key: "payment_condition_code",
    label: "Condição de pagamento",
    section: "purchasing",
    maxLength: 3,
    post: true,
  }),
  F({
    key: "payment_method_code",
    label: "Forma de pagamento",
    section: "purchasing",
    maxLength: 2,
    post: true,
  }),
  F({
    key: "accounting_account",
    label: "Conta contábil",
    section: "purchasing",
    maxLength: 20,
    post: true,
  }),
  F({
    key: "financial_nature_code",
    label: "Natureza financeira",
    section: "purchasing",
    maxLength: 10,
    post: true,
  }),
];

export type SupplierFormSection = {
  id: SupplierDetailSectionKey;
  fields: ReadonlyArray<SupplierFieldSpec>;
};

const SECTION_ORDER: SupplierDetailSectionKey[] = [
  "identification",
  "address",
  "contact",
  "fiscal",
  "purchasing",
];

function sectionsOf(
  predicate: (field: SupplierFieldSpec) => boolean,
): SupplierFormSection[] {
  return SECTION_ORDER.map((id) => ({
    id,
    fields: SUPPLIER_FIELD_REGISTRY.filter(
      (f) => f.section === id && predicate(f),
    ),
  }));
}

/** Todas as seções cadastrais — consulta e edição (inclui campos readonly). */
export const SUPPLIER_FORM_SECTIONS: ReadonlyArray<SupplierFormSection> =
  sectionsOf(() => true);

/** Spec de campo aceito pelo POST (key restrita ao draft de criação). */
export type SupplierCreateFieldSpec = SupplierFieldSpec & {
  key: keyof SupplierCreateDraft;
};

const isCreateField = (
  f: SupplierFieldSpec,
): f is SupplierCreateFieldSpec => f.post;

/** Seções do formulário de inclusão — somente campos aceitos pelo POST. */
export const SUPPLIER_CREATE_SECTIONS: ReadonlyArray<{
  id: SupplierDetailSectionKey;
  fields: ReadonlyArray<SupplierCreateFieldSpec>;
}> = sectionsOf(isCreateField) as ReadonlyArray<{
  id: SupplierDetailSectionKey;
  fields: ReadonlyArray<SupplierCreateFieldSpec>;
}>;

/** Campos com alteração comprovada no contrato PUT upstream. */
export const SUPPLIER_PUT_EDITABLE_KEYS = SUPPLIER_FIELD_REGISTRY.filter(
  (f) => f.put === "editable",
).map((f) => f.key);

export const SUPPLIERS_PAGE_SIZE_OPTIONS = [20, 50, 100] as const;
export const SUPPLIERS_EDITABLE_FIELDS = {
  supplier_name: 50,
  supplier_short_name: 20,
} as const;
