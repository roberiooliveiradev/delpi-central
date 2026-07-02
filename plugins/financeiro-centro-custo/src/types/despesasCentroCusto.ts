export type DespesasPeriodo = {
  data_inicio: string;
  data_fim: string;
};

export type DespesasFiltrosData = {
  periodo: DespesasPeriodo;
  filiais: Array<{ codigo: string }>;
  centros_custo: Array<{ codigo: string; descricao: string }>;
  fornecedores: Array<{
    codigo: string;
    loja: string;
    razao_social: string;
  }>;
};

export type DespesasResumoData = {
  periodo: DespesasPeriodo;
  total_periodo: number;
  quantidade_lancamentos: number;
  quantidade_centros_custo: number;
  quantidade_fornecedores: number;
  ticket_medio: number;
  maior_lancamento: number;
};

export type DespesasSeriePoint = {
  ano_mes: string;
  ano: number;
  mes: number;
  valor_total: number;
  quantidade_lancamentos: number;
};

export type DespesasSerieData = {
  periodo: DespesasPeriodo;
  serie: DespesasSeriePoint[];
};

export type DespesasRankingCentroItem = {
  centro_custo_codigo: string;
  centro_custo_descricao: string;
  valor_total: number;
  quantidade_lancamentos: number;
  percentual: number;
};

export type DespesasRankingCentrosData = {
  periodo: DespesasPeriodo;
  ranking: DespesasRankingCentroItem[];
};

export type DespesasRankingFornecedorItem = {
  fornecedor_cliente_codigo: string;
  loja: string;
  razao_social: string;
  valor_total: number;
  quantidade_lancamentos: number;
  percentual: number;
};

export type DespesasRankingFornecedoresData = {
  periodo: DespesasPeriodo;
  ranking: DespesasRankingFornecedorItem[];
};

export type DespesasLancamentoItem = {
  filial: string;
  data_emissao: string;
  data_emissao_formatada: string;
  centro_custo_codigo: string;
  centro_custo_descricao: string;
  fornecedor_cliente_codigo: string;
  loja: string;
  razao_social: string;
  documento: string;
  serie: string;
  pedido: string;
  item: string;
  item_pedido: string;
  produto_codigo: string;
  produto_descricao: string;
  observacoes: string;
  quantidade: number;
  valor_unitario: number;
  valor_total: number;
  conta_contabil: string;
  rateio: string;
  tes: string;
  cfop: string;
  tipo_documento: string;
  tipo_produto_lancamento: string;
  recno_sd1: number;
};

export type DespesasLancamentosPagination = {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export type DespesasLancamentosData = {
  periodo: DespesasPeriodo;
  pagination: DespesasLancamentosPagination;
  sort: {
    sort_by: LancamentosSortBy;
    sort_dir: SortDirection;
  };
  items: DespesasLancamentoItem[];
};

export type LancamentosSortBy =
  | "data_emissao"
  | "documento"
  | "razao_social"
  | "centro_custo_codigo"
  | "centro_custo_descricao"
  | "produto_codigo"
  | "produto_descricao"
  | "valor_total";

export type SortDirection = "asc" | "desc";

export type DespesasQueryFilters = {
  startDate: string;
  endDate: string;
  branch?: string;
  costCenter?: string;
  supplierCode?: string;
  supplierStore?: string;
};

export type LancamentosQueryParams = DespesasQueryFilters & {
  page?: number;
  pageSize?: number;
  search?: string;
  sortBy?: LancamentosSortBy;
  sortDir?: SortDirection;
};

export type FilterFormState = {
  startDate: string;
  endDate: string;
  branch: string;
  costCenter: string;
  supplierKey: string;
};

export const DEFAULT_LANCAMENTOS_PAGE_SIZE = 50;
export const DEFAULT_RANKING_LIMIT = 10;
