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

/** Campos editáveis via PUT: todo POST cadastral exceto documento e loja. */
export type SupplierEditableFieldKey = Exclude<
  keyof SupplierCreateDraft,
  "tax_id" | "supplier_store"
>;

export type SupplierEditDraft = Record<SupplierEditableFieldKey, string>;

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
  | "po-decision" // decisão funcional PO (F3.3) — upstream pendente de homologação
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
   * PUT: "editable" = liberado pela decisão funcional (gate upstream ainda
   * protege a escrita real); "protected" = documento/identidade, nunca
   * editável nesta funcionalidade; "readonly" = pendente de contrato.
   */
  put: "editable" | "readonly" | "protected";
  get: SupplierFieldGetSource;
  evidence: SupplierFieldEvidence;
  /** Largura visual no grid de 12 colunas (UX spec; mobile colapsa para 1 col). */
  span: number;
  /** Ajuda contextual exibida na própria label (tooltip oficial do kit). */
  help?: string;
  /**
   * Catálogo TOTVS da BFF (`/suppliers/catalogs/<kind>`) que fornece as
   * opções válidas do campo — ver `supplierCatalogs.ts`.
   */
  catalog?: SupplierCatalogKind;
  /** Campo cujo valor alimenta o filtro do catálogo (ex.: UF → municípios). */
  catalogDependsOn?: SupplierFieldKey;
  /** Campo preenchido automaticamente pela seleção de outro catálogo. */
  catalogDerivedFrom?: SupplierFieldKey;
};

/** Catálogos expostos pela BFF (`supplies-api` allowlist espelha o serviço de integração). */
export type SupplierCatalogKind =
  | "states"
  | "countries"
  | "bacen-countries"
  | "payment-conditions"
  | "payment-methods"
  | "financial-natures"
  | "accounting-accounts"
  | "municipalities";

const F = (
  spec: Omit<SupplierFieldSpec, "get" | "put" | "evidence"> &
    Partial<Pick<SupplierFieldSpec, "get" | "put" | "evidence">>,
): SupplierFieldSpec => ({
  get: "section",
  put: "readonly",
  evidence: "post-matrix",
  ...spec,
});

/**
 * Campo cadastral editável via PUT — decisão funcional do PO (F3.3).
 * A evidência upstream PUT permanece pendente de homologação TOTVS; a
 * escrita real continua protegida pelo feature gate no backend.
 */
const E = (
  spec: Omit<SupplierFieldSpec, "get" | "put" | "evidence" | "post">,
): SupplierFieldSpec =>
  F({ ...spec, post: true, put: "editable", evidence: "po-decision" });

