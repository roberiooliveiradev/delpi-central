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

/** Erro de validação por campo — contrato 422 da integração via BFF. */
export type SupplierFieldError = {
  field: SupplierFieldKey;
  message: string;
  code?: string;
};

/**
 * Campos criáveis (POST homologado em E2) SEM evidência de alteração de
 * valor via PUT — permanecem fora de qualquer derivação de editável.
 */
export type SupplierPostOnlyFieldKey =
  | "linked_customer_code"; // E6: upstream PUT ignora mudança de código —
  // entra no payload apenas como companion imutável do par (guard no backend de integração)

/**
 * Os 29 campos estendidos promovidos em E3 — 28 com PUT comprovado nos
 * ensaios E5+E6 (editáveis) + `SupplierPostOnlyFieldKey`, cujo código é
 * companion imutável do par composto upstream.
 */
export type SupplierExtendedFieldKey =
  | "legal_entity_type" | "address_number" | "po_box"
  | "commercial_contact_name" | "responsible_name" | "fax" | "website"
  | "icms_contributor" | "simples_nacional" | "cnae_code" | "simp_regime_code"
  | "pb_regime_code" | "tax_group_code" | "inss_withholding" | "iss_withholding"
  | "csll_withholding" | "cofins_withholding" | "pis_withholding"
  | "irf_calculation" | "inp_calculation" | "purchase_price_table_code"
  | "risk_code" | "swift_code" | "carrier_code" | "segment_code"
  | "administrator_code" | "linked_customer_code" | "linked_customer_store"
  | "linked_employee_code";

