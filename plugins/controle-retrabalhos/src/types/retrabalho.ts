export type RetrabalhoPeriodo = {
  start_date: string;
  end_date: string;
  branch: string;
};

export type RetrabalhoQueryFilters = {
  branch: string;
  start_date: string;
  end_date: string;
};

export type FilterFormState = {
  start_date: string;
  end_date: string;
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
  branch: string;
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
  /** Descrição canônica do motivo TOTVS (`DESCRICAO_MOTIVO`), ex.: RETRABALHO. */
  motivoDescricao?: string | null;
  stop_reason_description?: string | null;
  observacao: string;
  recno: number;
};

export type RetrabalhoDetalhesPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  is_complete?: boolean;
};

export type RetrabalhoDetalhesData = {
  periodo: RetrabalhoPeriodo;
  items: RetrabalhoDetalheItem[];
  page: number;
  pageSize: number;
  page_size?: number;
  total: number;
  totalPages: number;
  total_pages?: number;
  pagination?: RetrabalhoDetalhesPagination;
};

export const DEFAULT_PAGE_SIZE = 50;
export const DEFAULT_RANKING_LIMIT = 10;