export const SUPPLIER_FIELD_REGISTRY: ReadonlyArray<SupplierFieldSpec> = [
  // Identificação — CNPJ/CPF primeiro (decisão visual do PO, F5-UX-R2)
  F({
    key: "tax_id",
    label: "CNPJ/CPF",
    section: "identification",
    maxLength: 14,
    digitsOnly: true,
    post: true,
    put: "protected",
    get: "top",
    span: 4,
    help: "Documento fiscal (CNPJ ou CPF) que identifica o fornecedor. Na inclusão informe um documento válido; na edição é protegido e não pode ser alterado.",
  }),
  E({
    key: "person_type",
    label: "Tipo de pessoa",
    section: "identification",
    maxLength: 1,
    span: 4,
    options: [
      { value: "J", label: "Jurídica (CNPJ)" },
      { value: "F", label: "Física (CPF)" },
      { value: "X", label: "Outros" },
    ],
    help: "Classificação cadastral do fornecedor conforme os tipos aceitos pelo Protheus (Jurídica, Física, Outros).",
  }),
  F({
    key: "supplier_code",
    label: "Código",
    section: "identification",
    maxLength: 6,
    digitsOnly: true,
    post: false,
    put: "protected",
    get: "identity",
    evidence: "system",
    span: 2,
    help: "Identificador do fornecedor no Protheus, gerado pelo ERP na inclusão; protegido na edição.",
  }),
  F({
    key: "supplier_store",
    label: "Loja",
    section: "identification",
    maxLength: 2,
    digitsOnly: true,
    required: true,
    post: true,
    put: "protected",
    get: "identity",
    evidence: "identity",
    span: 2,
    help: "Estabelecimento (loja) associado ao código do fornecedor. Obrigatória na inclusão e protegida na edição.",
  }),
  F({
    key: "supplier_name",
    label: "Razão social",
    section: "identification",
    maxLength: 50,
    post: true,
    put: "editable",
    evidence: "put-contract",
    span: 6,
    help: "Razão social do fornecedor no cadastro do Protheus (A2_NOME), até 50 caracteres.",
  }),
  F({
    key: "supplier_short_name",
    label: "Nome fantasia",
    section: "identification",
    maxLength: 20,
    post: true,
    put: "editable",
    evidence: "put-contract",
    span: 6,
    help: "Nome fantasia ou nome reduzido do fornecedor (A2_NREDUZ), até 20 caracteres.",
  }),
  // Endereço
  E({
    key: "address",
    label: "Endereço",
    section: "address",
    maxLength: 40,
    span: 6,
    help: "Logradouro cadastral do fornecedor (A2_END). Pode receber sugestão da consulta por CEP e ser ajustado manualmente.",
  }),
  E({
    key: "district",
    label: "Bairro",
    section: "address",
    maxLength: 20,
    span: 3,
    help: "Bairro do endereço (A2_BAIRRO). Confira a sugestão retornada pela consulta de CEP.",
  }),
  E({
    key: "postal_code",
    label: "CEP",
    section: "address",
    maxLength: 8,
    digitsOnly: true,
    span: 3,
    help: "Informe o CEP (somente dígitos, A2_CEP) para consultar uma sugestão de endereço. Confira os dados antes de aplicá-los.",
  }),
  E({
    key: "city",
    label: "Cidade",
    section: "address",
    maxLength: 25,
    span: 4,
    catalog: "municipalities",
    catalogDependsOn: "state",
    help: "Município do fornecedor (A2_MUN), conciliado com o cadastro Protheus quando possível — selecione a UF e pesquise pelo nome.",
  }),
  E({
    key: "city_code",
    label: "Código IBGE",
    section: "address",
    maxLength: 5,
    digitsOnly: true,
    span: 2,
    catalogDerivedFrom: "city",
    help: "Código do município utilizado no cadastro Protheus (A2_COD_MUN). A correspondência com o código IBGE externo é validada antes de aplicar.",
  }),
  E({
    key: "state",
    label: "UF",
    section: "address",
    maxLength: 2,
    uppercase: true,
    span: 2,
    catalog: "states",
    help: "Unidade federativa do endereço (A2_EST) — selecione a UF cadastrada no Protheus; pode ser sugerida pela consulta de CEP.",
  }),
  E({
    key: "country_code",
    label: "País",
    section: "address",
    maxLength: 3,
    span: 4,
    catalog: "countries",
    help: "País cadastral do endereço (A2_PAIS) — pesquise pelo código ou descrição e selecione uma opção válida.",
  }),
  // Contato
  E({
    key: "contact_name",
    label: "Contato",
    section: "contact",
    maxLength: 15,
    span: 4,
    help: "Pessoa de referência para comunicação com o fornecedor (A2_CONTATO).",
  }),
  E({
    key: "area_code",
    label: "DDD",
    section: "contact",
    maxLength: 3,
    digitsOnly: true,
    span: 2,
    help: "Código de área do telefone cadastrado (A2_DDD).",
  }),
  E({
    key: "phone",
    label: "Telefone",
    section: "contact",
    maxLength: 50,
    span: 3,
    help: "Telefone utilizado para contato com o fornecedor (A2_TEL).",
  }),
  E({
    key: "email",
    label: "E-mail",
    section: "contact",
    maxLength: 50,
    span: 3,
    help: "Endereço eletrônico de contato do fornecedor (A2_EMAIL).",
  }),
  // Fiscal
  E({
    key: "state_registration",
    label: "Inscrição estadual",
    section: "fiscal",
    maxLength: 18,
    span: 4,
    help: "Identificação fiscal estadual do fornecedor, quando aplicável (A2_INSCR).",
  }),
  E({
    key: "municipal_registration",
    label: "Inscrição municipal",
    section: "fiscal",
    maxLength: 18,
    span: 4,
    help: "Identificação fiscal municipal do fornecedor, quando aplicável.",
  }),
  E({
    key: "rohs_indicator",
    label: "Indicador ROHS",
    section: "fiscal",
    maxLength: 1,
    span: 4,
    options: [
      { value: "N", label: "Não" },
      { value: "S", label: "Sim" },
    ],
    help: "Indicador cadastral ROHS utilizado pelo Protheus. A semântica detalhada é definida pelo ERP.",
  }),
  E({
    key: "bacen_country_code",
    label: "País (BACEN)",
    section: "fiscal",
    maxLength: 5,
    digitsOnly: true,
    span: 4,
    catalog: "bacen-countries",
    help: "Código de país BACEN usado pelo Protheus (A2_CODPAIS) — pesquise pelo código ou nome; campo distinto do país cadastral.",
  }),
  // Compras
  E({
    key: "payment_condition_code",
    label: "Condição de pagamento",
    section: "purchasing",
    maxLength: 3,
    span: 4,
    catalog: "payment-conditions",
    help: "Pesquise pelo código ou descrição e selecione a condição de pagamento cadastrada no Protheus (SE4/A2_COND).",
  }),
  E({
    key: "payment_method_code",
    label: "Forma de pagamento",
    section: "purchasing",
    maxLength: 2,
    span: 4,
    catalog: "payment-methods",
    help: "Selecione a forma de pagamento cadastrada no Protheus (tabela de opções 58 / A2_FORMPAG).",
  }),
  E({
    key: "accounting_account",
    label: "Conta contábil",
    section: "purchasing",
    maxLength: 20,
    span: 6,
    catalog: "accounting-accounts",
    help: "Pesquise pelo código ou descrição e selecione a conta contábil do plano de contas (CT1/A2_CONTA), até 20 caracteres.",
  }),
  E({
    key: "financial_nature_code",
    label: "Natureza financeira",
    section: "purchasing",
    maxLength: 10,
    span: 6,
    catalog: "financial-natures",
    help: "Pesquise pelo código ou descrição e selecione a natureza financeira cadastrada no Protheus (SED/A2_NATUREZ).",
  }),
];

/** Rótulo curto de tipo de pessoa para chips de identidade (header/consulta). */
export const SUPPLIER_PERSON_TYPE_LABELS: Record<string, string> = {
  J: "Jurídica",
  F: "Física",
  X: "Outros",
};

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