export type SupplierEditableFieldKey = Exclude<
  keyof SupplierCreateDraft,
  "tax_id" | "supplier_store" | SupplierPostOnlyFieldKey
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
  // X4.FIELDS.E3 — 29 campos com persistência POST comprovada em
  // homologação (E2). Criáveis; edição permanece `readonly` até a
  // homologação PUT dedicada (E3.S4).
  address_number: string;
  po_box: string;
  icms_contributor: string;
  simples_nacional: string;
  cnae_code: string;
  legal_entity_type: string;
  simp_regime_code: string;
  pb_regime_code: string;
  inss_withholding: string;
  iss_withholding: string;
  csll_withholding: string;
  cofins_withholding: string;
  pis_withholding: string;
  irf_calculation: string;
  inp_calculation: string;
  tax_group_code: string;
  commercial_contact_name: string;
  fax: string;
  website: string;
  responsible_name: string;
  risk_code: string;
  swift_code: string;
  purchase_price_table_code: string;
  carrier_code: string;
  segment_code: string;
  administrator_code: string;
  linked_customer_code: string;
  linked_customer_store: string;
  linked_employee_code: string;
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
  | "put-homologated" // X4.FIELDS.E5 — PUT comprovado em DELPI_TST01
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
  /** Mensagem PT-BR exibida quando o campo obrigatório está ausente. */
  requiredMessage?: string;
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
  /**
   * Catálogos compostos (ex.: `customers` → código+loja): qual chave do
   * item vira o valor deste campo. Default `"code"`.
   */
  catalogValueField?: "code" | "store";
  /**
   * Campo cujo valor alimenta o parâmetro `code` do catálogo (filtro
   * exato — ex.: lojas do cliente vinculado em `customers`).
   */
  catalogCodeParam?: SupplierFieldKey;
  /**
   * Campo-irmão que recebe `item.store` quando este campo usa um catálogo
   * composto — ex.: `linked_customer_code` preenche `linked_customer_store`.
   */
  catalogPairField?: SupplierFieldKey;
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
  | "municipalities"
  | "carriers"
  | "segments"
  | "administrators"
  | "employees"
  | "price-tables"
  | "customers";

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
    help: "Documento fiscal do fornecedor — CNPJ para pessoa jurídica ou CPF para pessoa física. Na inclusão, identifica o cadastro e ajuda a evitar duplicidades; na edição é protegido e não pode ser alterado. (TOTVS: SA2.A2_CGC)",
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
    help: "Natureza do cadastro: J para pessoa jurídica (CNPJ), F para pessoa física (CPF) ou X para outras situações. A escolha define como o ERP trata o documento e os dados fiscais do fornecedor. (TOTVS: SA2.A2_TIPO)",
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
    help: "Código do fornecedor no Protheus, gerado na inclusão. É a identificação do cadastro e não pode ser alterado. (TOTVS: SA2.A2_COD)",
  }),
  F({
    key: "supplier_store",
    label: "Loja",
    section: "identification",
    maxLength: 2,
    digitsOnly: true,
    required: true,
    requiredMessage: "Informe a loja com exatamente 2 dígitos.",
    post: true,
    put: "protected",
    get: "identity",
    evidence: "identity",
    span: 2,
    help: "Loja do cadastro do fornecedor — distingue unidades ou filiais do mesmo fornecedor. Definida na inclusão e não pode ser alterada. (TOTVS: SA2.A2_LOJA)",
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
    help: "Razão social do fornecedor, conforme o registro oficial. Use a denominação cadastral para identificar corretamente a empresa em pedidos, títulos e documentos. (TOTVS: SA2.A2_NOME)",
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
    help: "Nome fantasia — forma curta pela qual o fornecedor é conhecido nas operações do dia a dia. Pode ser diferente da razão social. (TOTVS: SA2.A2_NREDUZ)",
  }),
  // Endereço
  E({
    key: "address",
    label: "Endereço",
    section: "address",
    maxLength: 40,
    span: 6,
    help: "Logradouro do endereço cadastral do fornecedor — rua, avenida ou equivalente, sem o número do imóvel. (TOTVS: SA2.A2_END)",
  }),
  E({
    key: "district",
    label: "Bairro",
    section: "address",
    maxLength: 20,
    span: 3,
    help: "Bairro do endereço do fornecedor. (TOTVS: SA2.A2_BAIRRO)",
  }),
  E({
    key: "postal_code",
    label: "CEP",
    section: "address",
    maxLength: 8,
    digitsOnly: true,
    span: 3,
    help: "CEP do endereço do fornecedor. A consulta por CEP sugere logradouro, bairro, cidade e UF — confira as sugestões antes de aplicar. (TOTVS: SA2.A2_CEP)",
  }),
  E({
    key: "city",
    label: "Cidade",
    section: "address",
    maxLength: 25,
    span: 4,
    catalog: "municipalities",
    catalogDependsOn: "state",
    help: "Município do fornecedor. Ao escolher na lista, o código oficial do município é preenchido automaticamente. (TOTVS: SA2.A2_MUN)",
  }),
  E({
    key: "city_code",
    label: "Código IBGE",
    section: "address",
    maxLength: 5,
    digitsOnly: true,
    span: 2,
    catalogDerivedFrom: "city",
    help: "Código oficial do município, preenchido automaticamente pela seleção da cidade. Usado em obrigações fiscais. (TOTVS: SA2.A2_COD_MUN)",
  }),
  E({
    key: "state",
    label: "UF",
    section: "address",
    maxLength: 2,
    uppercase: true,
    span: 2,
    catalog: "states",
    help: "Unidade federativa do fornecedor (UF). Para fornecedores no exterior, utilize EX. (TOTVS: SA2.A2_EST)",
  }),
  E({
    key: "country_code",
    label: "País",
    section: "address",
    maxLength: 3,
    span: 4,
    catalog: "countries",
    help: "País do fornecedor — informe quando o fornecedor for estrangeiro, selecionando na lista de países. (TOTVS: SA2.A2_PAIS)",
  }),
  // Contato
  E({
    key: "contact_name",
    label: "Contato",
    section: "contact",
    maxLength: 15,
    span: 4,
    help: "Pessoa de contato do fornecedor para assuntos gerais do cadastro e da operação. (TOTVS: SA2.A2_CONTATO)",
  }),
  E({
    key: "area_code",
    label: "DDD",
    section: "contact",
    maxLength: 3,
    digitsOnly: true,
    span: 2,
    help: "DDD do telefone do fornecedor, somente dígitos. (TOTVS: SA2.A2_DDD)",
  }),
  E({
    key: "phone",
    label: "Telefone",
    section: "contact",
    maxLength: 50,
    span: 3,
    help: "Telefone principal do fornecedor, somente dígitos — pode incluir ramal ou mais de um número. (TOTVS: SA2.A2_TEL)",
  }),
  E({
    key: "email",
    label: "E-mail",
    section: "contact",
    maxLength: 50,
    span: 3,
    help: "E-mail principal do fornecedor para contato e envio de documentos. (TOTVS: SA2.A2_EMAIL)",
  }),
  // Fiscal
  E({
    key: "state_registration",
    label: "Inscrição estadual",
    section: "fiscal",
    maxLength: 18,
    span: 4,
    help: "Inscrição estadual do fornecedor — número registrado na Secretaria da Fazenda da UF. Informe ISENTO quando o fornecedor for isento. (TOTVS: SA2.A2_INSCR)",
  }),
  E({
    key: "municipal_registration",
    label: "Inscrição municipal",
    section: "fiscal",
    maxLength: 18,
    span: 4,
    help: "Inscrição municipal do fornecedor junto à prefeitura do município, quando aplicável. (TOTVS: SA2.A2_INSCRM)",
  }),
  E({
    key: "rohs_indicator",
    label: "Indicador ROHS",
    required: true,
    requiredMessage: "Selecione o indicador ROHS.",
    section: "fiscal",
    maxLength: 1,
    span: 4,
    options: [
      { value: "N", label: "Não" },
      { value: "S", label: "Sim" },
    ],
    help: "Indica se o fornecedor atende à diretiva RoHS de restrição de substâncias perigosas — informação usada no controle ambiental de materiais. (TOTVS: SA2.A2_YROHS)",
  }),
  E({
    key: "bacen_country_code",
    label: "País (BACEN)",
    required: true,
    requiredMessage: "Selecione o país conforme a tabela BACEN.",
    section: "fiscal",
    maxLength: 5,
    digitsOnly: true,
    span: 4,
    catalog: "bacen-countries",
    help: "Código do país no padrão do Banco Central, usado em operações internacionais e obrigações fiscais. Para fornecedores brasileiros, o código vigente é 01058. (TOTVS: SA2.A2_CODPAIS)",
  }),
  // Compras
  E({
    key: "payment_condition_code",
    label: "Condição de pagamento",
    required: true,
    requiredMessage: "Selecione a condição de pagamento.",
    section: "purchasing",
    maxLength: 3,
    span: 4,
    catalog: "payment-conditions",
    help: "Condição de pagamento padrão nas operações com o fornecedor — prazos e forma de parcelamento. Selecione uma condição cadastrada no Protheus. (TOTVS: SA2.A2_COND)",
  }),
  E({
    key: "payment_method_code",
    label: "Forma de pagamento",
    required: true,
    requiredMessage: "Selecione a forma de pagamento.",
    section: "purchasing",
    maxLength: 2,
    span: 4,
    catalog: "payment-methods",
    help: "Forma de pagamento preferencial nas operações com o fornecedor. Selecione uma forma cadastrada no Protheus. (TOTVS: SA2.A2_FORMPAG)",
  }),
  E({
    key: "accounting_account",
    label: "Conta contábil",
    required: true,
    requiredMessage: "Selecione uma conta contábil.",
    section: "purchasing",
    maxLength: 20,
    span: 6,
    catalog: "accounting-accounts",
    help: "Conta contábil padrão usada na contabilização das operações com o fornecedor. Selecione uma conta do plano de contas. (TOTVS: SA2.A2_CONTA)",
  }),
  E({
    key: "financial_nature_code",
    label: "Natureza financeira",
    required: true,
    requiredMessage: "Selecione a natureza financeira.",
    section: "purchasing",
    maxLength: 10,
    span: 6,
    catalog: "financial-natures",
    help: "Natureza financeira padrão para classificação dos títulos gerados nas operações com o fornecedor. Selecione uma natureza cadastrada no Protheus. (TOTVS: SA2.A2_NATUREZ)",
  }),
  // ------------------------------------------------------------------
  // X4.FIELDS.E3 — campos com persistência POST comprovada em homologação
  // (E2, DELPI_TST01). Criáveis via POST; edição permanece `readonly` até
  // a homologação PUT dedicada (E3.S4). Sem catálogo contratado para os
  // códigos de referência — seleção assistida pendente de owner (residual).
  // ------------------------------------------------------------------
  // Identificação — classificação cadastral
  F({
    key: "legal_entity_type",
    put: "editable",
    evidence: "put-homologated",
    label: "Natureza jurídica",
    section: "identification",
    maxLength: 1,
    post: true,
    span: 4,
    options: [
      { value: "1", label: "ME — Micro Empresa" },
      { value: "2", label: "EPP — Empresa de Pequeno Porte" },
      { value: "3", label: "MEI — Microempreendedor Individual" },
      { value: "4", label: "Cooperativa" },
      { value: "5", label: "Não optante" },
    ],
    help: "Natureza jurídica do fornecedor conforme a classificação do cadastro — microempresa, empresa de pequeno porte, MEI ou cooperativa. Selecione a opção correspondente. (TOTVS: SA2.A2_TPJ)",
  }),
  // Endereço
  F({
    key: "address_number",
    put: "editable",
    evidence: "put-homologated",
    label: "Número",
    section: "address",
    maxLength: 6,
    digitsOnly: true,
    post: true,
    span: 2,
    help: "Número do imóvel no endereço do fornecedor. Informe apenas o número — o logradouro permanece no campo Endereço. (TOTVS: SA2.A2_NR_END)",
  }),
  F({
    key: "po_box",
    put: "editable",
    evidence: "put-homologated",
    label: "Caixa postal",
    section: "address",
    maxLength: 5,
    post: true,
    span: 3,
    help: "Caixa postal do fornecedor — informe quando a correspondência não usa o endereço físico. (TOTVS: SA2.A2_CX_POST)",
  }),
  // Contato
  F({
    key: "commercial_contact_name",
    put: "editable",
    evidence: "put-homologated",
    label: "Contato comercial",
    section: "contact",
    maxLength: 15,
    post: true,
    span: 4,
    help: "Pessoa indicada pelo fornecedor para tratar de propostas, preços, negociações e demais assuntos comerciais. (TOTVS: SA2.A2_CONTCOM)",
  }),
  F({
    key: "responsible_name",
    put: "editable",
    evidence: "put-homologated",
    label: "Responsável",
    section: "contact",
    maxLength: 45,
    post: true,
    span: 4,
    help: "Nome do responsável pelo relacionamento com o fornecedor, quando essa referência for mantida no cadastro. (TOTVS: SA2.A2_NOMRESP)",
  }),
  F({
    key: "fax",
    put: "editable",
    evidence: "put-homologated",
    label: "Fax",
    section: "contact",
    maxLength: 15,
    digitsOnly: true,
    post: true,
    span: 2,
    help: "Número de fax do fornecedor, somente dígitos. (TOTVS: SA2.A2_FAX)",
  }),
  F({
    key: "website",
    put: "editable",
    evidence: "put-homologated",
    label: "Site",
    section: "contact",
    maxLength: 30,
    post: true,
    span: 6,
    help: "Site ou página eletrônica do fornecedor. (TOTVS: SA2.A2_HPAGE)",
  }),
  // Fiscal e tributário
  F({
    key: "icms_contributor",
    put: "editable",
    evidence: "put-homologated",
    label: "Contribuinte ICMS",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Contribuinte" },
      { value: "2", label: "Não contribuinte" },
    ],
    help: "Indica se o fornecedor é contribuinte de ICMS — influencia o tratamento do imposto nas operações de compra. (TOTVS: SA2.A2_CONTRIB)",
  }),
  F({
    key: "simples_nacional",
    put: "editable",
    evidence: "put-homologated",
    label: "Simples Nacional",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Optante" },
      { value: "2", label: "Não optante" },
    ],
    help: "Indica se o fornecedor é optante pelo Simples Nacional — o regime simplificado altera a apuração dos impostos nas operações. (TOTVS: SA2.A2_SIMPNAC)",
  }),
  F({
    key: "cnae_code",
    put: "editable",
    evidence: "put-homologated",
    label: "CNAE",
    section: "fiscal",
    maxLength: 9,
    digitsOnly: true,
    post: true,
    span: 3,
    help: "CNAE — código da atividade econômica principal do fornecedor, conforme a classificação oficial. Aplicável a pessoa jurídica e demais naturezas não físicas. (TOTVS: SA2.A2_CNAE)",
  }),
  F({
    key: "simp_regime_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Regime SIMP",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Sim" },
      { value: "2", label: "Não" },
    ],
    help: "Indica se o fornecedor utiliza o regime simplificado de tributação aplicável no estado. Selecione conforme o enquadramento fiscal do cadastro. (TOTVS: SA2.A2_REGESIM)",
  }),
  F({
    key: "pb_regime_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Regime PB",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Regime 1" },
      { value: "2", label: "Regime 2" },
    ],
    help: "Regime de apuração de PIS/COFINS do fornecedor. Selecione a opção conforme a orientação da área fiscal. (TOTVS: SA2.A2_REGPB)",
  }),
  F({
    key: "tax_group_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Grupo tributário",
    section: "fiscal",
    maxLength: 3,
    post: true,
    span: 3,
    help: "Grupo de tributação atribuído ao fornecedor para classificação fiscal interna. Informe o código definido pela área fiscal — os códigos em uso não seguem uma lista fechada no cadastro. (TOTVS: SA2.A2_GRPTRIB)",
  }),
  F({
    key: "inss_withholding",
    put: "editable",
    evidence: "put-homologated",
    label: "Retenção INSS",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "S", label: "Retém" },
      { value: "N", label: "Não retém" },
    ],
    help: "Indica se há retenção de INSS nos pagamentos feitos ao fornecedor, conforme a legislação previdenciária aplicável. (TOTVS: SA2.A2_RECINSS)",
  }),
  F({
    key: "iss_withholding",
    put: "editable",
    evidence: "put-homologated",
    label: "Retenção ISS",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "S", label: "Retém" },
      { value: "N", label: "Não retém" },
    ],
    help: "Indica se há retenção de ISS nas operações com o fornecedor. O enquadramento deve seguir a orientação fiscal da empresa. (TOTVS: SA2.A2_RECISS)",
  }),
  F({
    key: "csll_withholding",
    put: "editable",
    evidence: "put-homologated",
    label: "Retenção CSLL",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Retém" },
      { value: "2", label: "Não retém" },
    ],
    help: "Regra de retenção de CSLL aplicada aos pagamentos do fornecedor, conforme o enquadramento fiscal vigente. (TOTVS: SA2.A2_RECCSLL)",
  }),
  F({
    key: "cofins_withholding",
    put: "editable",
    evidence: "put-homologated",
    label: "Retenção COFINS",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Retém" },
      { value: "2", label: "Não retém" },
    ],
    help: "Regra de retenção de COFINS aplicada aos pagamentos do fornecedor, conforme o enquadramento fiscal vigente. (TOTVS: SA2.A2_RECCOFI)",
  }),
  F({
    key: "pis_withholding",
    put: "editable",
    evidence: "put-homologated",
    label: "Retenção PIS",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Retém" },
      { value: "2", label: "Não retém" },
    ],
    help: "Regra de retenção de PIS aplicada aos pagamentos do fornecedor, conforme o enquadramento fiscal vigente. (TOTVS: SA2.A2_RECPIS)",
  }),
  F({
    key: "irf_calculation",
    put: "editable",
    evidence: "put-homologated",
    label: "Cálculo IRRF",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Regra 1" },
      { value: "2", label: "Regra 2" },
      { value: "3", label: "Regra 3" },
      { value: "4", label: "Regra 4" },
    ],
    help: "Indica se é calculado IRRF — imposto de renda retido na fonte — nos pagamentos ao fornecedor. (TOTVS: SA2.A2_CALCIRF)",
  }),
  F({
    key: "inp_calculation",
    put: "editable",
    evidence: "put-homologated",
    label: "Cálculo INP",
    section: "fiscal",
    maxLength: 1,
    post: true,
    span: 3,
    options: [
      { value: "1", label: "Regra 1" },
      { value: "2", label: "Regra 2" },
    ],
    help: "Indica se é calculado o INSS patronal sobre os pagamentos ao fornecedor. (TOTVS: SA2.A2_CALCINP)",
  }),
  // Compras e relacionamentos
  F({
    key: "purchase_price_table_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Tabela de preços",
    section: "purchasing",
    maxLength: 3,
    post: true,
    span: 3,
    catalog: "price-tables",
    help: "Tabela de preços de compra associada ao fornecedor, usada como referência em cotações e pedidos. Selecione uma tabela cadastrada no Protheus. (TOTVS: SA2.A2_ZTABPRC)",
  }),
  F({
    key: "risk_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Código de risco",
    section: "purchasing",
    maxLength: 3,
    post: true,
    span: 3,
    help: "Classificação de risco atribuída ao fornecedor para os processos que consultam essa informação. Informe o código conforme a política vigente — a classificação não segue uma lista fechada no cadastro. (TOTVS: SA2.A2_RISCO)",
  }),
  F({
    key: "swift_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Código SWIFT",
    section: "purchasing",
    maxLength: 30,
    uppercase: true,
    post: true,
    span: 4,
    help: "Código SWIFT do banco do fornecedor, utilizado em pagamentos internacionais. (TOTVS: SA2.A2_SWIFT)",
  }),
  F({
    key: "carrier_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Transportadora",
    section: "purchasing",
    maxLength: 6,
    post: true,
    span: 3,
    catalog: "carriers",
    help: "Transportadora normalmente utilizada nas entregas relacionadas ao fornecedor. Selecione uma transportadora cadastrada no Protheus. (TOTVS: SA2.A2_TRANSP)",
  }),
  F({
    key: "segment_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Segmento",
    section: "purchasing",
    maxLength: 6,
    post: true,
    span: 3,
    catalog: "segments",
    help: "Segmento de atuação do fornecedor, conforme a classificação cadastrada no Protheus. (TOTVS: SA2.A2_SATIV1)",
  }),
  F({
    key: "administrator_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Administrador",
    section: "purchasing",
    maxLength: 3,
    post: true,
    span: 3,
    catalog: "administrators",
    help: "Administrador responsável pelo fornecedor nos processos financeiros. Selecione um administrador cadastrado no Protheus. (TOTVS: SA2.A2_CODADM)",
  }),
  F({
    key: "linked_customer_code",
    label: "Cliente vinculado",
    section: "purchasing",
    maxLength: 6,
    post: true,
    span: 3,
    catalog: "customers",
    catalogPairField: "linked_customer_store",
    help: "Cliente relacionado a este fornecedor no Protheus. Na inclusão, a seleção preenche código e loja do vínculo; na edição, o código do cliente vinculado não pode ser alterado — apenas a loja do vínculo existente. (TOTVS: SA2.A2_CLIENTE + SA2.A2_LOJCLI)",
  }),
  F({
    key: "linked_customer_store",
    put: "editable",
    evidence: "put-homologated",
    label: "Loja do cliente",
    section: "purchasing",
    maxLength: 2,
    digitsOnly: true,
    post: true,
    span: 3,
    catalog: "customers",
    catalogValueField: "store",
    catalogCodeParam: "linked_customer_code",
    help: "Loja do cliente vinculado ao fornecedor. As opções exibidas são as lojas do cliente atualmente vinculado — a troca exige que o vínculo já exista. (TOTVS: SA2.A2_LOJCLI)",
  }),
  F({
    key: "linked_employee_code",
    put: "editable",
    evidence: "put-homologated",
    label: "Funcionário vinculado",
    section: "purchasing",
    maxLength: 6,
    post: true,
    span: 4,
    catalog: "employees",
    help: "Funcionário da empresa vinculado a este fornecedor — contato interno ou responsável relacionado ao vínculo. Selecione um funcionário cadastrado no Protheus. (TOTVS: SA2.A2_NUMRA)",
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


/** X4.REST-STATUS.S1 — diagnóstico read-only da integração REST (BFF sanitizado). */
export type SupplierIntegrationStatus = {
  checked_at: string | null;
  environment: string | null;
  configuration: string | null;
  connectivity: string | null;
  authentication: string | null;
  authentication_http_status: number | null;
  suppliers_read: string | null;
  create_gate: string | null;
  update_gate: string | null;
  write_target_guard: string | null;
  write_validation: string | null;
  overall: string | null;
};
