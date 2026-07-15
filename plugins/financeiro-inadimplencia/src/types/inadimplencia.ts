export type SortDirection = "asc" | "desc";

export type PeriodPreset =
  | "last_6_months"
  | "last_12_months"
  | "current_year"
  | "previous_year"
  | "custom";

export type TituloStatus = "all" | "on_time" | "late";

export type ClientesSortBy =
  | "late_amount"
  | "late_titles"
  | "total_amount"
  | "on_time_by_quantity_percent"
  | "on_time_by_amount_percent"
  | "customer_name";

export type TitulosSortBy =
  | "amount"
  | "days_late"
  | "payment_date"
  | "issue_date"
  | "customer_name"
  | "number";

export type DelayRangeCode =
  | "EM_DIA"
  | "ATRASO_1_A_5_DIAS"
  | "ATRASO_6_A_15_DIAS"
  | "ATRASO_16_A_30_DIAS"
  | "ATRASO_ACIMA_30_DIAS";

export type InadimplenciaPeriodo = {
  data_inicio: string;
  data_fim_exclusiva: string;
  rotulo: string;
};

export type InadimplenciaTotais = {
  titulos: number;
  titulos_em_dia: number;
  titulos_atraso: number;
  valor_total: number;
  valor_atraso: number;
};

export type InadimplenciaIndicadores = {
  percentual_em_dia_qtd: number;
  percentual_inadimplencia_qtd: number;
  percentual_em_dia_valor: number;
  percentual_inadimplencia_valor: number;
};

export type InadimplenciaResumoData = {
  periodo: InadimplenciaPeriodo;
  totais: InadimplenciaTotais;
  indicadores: InadimplenciaIndicadores;
};

export type InadimplenciaMensalItem = {
  mes: string;
  ano_mes: string;
  total_titulos: number;
  titulos_em_dia: number;
  titulos_atraso: number;
  valor_total: number;
  valor_em_dia: number;
  valor_atraso: number;
  percentual_em_dia_qtd: number;
  percentual_em_dia_valor: number;
};

export type InadimplenciaMensalData = {
  periodo: InadimplenciaPeriodo;
  items: InadimplenciaMensalItem[];
};

export type InadimplenciaFaixaItem = {
  codigo: DelayRangeCode | string;
  rotulo: string;
  ordem: number;
  quantidade: number;
  valor: number;
  percentual_quantidade: number;
  percentual_valor: number;
};

export type InadimplenciaFaixasData = {
  periodo: InadimplenciaPeriodo;
  items: InadimplenciaFaixaItem[];
};

export type InadimplenciaPagination = {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export type InadimplenciaClienteItem = {
  cliente_codigo: string;
  loja: string;
  nome_cliente: string;
  nome_reduzido: string;
  total_titulos: number;
  titulos_em_dia: number;
  titulos_atraso: number;
  valor_total: number;
  valor_atraso: number;
  percentual_em_dia_qtd: number;
  percentual_em_dia_valor: number;
};

export type InadimplenciaClientesData = {
  periodo: InadimplenciaPeriodo;
  pagination: InadimplenciaPagination;
  sort: { sort_by: string; sort_dir: string };
  items: InadimplenciaClienteItem[];
};

export type InadimplenciaTituloItem = {
  filial: string;
  prefixo: string;
  numero: string;
  parcela: string;
  tipo: string;
  cliente_codigo: string;
  loja: string;
  nome_cliente: string;
  nome_reduzido: string;
  data_emissao: string;
  data_vencimento_real: string;
  data_baixa: string;
  valor_titulo: number;
  pago_em_dia: boolean;
  dias_atraso: number;
  faixa_atraso: {
    codigo: string;
    rotulo: string;
  };
};

export type InadimplenciaTitulosData = {
  periodo: InadimplenciaPeriodo;
  pagination: InadimplenciaPagination;
  sort: { sort_by: string; sort_dir: string };
  items: InadimplenciaTituloItem[];
};

export type PeriodFilter = {
  startDate?: string;
  endDate?: string;
};

export type MensalQueryParams = PeriodFilter & {
  customerCode?: string;
  storeCode?: string;
  /** Lista `CODIGO/LOJA` para filtro multiplo. */
  customers?: string[];
  /** Exclui WEG (000001) — somente Novos Negócios. */
  novosNegocios?: boolean;
};

export type ClientesQueryParams = PeriodFilter & {
  page?: number;
  pageSize?: number;
  sortBy?: ClientesSortBy;
  sortDir?: SortDirection;
  q?: string;
  onlyWithDelays?: boolean;
};

export type TitulosQueryParams = PeriodFilter & {
  customerCode?: string;
  storeCode?: string;
  status?: TituloStatus;
  delayRange?: DelayRangeCode | string;
  q?: string;
  page?: number;
  pageSize?: number;
  sortBy?: TitulosSortBy;
  sortDir?: SortDirection;
};

export type PeriodFormState = {
  preset: PeriodPreset;
  startDate: string;
  endDate: string;
};

export type SelectedCustomer = {
  cliente_codigo: string;
  loja: string;
  nome_cliente: string;
  nome_reduzido: string;
  titulos_atraso: number;
  valor_atraso: number;
};

export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PERIOD_MONTHS = 60;

export const CLIENTES_SORT_OPTIONS: Array<{ value: ClientesSortBy; label: string }> = [
  { value: "late_amount", label: "Valor atrasado" },
  { value: "late_titles", label: "Títulos atrasados" },
  { value: "total_amount", label: "Valor total" },
  { value: "on_time_by_quantity_percent", label: "Pontualidade (qtd)" },
  { value: "customer_name", label: "Cliente" },
];

export const DELAY_RANGE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "Todas as faixas" },
  { value: "EM_DIA", label: "Em dia" },
  { value: "ATRASO_1_A_5_DIAS", label: "1 a 5 dias" },
  { value: "ATRASO_6_A_15_DIAS", label: "6 a 15 dias" },
  { value: "ATRASO_16_A_30_DIAS", label: "16 a 30 dias" },
  { value: "ATRASO_ACIMA_30_DIAS", label: "Acima de 30 dias" },
];
