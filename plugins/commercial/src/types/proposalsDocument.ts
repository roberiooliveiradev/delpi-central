export type ProposalDocumentListItem = {
  proposta_interna: string;
  numero_ov: string;
  oportunidade: string;
  versao: string;
  data: string | null;
  cliente: string;
  filial: string;
  quantidade_itens: number;
};

export type ProposalDocumentListData = {
  items: ProposalDocumentListItem[];
  total: number;
};

export type ProposalDocumentHeader = {
  proposta_interna: string;
  numero_ov: string;
  oportunidade: string;
  versao: string;
  revisao_oportunidade: string;
  data: string | null;
  validade_dias: number | null;
  filial: string;
  status: string;
  soma_valores_r_mil: string | null;
  soma_valores_r_mil_numerico: number | null;
  total_liquido_r_mil?: number | null;
  total_liquido_r_mil_formatado?: string | null;
};

export type ProposalDocumentCompany = {
  nome: string;
  cnpj: string | null;
  inscricao_estadual: string | null;
  endereco: string;
  bairro: string;
  cidade: string;
  uf: string;
  cep: string | null;
  telefone: string | null;
  site: string;
};

export type ProposalDocumentCustomer = {
  codigo: string;
  loja: string;
  nome: string;
  nome_fantasia?: string | null;
  cnpj: string | null;
  ie?: string | null;
  endereco: string;
  bairro: string;
  cidade: string;
  uf: string;
  cep: string | null;
  telefone: string | null;
  email?: string | null;
  tipo_cadastro?: "cliente" | "prospect" | null;
  is_prospect?: boolean;
};

export type ProposalDocumentContact = {
  codigo: string;
  nome: string;
  email: string;
  telefone: string | null;
  departamento: string;
};

export type ProposalDocumentTerms = {
  codigo: string;
  descricao: string;
  icms: string | null;
  pis_cofins: string;
  ipi: string;
  frete: string;
  embalagem: string;
};

export type ProposalDocumentSeller = {
  codigo: string;
  nome: string;
  email: string;
  telefone: string | null;
  cargo: string;
};

export type ProposalDocumentItem = {
  item: string;
  produto: string;
  descricao: string;
  referencia_cliente: string;
  ncm: string | null;
  quantidade: number;
  unidade: string;
  preco_unitario: string | null;
  preco_unitario_numerico: number;
  valor_bruto_r_mil?: number | null;
  valor_bruto_r_mil_formatado?: string | null;
  valor_liquido_r_mil?: number | null;
  valor_liquido_r_mil_formatado?: string | null;
  valor_total: string | null;
  valor_total_numerico: number;
  prazo_dias: number | null;
  lote_minimo: string | null;
  lote_minimo_numerico?: number | null;
};

export type ProposalDocumentDetail = {
  cabecalho: ProposalDocumentHeader;
  empresa: ProposalDocumentCompany;
  cliente: ProposalDocumentCustomer;
  contato: ProposalDocumentContact;
  condicoes: ProposalDocumentTerms;
  vendedor: ProposalDocumentSeller;
  observacoes: string;
  itens: ProposalDocumentItem[];
};

export type ProposalDocumentPdfItemTextOverrides = {
  item: string;
  descricao?: string;
  referencia_cliente?: string;
  ncm?: string;
  prazo_dias?: string | number | null;
};

export type ProposalDocumentPdfLabelsOverrides = {
  colunas_itens?: Partial<
    Record<
      | "item"
      | "produto"
      | "descricao"
      | "referencia_cliente"
      | "ncm"
      | "quantidade"
      | "valor_bruto"
      | "valor_liquido"
      | "total"
      | "prazo"
      | "lote_minimo",
      string
    >
  >;
  resumo?: Partial<
    Record<"numero_ov" | "data" | "versao" | "total_r_mil" | "empresa" | "cliente", string>
  >;
};

export type ProposalDocumentPdfExportOverrides = {
  exibir_coluna_valor_liquido?: boolean;
  observacoes?: string;
  contato?: Partial<Pick<ProposalDocumentContact, "nome" | "departamento" | "email" | "telefone">>;
  condicoes?: Partial<
    Pick<ProposalDocumentTerms, "descricao" | "icms" | "pis_cofins" | "ipi" | "frete" | "embalagem">
  >;
  vendedor?: Partial<Pick<ProposalDocumentSeller, "nome" | "cargo" | "email" | "telefone">>;
  itens?: ProposalDocumentPdfItemTextOverrides[];
  rotulos?: ProposalDocumentPdfLabelsOverrides;
};
