export type PropostaComercialListItem = {
  proposta_interna: string;
  numero_ov: string;
  oportunidade: string;
  versao: string;
  data: string | null;
  cliente: string;
  filial: string;
  quantidade_itens: number;
};

export type PropostaComercialListData = {
  items: PropostaComercialListItem[];
  total: number;
};

export type PropostaComercialCabecalho = {
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

export type PropostaComercialEmpresa = {
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

export type PropostaComercialCliente = {
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

export type PropostaComercialContato = {
  codigo: string;
  nome: string;
  email: string;
  telefone: string | null;
  departamento: string;
};

export type PropostaComercialCondicoes = {
  codigo: string;
  descricao: string;
  icms: string | null;
  ipi: string;
  frete: string;
  embalagem: string;
};

export type PropostaComercialVendedor = {
  codigo: string;
  nome: string;
  email: string;
  telefone: string | null;
  cargo: string;
};

export type PropostaComercialItem = {
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
  aliquota_icms?: number | null;
  aliquota_pis_cofins?: number | null;
  valor_apos_icms_r_mil?: number | null;
  valor_apos_icms_r_mil_formatado?: string | null;
  valor_liquido_r_mil?: number | null;
  valor_liquido_r_mil_formatado?: string | null;
  id_formacao_preco?: string | null;
  status_calculo_valor_liquido?: string | null;
  fonte_valor_liquido?: string | null;
  valor_total: string | null;
  valor_total_numerico: number;
  prazo_dias: number | null;
  lote_minimo: number | null;
};

export type PropostaComercialDetail = {
  cabecalho: PropostaComercialCabecalho;
  empresa: PropostaComercialEmpresa;
  cliente: PropostaComercialCliente;
  contato: PropostaComercialContato;
  condicoes: PropostaComercialCondicoes;
  vendedor: PropostaComercialVendedor;
  observacoes: string;
  itens: PropostaComercialItem[];
};

export type PropostaComercialPdfExportOverrides = {
  observacoes?: string;
  contato?: Partial<Pick<PropostaComercialContato, "nome" | "departamento" | "email" | "telefone">>;
  condicoes?: Partial<
    Pick<PropostaComercialCondicoes, "descricao" | "icms" | "ipi" | "frete" | "embalagem">
  >;
  vendedor?: Partial<Pick<PropostaComercialVendedor, "nome" | "cargo" | "email" | "telefone">>;
};
