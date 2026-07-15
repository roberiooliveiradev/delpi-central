export const DEFAULT_RANKING_LIMIT = 10;

export type FilterFormState = {
  dataInicio: string;
  dataFim: string;
  mp: string;
  pa: string;
  op: string;
  motivo: string;
  centroTrabalho: string;
};

export type ScrapQueryFilters = {
  filial: string;
  dataInicio: string;
  dataFim: string;
  mp?: string;
  pa?: string;
  op?: string;
  motivo?: string;
  centroTrabalho?: string;
};

export type ScrapPeriodo = {
  dataInicio: string;
  dataFim: string;
  filial: string;
};

export type ScrapResumo = {
  periodo: ScrapPeriodo;
  totalValor: number;
  totalQuantidade: number;
  ocorrencias: number;
  registrosSemCusto: number;
  valorDia: number;
  valorMes: number;
};

export type ScrapRankingDimension =
  | "motivo"
  | "materia_prima"
  | "produto_acabado"
  | "centro_trabalho"
  | "colaborador";

export type ScrapRankingItem = {
  code: string;
  label: string;
  quantity: number;
  value: number;
  sharePct: number;
  occurrenceCount: number;
};

export type ScrapRankingsData = {
  periodo: ScrapPeriodo;
  dimension: ScrapRankingDimension;
  items: ScrapRankingItem[];
};

export type ScrapSeriePoint = {
  date: string;
  label: string;
  value: number;
  quantity: number;
  occurrenceCount: number;
};

export type ScrapSerieData = {
  periodo: ScrapPeriodo;
  granularity: "day" | "month";
  points: ScrapSeriePoint[];
};

export type ScrapRegistroItem = {
  filial: string;
  dataPerda: string;
  op: string;
  pa: string;
  mp: string;
  descricao: string;
  um: string;
  motivoCodigo: string;
  motivo: string;
  quantidade: number;
  valor: number;
  centroTrabalho: string;
  codigoOperador: string;
  nomeOperador: string;
};

export type ScrapRegistrosData = {
  periodo: ScrapPeriodo;
  items: ScrapRegistroItem[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};

export type ScrapFiltroOption = {
  codigo: string;
  descricao?: string;
};

export type ScrapFiltrosData = {
  materiasPrimas: ScrapFiltroOption[];
  produtosAcabados: ScrapFiltroOption[];
  ordensProducao: ScrapFiltroOption[];
  motivos: ScrapFiltroOption[];
};
