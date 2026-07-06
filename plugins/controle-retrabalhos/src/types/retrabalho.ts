export type RetrabalhoPeriodo = {
  dataInicio: string;
  dataFim: string;
  filial: string;
};

export type RetrabalhoQueryFilters = {
  filial: string;
  dataInicio: string;
  dataFim: string;
};

export type FilterFormState = {
  dataInicio: string;
  dataFim: string;
};

export type RetrabalhoResumo = {
  periodo: RetrabalhoPeriodo;
  totalApontamentos: number;
  totalHoras: number;
  totalCusto: number;
  custoMedioHora: number;
  registrosSemCusto: number;
  horasSemCusto: number;
  percentualHorasSemCusto: number;
  principalRecursoPorHoras: { recurso: string; totalHoras: number } | null;
  principalColaboradorPorHoras: {
    codigoOperador: string;
    nomeOperador: string;
    totalHoras: number;
  } | null;
};

export type RetrabalhoMensalItem = {
  anoMes: string;
  ano: number;
  mesNumero: number;
  mesNome: string;
  totalApontamentos: number;
  totalHoras: number;
  totalCusto: number;
  horasSemCusto: number;
};

export type RetrabalhoMensalData = {
  periodo: RetrabalhoPeriodo;
  items: RetrabalhoMensalItem[];
};

export type RetrabalhoRecursoItem = {
  recurso: string;
  centroCusto: string;
  totalApontamentos: number;
  totalHoras: number;
  totalCusto: number;
  horasSemCusto: number;
};

export type RetrabalhoColaboradorItem = {
  codigoOperador: string;
  nomeOperador: string;
  totalApontamentos: number;
  totalHoras: number;
  totalCusto: number;
  horasSemCusto: number;
};

export type RetrabalhoDetalheItem = {
  dataReferencia: string;
  filial: string;
  op: string;
  produto: string;
  operacao: string;
  recurso: string;
  centroCusto: string;
  codigoOperador: string;
  nomeOperador: string;
  tempoHoras: number;
  valorParada: number;
  fonteCusto: string;
  motivo: string;
  observacao: string;
  recno: number;
};

export type RetrabalhoDetalhesData = {
  periodo: RetrabalhoPeriodo;
  items: RetrabalhoDetalheItem[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};

export const DEFAULT_PAGE_SIZE = 50;
export const DEFAULT_RANKING_LIMIT = 10;
